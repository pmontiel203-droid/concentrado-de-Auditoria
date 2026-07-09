# Manual de Uso — Sistema de Auditoría y Recuperación (SAR)

## 1. Acceso
Abre en el navegador: **https://audit-recovery.preview.emergentagent.com**
No requiere usuario ni contraseña (acceso libre).

El sistema tiene 4 secciones en el menú lateral:
- **Dashboard** — indicadores de la semana.
- **Importar** — subir los archivos de las tiendas.
- **Concentrados** — descargar los reportes en Excel.
- **Base Histórica** — ver todos los datos y el registro de importaciones.

---

## 2. Importar auditorías (proceso semanal)
1. Entra a **Importar**.
2. Arrastra los archivos `.xlsx` de las tiendas de la semana (puedes soltar varios a la vez) o haz clic en **Seleccionar archivos**.
3. Haz clic en **Procesar**. El sistema, para cada archivo:
   - Verifica que sea un archivo válido (que contenga las hojas **Conc Dictámenes** y **Exhibiciones**). Si no las tiene, lo marca como **OMITIDO**.
   - Lee automáticamente todos los catálogos (no depende del nombre del archivo).
   - **Valida** que Exhibiciones coincida con Conc Dictámenes.
   - Guarda la información en la Base Histórica.
4. Verás el resultado de cada archivo:
   - 🟢 **IMPORTADO** — se guardó correctamente.
   - 🟡 **CON DIFERENCIAS** — hay diferencias entre Exhibiciones y Conc Dictámenes; **no se importa** hasta que la tienda corrija (o actives "Forzar").
   - ⚪ **OMITIDO** — no es un archivo de auditoría válido.
   - 🔴 **ERROR** — el archivo no se pudo abrir.

**Forzar importación:** si necesitas importar aunque haya diferencias, activa el interruptor *"Forzar importación"* antes de procesar.

> Reimportar el mismo archivo (misma tienda/semana/año) **reemplaza** los datos anteriores; no se duplican.

---

## 3. Dashboard
Selecciona la **semana** arriba a la derecha. Verás:
- Tiendas recibidas / pendientes / con diferencias.
- **% Negado** y **% Recuperado**, tallas auditadas y costo de oportunidad.
- Ranking de tiendas y de responsables.
- Resultados por catálogo (gráfica).
- Comparativo por semana.

---

## 4. Descargar Concentrados (Excel)
Entra a **Concentrados**. Hay 3 tarjetas:
- **Concentrado Semanal** — elige la semana y presiona el botón de descarga. Genera el Excel con el **formato idéntico al MACHOTE** de la Gerencia.
- **Concentrado Mensual** — elige el mes; suma todas las semanas del mes.
- **Concentrado Anual** — elige el año; acumulado anual desde la Base Histórica.

El archivo `.xlsx` se descarga automáticamente a tu carpeta de Descargas.

---

## 5. Base Histórica y Registro de importaciones
En **Base Histórica**:
- Pestaña **Base Histórica**: tabla con el detalle por tienda y catálogo (Auditados, Negado, Recuperado, Sin Exhibición, Exhibición, Frente, Bodega, Costo). Tiene buscador.
- Pestaña **Registro de importaciones**: bitácora con fecha, hora, semana, tienda, archivo, resultado, observaciones y usuario.

---

## Notas importantes
- La **regla de validación** Exhibiciones vs Conc Dictámenes es una primera versión (compara áreas de oportunidad vs incidencias de exhibición). Si la Gerencia define la fórmula exacta, se ajusta.
- Los concentrados Mensual y Anual usan la misma plantilla MACHOTE agregada. El formato propio del archivo ANUAL y el **Resumen Ejecutivo** quedan como siguiente fase.
