"""EcoRAEE Cloud - API backend (FastAPI).

Local:  uvicorn app.main:app --reload --port 8000
AWS:    el mismo servicio corre en EC2 (subred privada, sg-backend) detrás del ALB.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import FRONTEND_ORIGIN
from .errors import registrar_manejadores
from .routers import catalogos, dashboard, dispositivos, evaluaciones, evidencias, lotes, movimientos

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="EcoRAEE Cloud API",
    version="1.0.0",
    description="Gestión y trazabilidad de Residuos de Aparatos Eléctricos y Electrónicos (RAEE)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_manejadores(app)

for r in (dashboard.router, catalogos.usuarios, catalogos.centros, catalogos.destinos,
          dispositivos.router, lotes.router, evaluaciones.router, movimientos.router, evidencias.router):
    app.include_router(r)


@app.get("/", include_in_schema=False)
def raiz():
    return {"servicio": "EcoRAEE Cloud API", "documentacion": "/docs"}
