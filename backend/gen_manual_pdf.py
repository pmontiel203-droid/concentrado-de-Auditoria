# -*- coding: utf-8 -*-
"""Genera el Manual de Uso de SAR en PDF."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, ListFlowable, ListItem)

NAVY = colors.HexColor("#0b1220")
AMBER = colors.HexColor("#f5a524")
SLATE = colors.HexColor("#334155")
GRAY = colors.HexColor("#64748b")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=NAVY, fontSize=20, spaceAfter=6, spaceBefore=14)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=NAVY, fontSize=14, spaceAfter=4, spaceBefore=12)
BODY = ParagraphStyle("BODY", parent=styles["BodyText"], textColor=SLATE, fontSize=10.5, leading=15, spaceAfter=4)
SMALL = ParagraphStyle("SMALL", parent=styles["BodyText"], textColor=GRAY, fontSize=9, leading=12)
STEP = ParagraphStyle("STEP", parent=BODY, leftIndent=6)

story = []

# Portada / encabezado
story.append(Paragraph("Sistema de Auditoría y Recuperación (SAR)", H1))
story.append(Paragraph("Manual de uso — Paso a paso", ParagraphStyle("sub", parent=BODY, textColor=AMBER, fontSize=12)))
story.append(HRFlowable(width="100%", thickness=2, color=AMBER, spaceBefore=6, spaceAfter=10))
story.append(Paragraph("Gerencia de Mejoras · Consolidación automática de auditorías de las 17 tiendas.", SMALL))
story.append(Spacer(1, 8))

story.append(Paragraph("Acceso a la aplicación", H2))
story.append(Paragraph('Abre en tu navegador: <b><font color="#0b57d0">https://audit-recovery.preview.emergentagent.com</font></b>', BODY))
story.append(Paragraph("No requiere usuario ni contraseña. En el menú lateral encontrarás 4 secciones: <b>Dashboard</b>, <b>Importar</b>, <b>Concentrados</b> y <b>Base Histórica</b>.", BODY))


def numbered(items):
    return ListFlowable(
        [ListItem(Paragraph(t, STEP), value=i + 1) for i, t in enumerate(items)],
        bulletType="1", leftIndent=16, bulletColor=AMBER, bulletFontSize=10,
    )


story.append(Paragraph("1. Importar auditorías (proceso semanal)", H2))
story.append(numbered([
    "Entra a la sección <b>Importar</b>.",
    "Arrastra los archivos <b>.xlsx</b> de las tiendas de la semana (puedes soltar varios a la vez) o haz clic en <b>Seleccionar archivos</b>.",
    "Haz clic en <b>Procesar</b>. Para cada archivo el sistema: verifica que contenga las hojas <b>Conc Dictámenes</b> y <b>Exhibiciones</b>, lee todos los catálogos (sin depender del nombre del archivo), valida que Exhibiciones coincida con Conc Dictámenes y guarda en la Base Histórica.",
    "Revisa el resultado de cada archivo (ver colores abajo).",
]))
story.append(Spacer(1, 4))
res = [
    ["Estado", "Significado"],
    ["IMPORTADO", "Se guardó correctamente."],
    ["CON DIFERENCIAS", "Hay diferencias Exhibiciones vs Conc Dictámenes. NO se importa hasta corregir (o activar 'Forzar')."],
    ["OMITIDO", "No es un archivo de auditoría válido (faltan las hojas requeridas)."],
    ["ERROR", "El archivo no se pudo abrir."],
]
t = Table(res, colWidths=[3.5 * cm, 12 * cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fb")]),
    ("TEXTCOLOR", (0, 1), (-1, -1), SLATE),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t)
story.append(Spacer(1, 4))
story.append(Paragraph("<b>Forzar importación:</b> activa el interruptor antes de procesar si necesitas importar aunque existan diferencias. Reimportar el mismo archivo (misma tienda/semana/año) reemplaza los datos anteriores; no se duplican.", SMALL))

story.append(Paragraph("2. Dashboard (indicadores)", H2))
story.append(Paragraph("Selecciona la <b>semana</b> arriba a la derecha. Verás: tiendas recibidas / pendientes / con diferencias, <b>% Negado</b>, <b>% Recuperado</b>, tallas auditadas, costo de oportunidad, ranking de tiendas y de responsables, resultados por catálogo y comparativo por semana.", BODY))

story.append(Paragraph("3. Descargar Concentrados en Excel", H2))
story.append(numbered([
    "Entra a <b>Concentrados</b>.",
    "En <b>Concentrado Semanal</b> elige la semana y presiona el botón de descarga: genera el Excel con el formato idéntico al MACHOTE.",
    "En <b>Concentrado Mensual</b> elige el mes (suma todas las semanas del mes).",
    "En <b>Concentrado Anual</b> elige el año (acumulado desde la Base Histórica).",
    "El archivo .xlsx se descarga a tu carpeta de Descargas.",
]))

story.append(Paragraph("4. Base Histórica y Registro de importaciones", H2))
story.append(Paragraph("En <b>Base Histórica</b> tienes dos pestañas:", BODY))
story.append(ListFlowable([
    ListItem(Paragraph("<b>Base Histórica</b>: tabla con el detalle por tienda y catálogo (Auditados, Negado, Recuperado, Sin Exhibición, Exhibición, Frente, Bodega, Costo). Incluye buscador.", BODY)),
    ListItem(Paragraph("<b>Registro de importaciones</b>: bitácora con fecha, hora, semana, tienda, archivo, resultado, observaciones y usuario.", BODY)),
], bulletColor=AMBER, leftIndent=16))

story.append(Paragraph("¿Dónde veo los archivos?", H2))
story.append(ListFlowable([
    ListItem(Paragraph("<b>Los archivos que importas (auditorías):</b> quedan registrados en <b>Base Histórica → Registro de importaciones</b> (con el nombre del archivo y su resultado). Sus datos consolidados se ven en la pestaña <b>Base Histórica</b>.", BODY)),
    ListItem(Paragraph("<b>Los reportes generados (Excel):</b> se descargan a la carpeta <b>Descargas</b> de tu computadora desde la sección <b>Concentrados</b>.", BODY)),
    ListItem(Paragraph("<b>El código fuente del proyecto:</b> desde la plataforma Emergent, con el ícono de <b>VS Code</b> (explorador de archivos) o con <b>Save to GitHub</b> para clonar el repositorio.", BODY)),
], bulletColor=AMBER, leftIndent=16))

story.append(Spacer(1, 8))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
story.append(Paragraph("Notas: la regla de validación Exhibiciones vs Conc Dictámenes es una primera versión (ajustable a la fórmula exacta de la Gerencia). El Resumen Ejecutivo y los formatos propios Mensual/Anual quedan como siguiente fase.", SMALL))

doc = SimpleDocTemplate("/app/frontend/public/Manual_SAR.pdf", pagesize=letter,
                        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                        title="Manual de Uso SAR")
doc.build(story)
print("PDF generado")
