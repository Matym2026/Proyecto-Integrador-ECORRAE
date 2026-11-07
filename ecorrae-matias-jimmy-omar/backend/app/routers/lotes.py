"""Lotes: agrupación de dispositivos evaluados para traslado y entrega."""
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas as s
from ..crud import obtener
from ..database import get_db
from ..errors import ErrorNegocio
from ..storage import storage

router = APIRouter(prefix="/api/lotes", tags=["Lotes"])


def _salida(db: Session, lote: m.Lote) -> s.LoteOut:
    total, peso = db.execute(
        select(func.count(m.Dispositivo.id), func.coalesce(func.sum(m.Dispositivo.peso_kg), 0))
        .where(m.Dispositivo.lote_id == lote.id)
    ).one()
    out = s.LoteOut.model_validate(lote)
    out.total_dispositivos, out.peso_total_kg = total, Decimal(peso)
    return out


def _siguiente_codigo(db: Session) -> str:
    prefijo = f"LOTE-{datetime.now().year}-"
    ultimo = db.scalar(select(func.max(m.Lote.codigo)).where(m.Lote.codigo.like(f"{prefijo}%")))
    n = int(ultimo.rsplit("-", 1)[1]) + 1 if ultimo else 1
    return f"{prefijo}{n:03d}"


def _lote_abierto(db: Session, id_: int) -> m.Lote:
    lote = obtener(db, m.Lote, id_, "Lote")
    if lote.estado != "ABIERTO":
        raise ErrorNegocio(f"El lote {lote.codigo} está {lote.estado}; solo se modifican lotes ABIERTOS")
    return lote


@router.get("", response_model=list[s.LoteOut])
def listar(estado: s.EstadoLote | None = None, centro_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(m.Lote).order_by(m.Lote.id.desc())
    if estado:
        stmt = stmt.where(m.Lote.estado == estado)
    if centro_id:
        stmt = stmt.where(m.Lote.centro_id == centro_id)
    return [_salida(db, l) for l in db.scalars(stmt).unique().all()]


@router.get("/{id_}", response_model=s.LoteOut)
def consultar(id_: int, db: Session = Depends(get_db)):
    return _salida(db, obtener(db, m.Lote, id_, "Lote"))


@router.post("", response_model=s.LoteOut, status_code=status.HTTP_201_CREATED)
def crear(datos: s.LoteIn, db: Session = Depends(get_db)):
    centro = obtener(db, m.Centro, datos.centro_id, "Centro")
    if not centro.activo:
        raise ErrorNegocio("El centro seleccionado está inactivo")
    lote = m.Lote(
        codigo=datos.codigo or _siguiente_codigo(db), descripcion=datos.descripcion,
        centro_id=centro.id, creado_por=datos.creado_por, estado="ABIERTO",
    )
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return _salida(db, lote)


@router.put("/{id_}", response_model=s.LoteOut)
def actualizar(id_: int, datos: s.LoteUpdate, db: Session = Depends(get_db)):
    lote = obtener(db, m.Lote, id_, "Lote")
    lote.descripcion = datos.descripcion
    db.commit()
    return _salida(db, lote)


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_: int, db: Session = Depends(get_db)):
    lote = _lote_abierto(db, id_)
    for d in lote.dispositivos:  # los equipos vuelven a estar disponibles
        d.estado, d.lote_id = "EVALUADO", None
    claves = db.scalars(select(m.Evidencia.clave_objeto).where(m.Evidencia.lote_id == id_)).all()
    db.delete(lote)
    db.commit()
    for c in claves:
        storage.eliminar(c)


@router.post("/{id_}/dispositivos", response_model=s.LoteOut)
def asignar(id_: int, datos: s.AsignarDispositivos, db: Session = Depends(get_db)):
    """Agrega dispositivos EVALUADOS que estén en el mismo centro que el lote."""
    lote = _lote_abierto(db, id_)
    for did in dict.fromkeys(datos.dispositivo_ids):
        d = obtener(db, m.Dispositivo, did, "Dispositivo")
        if d.estado != "EVALUADO" or d.lote_id:
            raise ErrorNegocio(f"{d.codigo_trazabilidad} está {d.estado}: solo se agregan dispositivos EVALUADOS sin lote")
        if d.centro_actual_id != lote.centro_id:
            raise ErrorNegocio(f"{d.codigo_trazabilidad} está en otro centro ({d.centro_actual.nombre})")
        d.lote_id, d.estado = lote.id, "EN_LOTE"
    db.commit()
    return _salida(db, lote)


@router.delete("/{id_}/dispositivos/{dispositivo_id}", response_model=s.LoteOut)
def quitar(id_: int, dispositivo_id: int, db: Session = Depends(get_db)):
    lote = _lote_abierto(db, id_)
    d = obtener(db, m.Dispositivo, dispositivo_id, "Dispositivo")
    if d.lote_id != lote.id:
        raise ErrorNegocio(f"{d.codigo_trazabilidad} no pertenece al lote {lote.codigo}")
    d.lote_id, d.estado = None, "EVALUADO"
    db.commit()
    return _salida(db, lote)


@router.post("/{id_}/cerrar", response_model=s.LoteOut)
def cerrar(id_: int, db: Session = Depends(get_db)):
    """Cierra el lote: ya no admite cambios y queda listo para traslado o entrega."""
    lote = _lote_abierto(db, id_)
    if not lote.dispositivos:
        raise ErrorNegocio("No se puede cerrar un lote vacío")
    lote.estado, lote.fecha_cierre = "CERRADO", datetime.now()
    db.commit()
    return _salida(db, lote)
