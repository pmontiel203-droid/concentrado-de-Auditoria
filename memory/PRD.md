# PRD — Sistema de Auditoría y Recuperación (SAR)

## Problema original
Consolidar automáticamente las auditorías semanales de 17 tiendas (archivos Excel con hojas por catálogo que alimentan `Conc Dictámenes` y `Exhibiciones`), eliminando el copiado manual hacia el "Concentrado de Auditoría y Recuperación". Validar que Exhibiciones coincida con Conc Dictámenes antes de importar, guardar todo en una Base Histórica única y generar concentrados Semanal/Mensual/Anual con formato idéntico al MACHOTE de la Gerencia de Mejoras, más un dashboard de indicadores.

## Decisiones del usuario
- Web app (subida de múltiples .xlsx por semana, drag & drop) en lugar de carpeta local.
- Sin autenticación (acceso libre).
- Prioridad: reportes descargables en Excel con formato idéntico (plantilla MACHOTE).
- Usar exactamente las columnas de `Conc Dictamenes`.

## Arquitectura
- Backend FastAPI (`/app/backend/server.py`) + motor de Excel (`/app/backend/sar_excel.py`, openpyxl) + plantilla `/app/backend/templates/machote.xlsx`.
- MongoDB: colecciones `registros` (Base Histórica, un doc por tienda+catálogo+semana) e `import_logs`.
- Frontend React: sidebar navy + acento ámbar, fuentes Sora/Manrope. Páginas: Dashboard, Importar, Concentrados, Base Histórica.

## Mapeo de columnas (Conc Dictamenes → registro)
Auditados=Tallas Auditadas(col4), Frente=Frenteos(col6), Bodega=Bodega Venta(col8), Negado=suma causas cols6-19, Recuperado=suma bloque recuperadas, Exhibición=col15, Sin Exhibición=col21, Costo=col20. Causas de negado mapean 1:1 en orden a los grupos de columnas del MACHOTE (col 8,12,...,60).

## Implementado (2026-06)
- Importación multi-archivo con detección de archivo válido (hojas requeridas), parseo por catálogo, validación Exhibiciones vs Conc Dictámenes (bloqueante salvo `forzar`), inserción idempotente en Base Histórica y registro de importaciones.
- Dashboard: tiendas recibidas/pendientes/con diferencias, % Negado, % Recuperado, costo, rankings de tiendas y responsables, resultados por catálogo, comparativo por semana.
- Reportes descargables: Concentrado Semanal (formato MACHOTE idéntico vía relleno de plantilla), Mensual y Anual.
- Base Histórica y Registro de importaciones con búsqueda.
- Verificado: 14/14 pruebas backend (iteration_1.json).

## Notas / limitaciones conocidas
- La regla de validación Exhibiciones vs Conc Dictámenes es una aproximación (suma de áreas de oportunidad vs incidencias de exhibición); ajustable si la Gerencia define la fórmula exacta.
- Mensual/Anual usan la misma plantilla MACHOTE agregada (no las hojas mensuales del archivo ANUAL).
- TOTAL_TIENDAS = 17 (constante).

## Backlog priorizado
- P1: Formatos propios de Concentrado Mensual y Anual (según archivo ANUAL) y Resumen Ejecutivo.
- P1: Confirmar/ajustar regla exacta de validación de Exhibiciones con la Gerencia.
- P2: Catálogo maestro de las 17 tiendas y detección de faltantes por nombre.
- P2: Sección "Barras" en el MACHOTE si aplica; columnas de costo recuperado por catálogo.
- P2: Exportar dashboard a PDF; autenticación si se requiere control de acceso.
