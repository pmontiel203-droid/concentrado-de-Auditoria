from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import io
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import uuid

import openpyxl

import sar_excel as sx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MESES_NOMBRE = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------- Importación ----------------
@api_router.post("/import")
async def importar_archivos(
    files: list[UploadFile] = File(...),
    forzar: bool = Form(False),
    usuario: str = Form("Gerencia de Mejoras"),
):
    resultados = []
    for f in files:
        entry = {"archivo": f.filename, "resultado": "", "observaciones": "",
                 "tienda": "", "semana": None, "registros": 0}
        try:
            content = await f.read()
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        except Exception as e:
            entry["resultado"] = "ERROR"
            entry["observaciones"] = f"No se pudo abrir el archivo: {e}"
            resultados.append(entry)
            continue

        if not sx.es_archivo_valido(wb):
            if sx.es_concentrado_armado(wb):
                await _importar_concentrado_armado(wb, f.filename, usuario, entry)
                resultados.append(entry)
                wb.close()
                continue
            entry["resultado"] = "OMITIDO"
            entry["observaciones"] = ("No contiene las hojas 'Conc Dictamenes' y "
                                      "'Exhibiciones' ni hojas 'SEMANA' con detalle por catálogo")
            resultados.append(entry)
            wb.close()
            continue

        meta, registros = sx.parse_conc_dictamenes(wb)
        validacion = sx.validar_exhibiciones(wb, registros)
        wb.close()

        entry["tienda"] = meta["tienda"]
        entry["semana"] = meta["semana"]
        entry["registros"] = len(registros)
        entry["validacion"] = validacion

        if not validacion["coincide"] and not forzar:
            entry["resultado"] = "CON DIFERENCIAS"
            entry["observaciones"] = (
                f"Exhibiciones ({validacion['exhibiciones_oportunidades']:.0f}) "
                f"no coincide con Conc Dictamenes ({validacion['conc_incidencias_exhibicion']:.0f}). "
                f"Diferencia: {validacion['diferencia']:.0f}. No importado."
            )
            resultados.append(entry)
            await _log_import(entry, meta, usuario)
            continue

        # eliminar registros previos de la misma tienda/semana/año (idempotente)
        await db.registros.delete_many({
            "tienda_norm": sx.norm(meta["tienda"]),
            "semana": meta["semana"],
            "anio": meta["anio"],
        })

        fecha_imp = now_iso()
        docs = []
        for reg in registros:
            doc = {
                "id": str(uuid.uuid4()),
                "semana": meta["semana"], "mes": meta["mes"], "anio": meta["anio"],
                "periodo": meta["periodo"],
                "fecha_importacion": fecha_imp,
                "nombre_archivo": f.filename,
                "tienda": meta["tienda"], "tienda_norm": sx.norm(meta["tienda"]),
                **reg,
            }
            docs.append(doc)
        if docs:
            await db.registros.insert_many(docs)

        entry["resultado"] = "IMPORTADO" + (" (FORZADO)" if not validacion["coincide"] else "")
        entry["observaciones"] = f"{len(registros)} catálogos importados."
        resultados.append(entry)
        await _log_import(entry, meta, usuario)

    return {"resultados": resultados}


async def _importar_concentrado_armado(wb, filename, usuario, entry):
    """Importa un Concentrado ya armado (hojas SEMANA) directo al histórico, sin validar."""
    registros = sx.parse_concentrado_armado(wb)
    if not registros:
        entry["resultado"] = "OMITIDO"
        entry["observaciones"] = "Archivo de concentrado sin datos por catálogo."
        return

    # sobrescribir por (tienda, semana, año)
    claves = {(sx.norm(r["tienda"]), r["semana"], r["anio"]) for r in registros}
    for tnorm, semana, anio in claves:
        await db.registros.delete_many({"tienda_norm": tnorm, "semana": semana, "anio": anio})

    fecha_imp = now_iso()
    docs = []
    for reg in registros:
        docs.append({
            "id": str(uuid.uuid4()),
            "fecha_importacion": fecha_imp,
            "nombre_archivo": filename,
            "tienda_norm": sx.norm(reg["tienda"]),
            **reg,
        })
    if docs:
        await db.registros.insert_many(docs)

    semanas = sorted({r["semana"] for r in registros if r["semana"]})
    tiendas = sorted({r["tienda"] for r in registros if r["tienda"]})
    entry["resultado"] = "IMPORTADO"
    entry["tienda"] = f"{len(tiendas)} tiendas"
    entry["semana"] = ", ".join(str(s) for s in semanas) if semanas else None
    entry["registros"] = len(registros)
    entry["observaciones"] = (
        f"Concentrado armado: {len(registros)} registros, "
        f"semanas [{', '.join(str(s) for s in semanas)}], {len(tiendas)} tiendas."
    )
    ahora = datetime.now(timezone.utc)
    await db.import_logs.insert_one({
        "id": str(uuid.uuid4()),
        "fecha": ahora.strftime("%Y-%m-%d"), "hora": ahora.strftime("%H:%M:%S"),
        "timestamp": ahora.isoformat(),
        "semana": entry["semana"], "anio": registros[0].get("anio"),
        "tienda": entry["tienda"], "archivo": filename,
        "resultado": entry["resultado"], "observaciones": entry["observaciones"],
        "usuario": usuario,
    })


async def _log_import(entry, meta, usuario):
    ahora = datetime.now(timezone.utc)
    await db.import_logs.insert_one({
        "id": str(uuid.uuid4()),
        "fecha": ahora.strftime("%Y-%m-%d"),
        "hora": ahora.strftime("%H:%M:%S"),
        "timestamp": ahora.isoformat(),
        "semana": meta.get("semana"),
        "anio": meta.get("anio"),
        "tienda": entry.get("tienda"),
        "archivo": entry.get("archivo"),
        "resultado": entry.get("resultado"),
        "observaciones": entry.get("observaciones"),
        "usuario": usuario,
    })


# ---------------- Consultas ----------------
@api_router.get("/registros")
async def get_registros(semana: Optional[int] = None, mes: Optional[int] = None,
                        anio: Optional[int] = None, tienda: Optional[str] = None):
    q = {}
    if semana is not None:
        q["semana"] = semana
    if mes is not None:
        q["mes"] = mes
    if anio is not None:
        q["anio"] = anio
    if tienda:
        q["tienda_norm"] = sx.norm(tienda)
    regs = await db.registros.find(q, {"_id": 0}).to_list(20000)
    return regs


@api_router.get("/imports")
async def get_imports():
    logs = await db.import_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    return logs


@api_router.get("/semanas")
async def get_semanas():
    pipeline = [
        {"$group": {"_id": {"semana": "$semana", "anio": "$anio", "mes": "$mes"},
                    "tiendas": {"$addToSet": "$tienda"}}},
        {"$sort": {"_id.anio": -1, "_id.semana": -1}},
    ]
    out = []
    async for row in db.registros.aggregate(pipeline):
        out.append({
            "semana": row["_id"]["semana"], "anio": row["_id"]["anio"],
            "mes": row["_id"]["mes"], "num_tiendas": len(row["tiendas"]),
            "tiendas": sorted([t for t in row["tiendas"] if t]),
        })
    return out


# ---------------- Dashboard ----------------
TOTAL_TIENDAS = 17


@api_router.get("/dashboard")
async def dashboard(semana: Optional[int] = None, anio: Optional[int] = None,
                    mes: Optional[int] = None):
    q = {}
    if semana is not None:
        q["semana"] = semana
    if mes is not None:
        q["mes"] = mes
    if anio is not None:
        q["anio"] = anio
    regs = await db.registros.find(q, {"_id": 0}).to_list(50000)

    tiendas = {}
    catalogos = {}
    responsables = {}
    tot_aud = tot_neg = tot_rec = tot_costo = 0.0
    for r in regs:
        t = r.get("tienda") or "?"
        td = tiendas.setdefault(t, {"auditados": 0.0, "negado": 0.0, "recuperado": 0.0, "costo": 0.0})
        td["auditados"] += r["auditados"]; td["negado"] += r["negado"]
        td["recuperado"] += r["recuperado"]; td["costo"] += r["costo"]
        c = r.get("catalogo") or "?"
        cd = catalogos.setdefault(c, {"auditados": 0.0, "negado": 0.0, "recuperado": 0.0})
        cd["auditados"] += r["auditados"]; cd["negado"] += r["negado"]; cd["recuperado"] += r["recuperado"]
        resp = r.get("responsable") or "Sin responsable"
        rd = responsables.setdefault(resp, {"negado": 0.0, "recuperado": 0.0})
        rd["negado"] += r["negado"]; rd["recuperado"] += r["recuperado"]
        tot_aud += r["auditados"]; tot_neg += r["negado"]
        tot_rec += r["recuperado"]; tot_costo += r["costo"]

    def pct(a, b):
        return round(100.0 * a / b, 2) if b else 0.0

    # tiendas con errores/diferencias en logs
    log_q = {}
    if semana is not None:
        log_q["semana"] = semana
    if anio is not None:
        log_q["anio"] = anio
    logs = await db.import_logs.find(log_q, {"_id": 0}).to_list(2000)
    con_error = sorted({l["tienda"] for l in logs
                        if l.get("resultado") in ("ERROR", "CON DIFERENCIAS") and l.get("tienda")})

    recibidas = len(tiendas)
    ranking_tiendas = sorted(
        [{"tienda": k, **v, "pct_negado": pct(v["negado"], v["auditados"]),
          "pct_recuperado": pct(v["recuperado"], v["negado"])}
         for k, v in tiendas.items()],
        key=lambda x: x["pct_recuperado"], reverse=True)
    ranking_resp = sorted(
        [{"responsable": k, **v, "pct_recuperado": pct(v["recuperado"], v["negado"])}
         for k, v in responsables.items()],
        key=lambda x: x["pct_recuperado"], reverse=True)
    por_catalogo = sorted(
        [{"catalogo": k, **v, "pct_negado": pct(v["negado"], v["auditados"])}
         for k, v in catalogos.items()],
        key=lambda x: x["negado"], reverse=True)

    return {
        "tiendas_recibidas": recibidas,
        "tiendas_pendientes": max(0, TOTAL_TIENDAS - recibidas),
        "tiendas_con_errores": len(con_error),
        "lista_con_errores": con_error,
        "total_auditados": tot_aud,
        "total_negado": tot_neg,
        "total_recuperado": tot_rec,
        "total_costo": tot_costo,
        "pct_negado": pct(tot_neg, tot_aud),
        "pct_recuperado": pct(tot_rec, tot_neg),
        "ranking_tiendas": ranking_tiendas,
        "ranking_responsables": ranking_resp,
        "por_catalogo": por_catalogo,
    }


@api_router.get("/comparativo")
async def comparativo(anio: Optional[int] = None, tipo: str = "semana"):
    """tipo: 'semana' | 'mes' -> series agregadas para comparativos."""
    match = {}
    if anio is not None:
        match["anio"] = anio
    key = "$semana" if tipo == "semana" else "$mes"
    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {"$group": {"_id": key, "auditados": {"$sum": "$auditados"},
                    "negado": {"$sum": "$negado"}, "recuperado": {"$sum": "$recuperado"},
                    "costo": {"$sum": "$costo"}}},
        {"$sort": {"_id": 1}},
    ]
    out = []
    async for row in db.registros.aggregate(pipeline):
        if row["_id"] is None:
            continue
        aud = row["auditados"]; neg = row["negado"]
        etiqueta = (f"Sem {int(row['_id'])}" if tipo == "semana"
                    else MESES_NOMBRE[int(row["_id"])] if 1 <= int(row["_id"]) <= 12 else str(row["_id"]))
        out.append({
            "periodo": etiqueta, "clave": row["_id"],
            "auditados": aud, "negado": neg, "recuperado": row["recuperado"], "costo": row["costo"],
            "pct_negado": round(100.0 * neg / aud, 2) if aud else 0.0,
            "pct_recuperado": round(100.0 * row["recuperado"] / neg, 2) if neg else 0.0,
        })
    return out


# ---------------- Reportes descargables ----------------
def _stream(data: bytes, filename: str):
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@api_router.get("/reporte/semanal")
async def reporte_semanal(semana: int, anio: Optional[int] = None):
    q = {"semana": semana}
    if anio is not None:
        q["anio"] = anio
    regs = await db.registros.find(q, {"_id": 0}).to_list(50000)
    if not regs:
        raise HTTPException(404, "No hay datos para esa semana")
    data = sx.generar_concentrado(regs, f"Semana {semana}")
    return _stream(data, f"Concentrado_Semanal_{semana}.xlsx")


@api_router.get("/reporte/mensual")
async def reporte_mensual(mes: int, anio: Optional[int] = None):
    q = {"mes": mes}
    if anio is not None:
        q["anio"] = anio
    regs = await db.registros.find(q, {"_id": 0}).to_list(80000)
    if not regs:
        raise HTTPException(404, "No hay datos para ese mes")
    data = sx.generar_concentrado(regs, MESES_NOMBRE[mes] if 1 <= mes <= 12 else str(mes))
    return _stream(data, f"Concentrado_Mensual_{MESES_NOMBRE[mes]}.xlsx")


@api_router.get("/reporte/anual")
async def reporte_anual(anio: int):
    regs = await db.registros.find({"anio": anio}, {"_id": 0}).to_list(200000)
    if not regs:
        raise HTTPException(404, "No hay datos para ese año")
    data = sx.generar_concentrado(regs, f"Anual {anio}")
    return _stream(data, f"Concentrado_Anual_{anio}.xlsx")


@api_router.delete("/registros")
async def borrar_registros(semana: Optional[int] = None, anio: Optional[int] = None):
    q = {}
    if semana is not None:
        q["semana"] = semana
    if anio is not None:
        q["anio"] = anio
    if not q:
        raise HTTPException(400, "Debe indicar semana y/o año")
    res = await db.registros.delete_many(q)
    return {"eliminados": res.deleted_count}


@api_router.get("/")
async def root():
    return {"message": "SAR API"}


app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def crear_indices():
    await db.registros.create_index([("semana", 1), ("anio", 1)])
    await db.registros.create_index([("mes", 1), ("anio", 1)])
    await db.registros.create_index([("anio", 1)])
    await db.registros.create_index([("tienda_norm", 1), ("semana", 1), ("anio", 1)])
    await db.import_logs.create_index([("timestamp", -1)])


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
