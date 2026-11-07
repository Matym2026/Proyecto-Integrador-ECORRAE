"""Movimientos: traslados entre centros y entrega al destino final.

Los movimientos son el registro de auditoría de la trazabilidad, por eso no se
eliminan: solo se permite corregir la guía de remisión y las observaciones.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas as s
from ..crud import guardar, obtener
from ..database import get_db
from ..errors import ErrorNegocio

router = APIRouter(prefix="/api/movimientos", tags=["Movimientos"])

DESTINOS_SIN_PELIGROSOS = ("REUTILIZACION", "DONACION")


def _ultima_recomendacion(db: Session, dispositivo_id: int):
    return db.scalars(
        select(m.Evaluacion).where(m.Evaluacion.dispositivo_id == dispositivo_id)
        .order_by(m.Evaluacion.fecha.desc()).limit(1)
    ).first()


def _validar_compatibilidad(db: Session, dispositivos: list[m.Dispositivo], destino: m.Destino):
    """Regla ambiental: un RAEE con componentes peligrosos no puede ir a donación
    ni reutilización; debe ir a reciclaje o disposición final autorizada."""
    for d in dispositivos:
        ev = _ultima_recomendacion(db, d.id)
        if ev is None:
            raise ErrorNegocio(f"{d.codigo_trazabilidad} no tiene evaluación técnica")
        if ev.contiene_peligrosos and destino.tipo in DESTINOS_SIN_PELIGROSOS:
            raise ErrorNegocio(
                f"{d.codigo_trazabilidad} contiene componentes peligrosos y no puede enviarse a "
                f"{destino.tipo}. Elija un destino de RECICLAJE o DISPOSICION_FINAL"
            )


@router.get("", response_model=list[s.MovimientoOut])
def listar(tipo: s.TipoMovimiento | None = None, dispositivo_id: int | None = None,
           lote_id: int | None = None, limite: int = 200, db: Session = Depends(get_db)):
    stmt = select(m.Movimiento).order_by(m.Movimiento.fecha.desc()).limit(min(limite, 1000))
    if tipo:
        stmt = stmt.where(m.Movimiento.tipo == tipo)
    if dispositivo_id:
        stmt = stmt.where(m.Movimiento.dispositivo_id == dispositivo_id)
    if lote_id:
        stmt = stmt.where(m.Movimiento.lote_id == lote_id)
    return db.scalars(stmt).unique().all()


@router.get("/{id_}", response_model=s.MovimientoOut)
def consultar(id_: int, db: Session = Depends(get_db)):
    return obtener(db, m.Movimiento, id_, "Movimiento")


@router.post("", response_model=s.MovimientoOut, status_code=status.HTTP_201_CREATED)
def registrar(datos: s.MovimientoIn, db: Session = Depends(get_db)):
    if datos.responsable_id:
        obtener(db, m.Usuario, datos.responsable_id, "Usuario")
    mov = m.Movimiento(tipo=datos.tipo, responsable_id=datos.responsable_id,
                       guia_remision=datos.guia_remision, observaciones=datos.observaciones)

    if datos.lote_id:
        lote = obtener(db, m.Lote, datos.lote_id, "Lote")
        if lote.estado != "CERRADO":
            raise ErrorNegocio(f"El lote {lote.codigo} está {lote.estado}; solo se mueven lotes CERRADOS")
        mov.lote_id, mov.centro_origen_id = lote.id, lote.centro_id
        if datos.tipo == "TRASLADO":
            centro = obtener(db, m.Centro, datos.centro_destino_id, "Centro")
            if centro.id == lote.centro_id:
                raise ErrorNegocio("El centro de destino es el mismo centro actual del lote")
            mov.centro_destino_id = lote.centro_id = centro.id
            for d in lote.dispositivos:
                d.centro_actual_id = centro.id
        else:
            destino = obtener(db, m.Destino, datos.destino_id, "Destino")
            if not destino.activo:
                raise ErrorNegocio("El destino seleccionado está inactivo")
            _validar_compatibilidad(db, lote.dispositivos, destino)
            mov.destino_id = lote.destino_id = destino.id
            lote.estado = "ENTREGADO"
            for d in lote.dispositivos:
                d.estado = "EN_DESTINO"
    else:
        d = obtener(db, m.Dispositivo, datos.dispositivo_id, "Dispositivo")
        if d.lote_id:
            raise ErrorNegocio(f"{d.codigo_trazabilidad} pertenece a un lote: registre el movimiento sobre el lote")
        if d.estado == "EN_DESTINO":
            raise ErrorNegocio(f"{d.codigo_trazabilidad} ya fue entregado a su destino final")
        mov.dispositivo_id, mov.centro_origen_id = d.id, d.centro_actual_id
        if datos.tipo == "TRASLADO":
            centro = obtener(db, m.Centro, datos.centro_destino_id, "Centro")
            if centro.id == d.centro_actual_id:
                raise ErrorNegocio("El centro de destino es el mismo centro actual del dispositivo")
            mov.centro_destino_id = d.centro_actual_id = centro.id
        else:
            if d.estado != "EVALUADO":
                raise ErrorNegocio("Solo se entregan a destino final dispositivos EVALUADOS")
            destino = obtener(db, m.Destino, datos.destino_id, "Destino")
            _validar_compatibilidad(db, [d], destino)
            mov.destino_id = destino.id
            d.estado = "EN_DESTINO"

    mov.fecha = datetime.now()
    return guardar(db, mov)


class MovimientoUpdate(BaseModel):
    guia_remision: str | None = Field(default=None, max_length=40)
    observaciones: str | None = None


@router.patch("/{id_}", response_model=s.MovimientoOut)
def corregir(id_: int, datos: MovimientoUpdate, db: Session = Depends(get_db)):
    mov = obtener(db, m.Movimiento, id_, "Movimiento")
    mov.guia_remision = (datos.guia_remision or "").strip() or None
    mov.observaciones = (datos.observaciones or "").strip() or None
    return guardar(db, mov)
