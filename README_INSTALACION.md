# SAR — Sistema de Auditoría y Recuperación
## Guía de instalación (para correr en tu propio servidor / PC)

> IMPORTANTE: Esta es una aplicación **full-stack** (no es un .exe de "instalar y listo").
> Requiere 3 componentes: **Node.js** (frontend), **Python** (backend) y **MongoDB** (base de datos).

---

## 1. Requisitos previos (instalar una sola vez)
- **Node.js 18+** y **Yarn**  → https://nodejs.org  (luego: `npm install -g yarn`)
- **Python 3.11+**           → https://www.python.org
- **MongoDB Community**      → https://www.mongodb.com/try/download/community
  (o usar MongoDB Atlas en la nube y copiar su cadena de conexión)

---

## 2. Estructura del proyecto
```
/backend      -> API en FastAPI (Python)
   server.py
   sar_excel.py          (motor de Excel: parseo + reportes)
   templates/machote.xlsx (plantilla del Concentrado)
   requirements.txt
   .env                  (configuración: MONGO_URL, DB_NAME)
/frontend     -> Interfaz en React
   src/ ...
   package.json
   .env                  (REACT_APP_BACKEND_URL)
```

---

## 3. Configurar variables de entorno

**backend/.env**
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="sar_db"
CORS_ORIGINS="*"
```

**frontend/.env**
```
REACT_APP_BACKEND_URL=http://localhost:8001
```
(Si lo publicas en un servidor, cambia esa URL por la dirección real del backend.)

---

## 4. Arrancar el BACKEND
```bash
cd backend
python -m venv venv
# Windows:  venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001
```
El backend queda en: http://localhost:8001/api/

---

## 5. Arrancar el FRONTEND (en otra terminal)
```bash
cd frontend
yarn install
yarn start
```
Se abre en: http://localhost:3000

---

## 6. Uso
1. Abre http://localhost:3000
2. Ve a **Importar** y sube los .xlsx de las tiendas.
3. Genera los **Concentrados** (Semanal/Mensual/Anual) en Excel.
4. Consulta el **Dashboard** y la **Base Histórica**.

---

## Notas
- MongoDB debe estar corriendo antes de iniciar el backend.
- Para producción real 24/7, lo más sencillo es usar el **Deploy de Emergent**
  (no requiere instalar nada) o subir el código a un servidor con Docker.
- La carpeta `node_modules` NO viene incluida en el zip (se genera con `yarn install`).
