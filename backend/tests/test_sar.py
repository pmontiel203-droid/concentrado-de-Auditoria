"""SAR backend integration tests."""
import io
import os
import pytest
import requests
import openpyxl

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://audit-recovery.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
SAMPLE = "/app/tests/samples/checklist_sem26.xlsx"

SEMANA = 26
ANIO = 2026


@pytest.fixture(scope="module")
def sample_bytes():
    with open(SAMPLE, "rb") as f:
        return f.read()


@pytest.fixture(scope="module", autouse=True)
def clean_state():
    # Ensure clean DB for semana 26 before test run
    requests.delete(f"{API}/registros", params={"semana": SEMANA, "anio": ANIO}, timeout=30)
    yield
    # optional cleanup after
    requests.delete(f"{API}/registros", params={"semana": SEMANA, "anio": ANIO}, timeout=30)


def _post_import(sample_bytes, forzar=None, filename="checklist_sem26.xlsx"):
    files = {"files": (filename, sample_bytes,
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    data = {}
    if forzar is not None:
        data["forzar"] = str(forzar).lower()
    return requests.post(f"{API}/import", files=files, data=data, timeout=60)


# ---------- 1. No-forzar => CON DIFERENCIAS, no records ----------
def test_import_sin_forzar_con_diferencias(sample_bytes):
    r = _post_import(sample_bytes, forzar=None)
    assert r.status_code == 200, r.text
    resultados = r.json()["resultados"]
    assert len(resultados) == 1
    entry = resultados[0]
    assert entry["resultado"] == "CON DIFERENCIAS", entry
    assert entry["tienda"], "should have tienda parsed"
    assert entry["semana"] == SEMANA
    v = entry.get("validacion", {})
    assert v.get("coincide") is False
    assert v.get("diferencia", 0) != 0

    # Verify no records were stored
    regs = requests.get(f"{API}/registros", params={"semana": SEMANA, "anio": ANIO}, timeout=30).json()
    assert regs == [], f"Expected no records but got {len(regs)}"


# ---------- 2. Forzar => IMPORTADO (FORZADO), 16 records ----------
def test_import_forzar_true(sample_bytes):
    r = _post_import(sample_bytes, forzar=True)
    assert r.status_code == 200, r.text
    entry = r.json()["resultados"][0]
    assert entry["resultado"] == "IMPORTADO (FORZADO)", entry
    assert entry["registros"] == 16
    assert "ECATEPEC" in entry["tienda"].upper()
    assert entry["semana"] == SEMANA


# ---------- 3. Idempotency ----------
def test_import_idempotent(sample_bytes):
    _post_import(sample_bytes, forzar=True)
    _post_import(sample_bytes, forzar=True)
    regs = requests.get(f"{API}/registros", params={"semana": SEMANA, "anio": ANIO}, timeout=30).json()
    # Only Ecatepec has 16 records
    ecatepec = [r for r in regs if "ECATEPEC" in (r.get("tienda") or "").upper()]
    assert len(ecatepec) == 16, f"Idempotency failed: got {len(ecatepec)} records"


# ---------- 4. Non-audit file => OMITIDO ----------
def test_import_omitido_no_sheets():
    wb = openpyxl.Workbook()
    wb.active.title = "Random"
    wb.active["A1"] = "hola"
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    files = {"files": ("bad.xlsx", buf.read(),
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = requests.post(f"{API}/import", files=files, timeout=30)
    assert r.status_code == 200
    entry = r.json()["resultados"][0]
    assert entry["resultado"] == "OMITIDO", entry


# ---------- 5. Semanas ----------
def test_get_semanas():
    r = requests.get(f"{API}/semanas", timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert any(s["semana"] == SEMANA and s["anio"] == ANIO for s in data), data


# ---------- 6. Registros field structure ----------
def test_registros_fields():
    regs = requests.get(f"{API}/registros", params={"semana": SEMANA, "anio": ANIO}, timeout=30).json()
    ecatepec = [r for r in regs if "ECATEPEC" in (r.get("tienda") or "").upper()]
    assert len(ecatepec) == 16
    required = ["semana", "mes", "anio", "fecha_importacion", "nombre_archivo",
                "tienda", "responsable", "area", "catalogo", "auditados", "negado",
                "recuperado", "sin_exhibicion", "exhibicion", "frente", "bodega",
                "costo", "observaciones"]
    for field in required:
        assert field in ecatepec[0], f"missing field {field}"


# ---------- 7. Dashboard ----------
def test_dashboard():
    r = requests.get(f"{API}/dashboard", params={"semana": SEMANA, "anio": ANIO}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    for key in ["tiendas_recibidas", "tiendas_pendientes", "pct_negado",
                "pct_recuperado", "ranking_tiendas", "ranking_responsables",
                "por_catalogo", "total_costo"]:
        assert key in d, f"missing {key}"
    assert d["tiendas_pendientes"] == 17 - d["tiendas_recibidas"]
    assert d["tiendas_recibidas"] >= 1


# ---------- 8. Comparativo ----------
def test_comparativo():
    r = requests.get(f"{API}/comparativo", params={"anio": ANIO, "tipo": "semana"}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    row = data[0]
    for k in ["periodo", "pct_negado", "pct_recuperado"]:
        assert k in row


# ---------- 9. Imports log ----------
def test_imports_log():
    r = requests.get(f"{API}/imports", timeout=30)
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) > 0
    entry = logs[0]
    for k in ["fecha", "hora", "semana", "tienda", "archivo", "resultado",
              "observaciones", "usuario"]:
        assert k in entry, f"missing {k}"


# ---------- 10. Reporte semanal excel ----------
def test_reporte_semanal_excel():
    r = requests.get(f"{API}/reporte/semanal", params={"semana": SEMANA, "anio": ANIO}, timeout=60)
    assert r.status_code == 200
    assert "spreadsheet" in r.headers.get("Content-Type", "")
    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    assert "Concentrado " in wb.sheetnames
    ws = wb["Concentrado "]
    # find Ecatepec row in column 2
    found_row = None
    for row in range(1, ws.max_row + 1):
        v = ws.cell(row=row, column=2).value
        if v and "ecatepec" in str(v).lower():
            found_row = row
            break
    assert found_row, "Ecatepec row not found"
    col6 = ws.cell(row=found_row, column=6).value
    col64 = ws.cell(row=found_row, column=64).value
    assert col6 and float(col6) > 0, f"col 6 (auditados) empty at row {found_row}: {col6}"
    assert col64 is not None, f"col 64 empty at row {found_row}"


# ---------- 10b. detalle_full present in registros ----------
def test_registros_detalle_full():
    # ensure data
    with open(SAMPLE, "rb") as f:
        _post_import(f.read(), forzar=True)
    regs = requests.get(f"{API}/registros", params={"semana": SEMANA, "anio": ANIO}, timeout=30).json()
    ecatepec = [r for r in regs if "ECATEPEC" in (r.get("tienda") or "").upper()]
    assert len(ecatepec) == 16
    for r in ecatepec:
        assert "detalle_full" in r, "missing detalle_full key"
        df = r["detalle_full"]
        assert isinstance(df, dict)
        # keys '3'..'37' expected
        for c in range(3, 38):
            assert str(c) in df, f"detalle_full missing col {c}"


# ---------- 10c. SEMANA sheet filled ----------
def test_reporte_semanal_semana_sheet():
    r = requests.get(f"{API}/reporte/semanal", params={"semana": SEMANA, "anio": ANIO}, timeout=60)
    assert r.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    assert "SEMANA" in wb.sheetnames, f"SEMANA sheet missing. Sheets: {wb.sheetnames}"
    ws = wb["SEMANA"]

    # (a) Calzado per-store row for Ecatepec in rows 7..23
    ec_row = None
    for row in range(7, 24):
        v = ws.cell(row=row, column=1).value
        if v and "ecatepec" in str(v).lower():
            ec_row = row
            break
    assert ec_row, "Ecatepec Calzado row not found in 7..23"
    col3 = ws.cell(row=ec_row, column=3).value
    col4 = ws.cell(row=ec_row, column=4).value
    assert col3 is not None and float(col3) > 0, f"col3 not populated: {col3}"
    assert col4 is not None and float(col4) > 0, f"col4 not populated: {col4}"

    # (b) per-catalog detail block: find row where col1 contains Ecatepec and col2=='Responsable De Catalogo'
    block_row = None
    for row in range(1, ws.max_row + 1):
        c1 = ws.cell(row=row, column=1).value
        c2 = ws.cell(row=row, column=2).value
        if c1 and "ecatepec" in str(c1).lower() and c2 and "responsable" in str(c2).lower():
            block_row = row
            break
    assert block_row, "Ecatepec per-catalog header row not found"

    # next 16 rows should have catalog labels in col1
    labels = []
    for i in range(1, 17):
        v = ws.cell(row=block_row + i, column=1).value
        labels.append(str(v).upper() if v else "")
    joined = " ".join(labels)
    assert "BOTAS" in joined, f"BOTAS missing in catalog block: {labels}"
    assert "URBANO" in joined, f"URBANO missing in catalog block: {labels}"

    # at least one row has a responsable in col2 and numeric col4>0
    found_numeric = False
    for i in range(1, 17):
        r_ = block_row + i
        c2 = ws.cell(row=r_, column=2).value
        c4 = ws.cell(row=r_, column=4).value
        if c2 and isinstance(c4, (int, float)) and float(c4) > 0:
            found_numeric = True
            break
    assert found_numeric, "No catalog detail row with responsable and numeric col4>0"

    # (c) Concentrado Ecatepec row col6 populated
    ws2 = wb["Concentrado "]
    for row in range(1, ws2.max_row + 1):
        v = ws2.cell(row=row, column=2).value
        if v and "ecatepec" in str(v).lower():
            c6 = ws2.cell(row=row, column=6).value
            assert c6 and float(c6) > 0, f"Concentrado Ecatepec col6 empty: {c6}"
            break


# ---------- 11. Reporte mensual ----------
def test_reporte_mensual():
    r = requests.get(f"{API}/reporte/mensual", params={"mes": 7, "anio": ANIO}, timeout=60)
    assert r.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    assert "Concentrado " in wb.sheetnames


# ---------- 12. Reporte anual ----------
def test_reporte_anual():
    r = requests.get(f"{API}/reporte/anual", params={"anio": ANIO}, timeout=60)
    assert r.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    assert "Concentrado " in wb.sheetnames


# ---------- 13. Reporte semanal 404 ----------
def test_reporte_semanal_404():
    r = requests.get(f"{API}/reporte/semanal", params={"semana": 999}, timeout=30)
    assert r.status_code == 404


# ---------- 14. Delete registros ----------
def test_delete_registros():
    # ensure data exists
    with open(SAMPLE, "rb") as f:
        _post_import(f.read(), forzar=True)
    r = requests.delete(f"{API}/registros", params={"semana": SEMANA, "anio": ANIO}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "eliminados" in body
    assert body["eliminados"] >= 16
    # verify gone
    regs = requests.get(f"{API}/registros", params={"semana": SEMANA, "anio": ANIO}, timeout=30).json()
    assert regs == []
