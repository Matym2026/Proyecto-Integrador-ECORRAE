"""Utilidades CRUD reutilizables."""
from typing import Type, TypeVar

from sqlalchemy.orm import Session

from .errors import NoEncontrado

T = TypeVar("T")


def obtener(db: Session, modelo: Type[T], id_: int, entidad: str | None = None) -> T:
    obj = db.get(modelo, id_)
    if obj is None:
        raise NoEncontrado(entidad or modelo.__name__, id_)
    return obj


def guardar(db: Session, obj):
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
