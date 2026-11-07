"""Evaluaciones técnicas: determinan el tratamiento recomendado del RAEE."""
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas as s
from ..crud import guardar, obtener
from ..database import get_db
from ..errors import ErrorNegocio

router = APIRouter(prefix="/api/evaluaciones", tags=["Evaluaciones"])


def _validar_evaluador(db: Session, evaluador_id: int):
    u = obtener(db, m.Usuario, evaluador_id, "Usuario")
    if u.rol not in ("EVALUADOR", "ADMIN") or not u.activo:
        raise ErrorNegocio(f"{u.nombre} no tiene rol EVALUADOR activo")


def _dispositivo_evaluable(db: Session, dispositivo_id: int) -> m.Dispositivo:
    d = obtener(db, m.Dispositivo, dispositivo_id, "Dispositivo")
    if d.estado not in ("REGISTRADO", "EVALUADO"):
        raise ErrorNegocio(f"{d.codigo_trazabilidad} está {d.estado}; solo se evalúan equipos REGISTRADOS o EVALUADOS")
    return d


@router.get("", response_model=list[s.EvaluacionOut])
def listar(dispositivo_id: int | None = None, recomendacion: s.Recomendacion | None = None,
           db: Session = Depends(get_db)):
    stmt = select(m.Evaluacion).order_by(m.Evaluacion.fecha.desc())
    if dispositivo_id:
        stmt = stmt.where(m.Evaluacion.dispositivo_id == dispositivo_id)
    if recomendacion:
        stmt = stmt.where(m.Evaluacion.recomendacion == recomendacion)
    return db.scalars(stmt).unique().all()


@router.get("/{id_}", response_model=s.EvaluacionOut)
def consultar(id_: int, db: Session = Depends(get_db)):
    return obtener(db, m.Evaluacion, id_, "Evaluación")


@router.post("", response_model=s.EvaluacionOut, status_code=status.HTTP_201_CREATED)
def crear(datos: s.EvaluacionIn, db: Session = Depends(get_db)):
    d = _dispositivo_evaluable(db, datos.dispositivo_id)
    _validar_evaluador(db, datos.evaluador_id)
    ev = m.Evaluacion(**datos.model_dump())
    d.estado = "EVALUADO"
    return guardar(db, ev)


@router.put("/{id_}", response_model=s.EvaluacionOut)
def actualizar(id_: int, datos: s.EvaluacionIn, db: Session = Depends(get_db)):
    ev = obtener(db, m.Evaluacion, id_, "Evaluación")
    if datos.dispositivo_id != ev.dispositivo_id:
        raise ErrorNegocio("No se puede cambiar el dispositivo de una evaluación")
    _dispositivo_evaluable(db, ev.dispositivo_id)
    _validar_evaluador(db, datos.evaluador_id)
    for k, v in datos.model_dump().items():
        setattr(ev, k, v)
    return guardar(db, ev)


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_: int, db: Session = Depends(get_db)):
    ev = obtener(db, m.Evaluacion, id_, "Evaluación")
    d = _dispositivo_evaluable(db, ev.dispositivo_id)
    db.delete(ev)
    db.flush()
    restantes = db.scalar(select(func.count()).where(m.Evaluacion.dispositivo_id == d.id))
    if restantes == 0:
        d.estado = "REGISTRADO"
    db.commit()
