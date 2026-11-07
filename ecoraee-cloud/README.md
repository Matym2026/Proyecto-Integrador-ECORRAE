# EcoRAEE Cloud – Parte II: desarrollo local

Primera versión funcional de EcoRAEE Cloud, el sistema de trazabilidad de **Residuos de Aparatos Eléctricos y Electrónicos (RAEE)**: desde que un equipo ingresa a un centro de acopio hasta que se entrega a un gestor autorizado.

Todo corre **en local**. No se despliega nada en AWS ni se usan servicios en la nube.

| Capa | Tecnología local | Equivalente en la arquitectura AWS (Parte I) |
|---|---|---|
| Frontend | React 18 + Vite (puerto 5173) | Usuarios → Internet Gateway → ALB (HTTPS 443) |
| Backend / API | Python FastAPI + SQLAlchemy (puerto 8000) | EC2 Backend en subred privada app (`sg-backend`, HTTP 8000) |
| Base de datos | PostgreSQL 16 (puerto 5432) | RDS PostgreSQL en subred privada BD (`sg-rds`, 5432) |
| Evidencias | Carpeta `backend/storage/` con claves tipo S3 | Amazon S3 (evidencias RAEE) vía Endpoint de S3 |
| Credenciales BD | Archivo `backend/.env` | Secrets Manager (`EcoRAEE-Secrets-BD-Lectura`) |
| Logs | Consola de uvicorn | CloudWatch Logs |

---

## 1. Requisitos

- **Python 3.11 o superior**
- **Node.js 18 o superior** (incluye npm)
- **PostgreSQL 14 o superior**, de una de estas dos formas:
  - **Opción A (recomendada):** Docker Desktop
  - **Opción B:** PostgreSQL instalado en Windows (con pgAdmin)

## 2. Base de datos

### Opción A – Docker
```bash
docker compose up -d
```
Crea la base `ecoraee` (usuario `ecoraee` / clave `ecoraee123`) y carga el esquema y los datos de prueba automáticamente.
Para volver a los datos de prueba: `docker compose down -v` y luego `docker compose up -d`.

### Opción B – PostgreSQL instalado
En **pgAdmin** (Query Tool conectado como `postgres`) o en `psql`:
```sql
CREATE USER ecoraee WITH PASSWORD 'ecoraee123';
CREATE DATABASE ecoraee OWNER ecoraee;
```
Luego cargue los scripts **en orden**, conectado a la base `ecoraee`:
```bash
psql -U ecoraee -d ecoraee -h localhost -f database/01_schema.sql
psql -U ecoraee -d ecoraee -h localhost -f database/02_seed.sql
```
(En pgAdmin: abra cada archivo en el Query Tool de la base `ecoraee` y ejecútelo.)
Ejecutar de nuevo ambos scripts reinicia la base con los datos de prueba.

## 3. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env        # Windows   (Linux/Mac: cp .env.example .env)
uvicorn app.main:app --reload --port 8000
```
- Comprobar: http://localhost:8000/api/health → `{"estado":"ok","base_de_datos":"conectada"}`
- **Documentación interactiva de la API (Swagger):** http://localhost:8000/docs

## 4. Frontend (React)
En otra terminal:
```bash
cd frontend
npm install
npm run dev
```
Abrir **http://localhost:5173**. Vite redirige `/api` al backend en el puerto 8000.
El indicador verde de la barra lateral («API + BD conectadas») confirma la integración de las tres capas.

## 5. Prueba de integración automática
Con el backend corriendo (y la base recién cargada):
```bash
cd backend
pip install httpx
python tests/prueba_flujo.py
```
Recorre el ciclo completo (registro → evaluación → lote → traslado → entrega → evidencia → trazabilidad) y los casos de error: **38 verificaciones**.
Al terminar, recargue la base (paso 2) para dejar los datos de prueba limpios antes de grabar.

---

## Modelo de datos

```
usuarios ─┬─< dispositivos >── centros ──< lotes >── destinos
          │        │  └────────────────────┘  (lote_id)
          ├─< evaluaciones >─┘
          ├─< movimientos  >── dispositivo | lote, centro origen/destino, destino
          └─< evidencias   >── dispositivo | lote   (archivo en storage / S3)
```

| Tabla | Propósito | Restricciones destacadas |
|---|---|---|
| `usuarios` | Personas que operan el sistema | `email` único con formato válido; `rol` ∈ ADMIN, OPERADOR, EVALUADOR, AUDITOR |
| `centros` | Acopio, almacén o tratamiento | `nombre` único; `tipo` controlado |
| `destinos` | Gestores autorizados | RUC de 13 dígitos; tipo REUTILIZACION, RECICLAJE, DONACION, DISPOSICION_FINAL |
| `lotes` | Agrupación para traslado y entrega | `codigo` único; ENTREGADO exige destino; fecha de cierre ≥ creación |
| `dispositivos` | Cada RAEE | código de trazabilidad y serie únicos; `peso_kg` entre 0 y 2000; FK a centro, lote y usuario |
| `evaluaciones` | Diagnóstico técnico | REUTILIZACION exige funcional **y** datos borrados (CHECK) |
| `movimientos` | Historial de auditoría | debe referirse a un dispositivo o un lote; reglas por tipo (CHECK) |
| `evidencias` | Metadatos de archivos | `clave_objeto` única (clave S3); tamaño > 0 |

Las FK usan `RESTRICT` (no se borra un centro con equipos), `CASCADE` (al borrar un dispositivo se borra su historial) o `SET NULL` según corresponda.

## Ciclo de trazabilidad y reglas de negocio

1. **Registro e ingreso**: se registra el equipo, se genera su código `RAEE-AAAA-NNNNN` y, en la misma transacción, el movimiento de **INGRESO** al centro.
2. **Evaluación técnica**: solo usuarios EVALUADOR/ADMIN. Define estado físico, funcionalidad, borrado de datos, componentes peligrosos y tratamiento recomendado. El equipo pasa a **EVALUADO**.
3. **Consolidación en lote**: solo se agregan equipos evaluados, sin lote y del mismo centro. El lote se **cierra** antes de moverlo.
4. **Traslado**: lote cerrado (o equipo suelto) a otro centro; todos sus dispositivos actualizan su ubicación.
5. **Entrega a destino final**: el lote pasa a **ENTREGADO** y sus equipos a **EN_DESTINO**. Regla ambiental: un equipo con componentes peligrosos **no** puede ir a DONACION ni REUTILIZACION.
6. **Evidencias**: fotos o PDF (máx. 10 MB) asociados a un dispositivo o lote.
7. **Consulta de trazabilidad**: `GET /api/dispositivos/{id}/trazabilidad` devuelve la línea de tiempo completa.

Los movimientos no se eliminan (son el registro de auditoría); solo se corrige la guía de remisión y las observaciones.

## Endpoints principales

| Módulo | Endpoints |
|---|---|
| Catálogos | `GET/POST /api/{usuarios\|centros\|destinos}` · `GET/PUT/DELETE /api/{recurso}/{id}` |
| Dispositivos | `GET/POST /api/dispositivos` · `GET/PUT/DELETE /api/dispositivos/{id}` · `GET /api/dispositivos/{id}/trazabilidad` |
| Evaluaciones | `GET/POST /api/evaluaciones` · `GET/PUT/DELETE /api/evaluaciones/{id}` |
| Lotes | `GET/POST /api/lotes` · `GET/PUT/DELETE /api/lotes/{id}` · `POST /api/lotes/{id}/dispositivos` · `DELETE /api/lotes/{id}/dispositivos/{did}` · `POST /api/lotes/{id}/cerrar` |
| Movimientos | `GET/POST /api/movimientos` · `GET/PATCH /api/movimientos/{id}` |
| Evidencias | `GET/POST /api/evidencias` · `GET /api/evidencias/{id}/archivo` · `DELETE /api/evidencias/{id}` |
| Otros | `GET /api/health` · `GET /api/dashboard` |

**Manejo de errores** (siempre `{"detail": "..."}` en español):
`404` registro inexistente · `422` validación de datos (con `errores` por campo) · `400` regla de negocio · `409` duplicados o integridad referencial · `413/415` archivo demasiado grande o tipo no permitido · `503` base de datos caída.

## Estructura del proyecto
```
ecoraee-cloud/
├── docker-compose.yml          PostgreSQL local
├── database/
│   ├── 01_schema.sql           Tablas, PK, FK, CHECK, índices
│   └── 02_seed.sql             Datos de prueba
├── backend/
│   ├── app/
│   │   ├── main.py             App FastAPI, CORS, routers
│   │   ├── config.py           Variables de entorno (.env)
│   │   ├── database.py         Conexión SQLAlchemy
│   │   ├── models.py           Modelos ORM
│   │   ├── schemas.py          Validación Pydantic
│   │   ├── errors.py           Manejo centralizado de errores
│   │   ├── storage.py          Almacenamiento de evidencias (local → S3)
│   │   └── routers/            Un archivo por módulo
│   └── tests/prueba_flujo.py   Prueba de integración
└── frontend/
    └── src/
        ├── api.js              Cliente HTTP
        ├── components/         Formulario validado, modales, evidencias
        └── pages/              Panel, Dispositivos, Evaluaciones, Lotes, Movimientos, Catálogos
```

## Camino a AWS (siguiente etapa)
- `DATABASE_URL` apuntará al endpoint de RDS, leído desde Secrets Manager con el rol `EcoRAEE-EC2-Role`.
- `storage.py`: reemplazar `LocalStorage` por una clase con `boto3` (`put_object`, `get_object`, `delete_object`). Las claves (`dispositivos/5/…`, `lotes/2/…`) ya siguen la estructura del bucket.
- El frontend compilado (`npm run build`) se sirve detrás del ALB, que enruta `/api` al backend en EC2.
