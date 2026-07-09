"""SAR - Motor de parseo y generación de reportes Excel."""
import io
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

TEMPLATE_PATH = Path(__file__).parent / "templates" / "machote.xlsx"

REQUIRED_SHEETS = ["Conc Dictamenes", "Exhibiciones"]

# Causas de negado en el orden de "Conc Dictamenes" (col 6..19) que mapean 1:1
# a los grupos de columnas del MACHOTE (col 8,12,16,...,60).
NEGADO_CAUSAS = [
    "Frenteos", "Revueltos", "Bodega Venta", "Bodega Tapanco", "Doble Ubicacion",
    "Excedente", "Origen", "Cambios / Probadores", "Negados sin Recuperar",
    "Exhibiciones", "Bodega Aclaracion", "Aduanas", "Golden o apartados",
    "Control de calidad",
]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

ROPA_CATALOGOS = {"ROPA DOBLADA", "ROPA COLGADA", "JEANS"}


def norm(s):
    if s is None:
        return ""
    s = str(s).strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.upper().strip()


def num(v):
    """Coerce a cell value to float; '-', None, text -> 0."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if s in ("", "-", "#VALUE!", "#DIV/0!"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def area_de_catalogo(catalogo):
    return "Ropa" if norm(catalogo) in ROPA_CATALOGOS else "Calzado"


def find_sheet(wb, target):
    tnorm = norm(target)
    for name in wb.sheetnames:
        if norm(name) == tnorm:
            return name
    return None


def es_archivo_valido(wb):
    return all(find_sheet(wb, s) is not None for s in REQUIRED_SHEETS)


def parse_semana(raw):
    m = re.search(r"(\d+)", str(raw or ""))
    return int(m.group(1)) if m else None


def parse_periodo(texto):
    """Extrae mes y año de textos como 'Del 29 al 03 de Julio del 2026'."""
    t = norm(texto)
    mes = None
    for i, nombre in enumerate(MESES, start=1):
        if norm(nombre) in t:
            mes = i
            break
    ym = re.search(r"(20\d{2})", str(texto or ""))
    anio = int(ym.group(1)) if ym else None
    return mes, anio


def parse_conc_dictamenes(wb):
    """Devuelve (meta, registros[]) desde la hoja Conc Dictamenes."""
    ws = wb[find_sheet(wb, "Conc Dictamenes")]

    def cell(r, c):
        return ws.cell(row=r, column=c).value

    tienda = cell(4, 3)
    semana = parse_semana(cell(4, 10))
    periodo = cell(4, 26)
    mes, anio = parse_periodo(periodo)

    # bloque de recuperadas: filas 29..44, catalogo en col 4, causas cols 6..19
    recuperadas = {}
    for r in range(29, 45):
        cat = cell(r, 4)
        if cat is None:
            continue
        recuperadas[norm(cat)] = {
            NEGADO_CAUSAS[i]: num(cell(r, 6 + i)) for i in range(14)
        }

    registros = []
    for r in range(8, 24):
        cat = cell(r, 1)
        if cat is None or norm(cat) in ("", "TOTAL"):
            continue
        catnorm = norm(cat)
        negado_detalle = {NEGADO_CAUSAS[i]: num(cell(r, 6 + i)) for i in range(14)}
        rec_detalle = recuperadas.get(catnorm, {c: 0.0 for c in NEGADO_CAUSAS})
        negado_total = sum(negado_detalle.values())
        recuperado_total = sum(rec_detalle.values())
        reg = {
            "catalogo": str(cat).strip(),
            "responsable": str(cell(r, 2)).strip() if cell(r, 2) else "",
            "area": area_de_catalogo(cat),
            "total_pasillo": num(cell(r, 3)),
            "auditados": num(cell(r, 4)),
            "pct_cobertura": num(cell(r, 5)),
            "frente": num(cell(r, 6)),
            "bodega": num(cell(r, 8)),
            "negado": negado_total,
            "recuperado": recuperado_total,
            "exhibicion": num(cell(r, 15)),
            "sin_exhibicion": num(cell(r, 21)),
            "costo": num(cell(r, 20)),
            "observaciones": "",
            "negado_detalle": negado_detalle,
            "recuperado_detalle": rec_detalle,
        }
        registros.append(reg)

    meta = {"tienda": str(tienda).strip() if tienda else "", "semana": semana,
            "mes": mes, "anio": anio, "periodo": str(periodo).strip() if periodo else ""}
    return meta, registros


def validar_exhibiciones(wb, registros):
    """Compara totales de Exhibiciones vs Conc Dictamenes. Devuelve dict."""
    ws = wb[find_sheet(wb, "Exhibiciones")]
    total_oportunidades = 0.0
    total_recuperadas = 0.0
    for r in range(1, ws.max_row + 1):
        c3 = ws.cell(row=r, column=3).value
        if c3 and norm(c3).startswith("TOTAL"):
            total_oportunidades += num(ws.cell(row=r, column=19).value)
            total_recuperadas += num(ws.cell(row=r, column=20).value)

    conc_incidencias = sum(
        reg["exhibicion"] + reg["sin_exhibicion"] for reg in registros
    )
    diferencia = round(total_oportunidades - conc_incidencias, 2)
    return {
        "exhibiciones_oportunidades": total_oportunidades,
        "exhibiciones_recuperadas": total_recuperadas,
        "conc_incidencias_exhibicion": conc_incidencias,
        "diferencia": diferencia,
        "coincide": abs(diferencia) < 0.001,
    }


# ---------------- Generación de reportes ----------------

def _store_row_map(ws, r_ini, r_fin):
    """Mapea nombre normalizado de tienda -> fila, en un rango de la plantilla."""
    m = {}
    for r in range(r_ini, r_fin + 1):
        v = ws.cell(row=r, column=2).value
        if v and isinstance(v, str) and v.strip():
            m[norm(v)] = r
    return m


def _fill_section(ws, r_ini, r_fin, por_tienda):
    """Rellena una sección (Calzado/Ropa) del MACHOTE con datos agregados por tienda."""
    row_map = _store_row_map(ws, r_ini, r_fin)
    for tienda_norm, agg in por_tienda.items():
        row = row_map.get(tienda_norm)
        if not row:
            continue
        ws.cell(row=row, column=5, value=round(agg["total_pasillo"]))
        ws.cell(row=row, column=6, value=round(agg["auditados"]))
        for i, causa in enumerate(NEGADO_CAUSAS):
            ws.cell(row=row, column=8 + 4 * i, value=round(agg["negado_detalle"].get(causa, 0)))
            ws.cell(row=row, column=10 + 4 * i, value=round(agg["recuperado_detalle"].get(causa, 0)))
        ws.cell(row=row, column=64, value=round(agg["negado"]))
        ws.cell(row=row, column=66, value=round(agg["recuperado"]))
        ws.cell(row=row, column=68, value=round(agg["costo"]))


def _aggregate(registros):
    """Agrupa registros por (area, tienda)."""
    out = {"Calzado": {}, "Ropa": {}}
    for reg in registros:
        area = reg.get("area", "Calzado")
        area = area if area in out else "Calzado"
        t = norm(reg["tienda"])
        d = out[area].setdefault(t, {
            "total_pasillo": 0.0, "auditados": 0.0, "negado": 0.0,
            "recuperado": 0.0, "costo": 0.0,
            "negado_detalle": {c: 0.0 for c in NEGADO_CAUSAS},
            "recuperado_detalle": {c: 0.0 for c in NEGADO_CAUSAS},
        })
        d["total_pasillo"] += reg["total_pasillo"]
        d["auditados"] += reg["auditados"]
        d["negado"] += reg["negado"]
        d["recuperado"] += reg["recuperado"]
        d["costo"] += reg["costo"]
        for c in NEGADO_CAUSAS:
            d["negado_detalle"][c] += reg.get("negado_detalle", {}).get(c, 0)
            d["recuperado_detalle"][c] += reg.get("recuperado_detalle", {}).get(c, 0)
    return out


def generar_concentrado(registros, etiqueta):
    """Genera un xlsx con formato MACHOTE. Devuelve bytes."""
    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    ws = wb["Concentrado "]
    agg = _aggregate(registros)
    _fill_section(ws, 8, 24, agg["Calzado"])
    _fill_section(ws, 39, 55, agg["Ropa"])
    # etiquetas de periodo
    for (r, c) in [(3, 24), (3, 88), (3, 117), (34, 24), (34, 117)]:
        try:
            ws.cell(row=r, column=c, value=etiqueta)
        except Exception:
            pass
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
