"""CRUD de catálogos: usuarios, centros y destinos."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..crud import guardar, obtener
from ..database import get_db


def crear_router_catalogo(prefijo, modelo, esquema_in, esquema_out, entidad, campos_busqueda):
    router = APIRouter(prefix=f"/api/{prefijo}", tags=[entidad])

    @router.get("", response_model=list[esquema_out])
    def listar(
        q: str | None = Query(None, description="Búsqueda por texto"),
        solo_activos: bool = False,
        db: Session = Depends(get_db),
    ):
        stmt = select(modelo).order_by(modelo.id)
        if q:
            stmt = stmt.where(or_(*[getattr(modelo, c).ilike(f"%{q}%") for c in campos_busqueda]))
        if solo_activos:
            stmt = stmt.where(modelo.activo.is_(True))
        return db.scalars(stmt).all()

    @router.get("/{id_}", response_model=esquema_out)
    def consultar(id_: int, db: Session = Depends(get_db)):
        return obtener(db, modelo, id_, entidad)

    @router.post("", response_model=esquema_out, status_code=status.HTTP_201_CREATED)
    def crear(datos: esquema_in, db: Session = Depends(get_db)):
        return guardar(db, modelo(**datos.model_dump()))

    @router.put("/{id_}", response_model=esquema_out)
    def actualizar(id_: int, datos: esquema_in, db: Session = Depends(get_db)):
        obj = obtener(db, modelo, id_, entidad)
        for k, v in datos.model_dump().items():
            setattr(obj, k, v)
        return guardar(db, obj)

    @router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
    def eliminar(id_: int, db: Session = Depends(get_db)):
        obj = obtener(db, modelo, id_, entidad)
        db.delete(obj)
        db.commit()  

    return router


usuarios = crear_router_catalogo(
    "usuarios", models.Usuario, schemas.UsuarioIn, schemas.UsuarioOut, "Usuario", ["nombre", "email"]
)
centros = crear_router_catalogo(
    "centros", models.Centro, schemas.CentroIn, schemas.CentroOut, "Centro", ["nombre", "ciudad"]
)
destinos = crear_router_catalogo(
    "destinos", models.Destino, schemas.DestinoIn, schemas.DestinoOut, "Destino", ["nombre", "ciudad"]
)
