"""Indicadores generales para la pantalla de inicio."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas as s
from ..database import get_db

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"estado": "ok", "base_de_datos": "conectada"}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    por_estado = dict(db.execute(
        select(m.Dispositivo.estado, func.count()).group_by(m.Dispositivo.estado)).all())
    por_tipo = [{"tipo": t, "cantidad": c} for t, c in db.execute(
        select(m.Dispositivo.tipo, func.count()).group_by(m.Dispositivo.tipo).order_by(func.count().desc())).all()]
    peso_total = db.scalar(select(func.coalesce(func.sum(m.Dispositivo.peso_kg), 0)))
    peso_entregado = db.scalar(select(func.coalesce(func.sum(m.Dispositivo.peso_kg), 0))
                               .where(m.Dispositivo.estado == "EN_DESTINO"))
    por_centro = [{"centro": n, "cantidad": c} for n, c in db.execute(
        select(m.Centro.nombre, func.count(m.Dispositivo.id))
        .join(m.Dispositivo, m.Dispositivo.centro_actual_id == m.Centro.id, isouter=True)
        .where(m.Dispositivo.estado != "EN_DESTINO")
        .group_by(m.Centro.nombre).order_by(m.Centro.nombre)).all()]
    lotes_por_estado = dict(db.execute(select(m.Lote.estado, func.count()).group_by(m.Lote.estado)).all())
    ultimos = db.scalars(select(m.Movimiento).order_by(m.Movimiento.fecha.desc()).limit(6)).unique().all()
    return {
        "total_dispositivos": sum(por_estado.values()),
        "por_estado": {e: por_estado.get(e, 0) for e in ("REGISTRADO", "EVALUADO", "EN_LOTE", "EN_DESTINO")},
        "por_tipo": por_tipo,
        "peso_total_kg": float(peso_total),
        "peso_entregado_kg": float(peso_entregado),
        "en_centros": por_centro,
        "lotes_por_estado": {e: lotes_por_estado.get(e, 0) for e in ("ABIERTO", "CERRADO", "ENTREGADO")},
        "ultimos_movimientos": [s.MovimientoOut.model_validate(x).model_dump(mode="json") for x in ultimos],
    }
