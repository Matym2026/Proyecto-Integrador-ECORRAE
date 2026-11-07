"""Manejo centralizado de errores: todas las respuestas de error tienen la
forma {"detail": "mensaje legible", "errores": [...] (opcional)}."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError

log = logging.getLogger("ecoraee")


class ErrorNegocio(Exception):
    """Violación de una regla del proceso de trazabilidad."""

    def __init__(self, mensaje: str, status_code: int = 400):
        self.mensaje = mensaje
        self.status_code = status_code


class NoEncontrado(ErrorNegocio):
    def __init__(self, entidad: str, id_):
        super().__init__(f"{entidad} con id {id_} no existe", 404)


TRADUCCIONES = {
    "missing": "Campo obligatorio",
    "string_type": "Campo obligatorio",
    "int_type": "Campo obligatorio",
    "decimal_type": "Debe ser un número",
    "float_parsing": "Debe ser un número",
    "decimal_max_places": "Máximo {decimal_places} decimales",
    "value_error.email": "Correo inválido",
    "string_too_short": "Texto demasiado corto",
    "string_too_long": "Texto demasiado largo",
    "string_pattern_mismatch": "Formato inválido",
    "literal_error": "Valor no permitido",
    "greater_than": "Debe ser mayor que {gt}",
    "less_than_equal": "Debe ser menor o igual que {le}",
    "int_parsing": "Debe ser un número entero",
    "decimal_parsing": "Debe ser un número",
    "value_error": "{msg}",
    "too_short": "Debe incluir al menos un elemento",
    "bool_parsing": "Debe ser verdadero o falso",
}

MENSAJES_CONSTRAINT = {
    "usuarios_email_key": "Ya existe un usuario con ese correo",
    "centros_nombre_key": "Ya existe un centro con ese nombre",
    "destinos_nombre_key": "Ya existe un destino con ese nombre",
    "lotes_codigo_key": "Ya existe un lote con ese código",
    "dispositivos_numero_serie_key": "Ya existe un dispositivo con ese número de serie",
    "dispositivos_codigo_trazabilidad_key": "Código de trazabilidad duplicado",
    "chk_eval_reutilizacion": "Para REUTILIZACION el equipo debe ser funcional y con datos borrados",
}


def _mensaje_campo(err: dict) -> str:
    plantilla = TRADUCCIONES.get(err["type"])
    if not plantilla:
        return err["msg"]
    msg = err["msg"].removeprefix("Value error, ")
    return plantilla.format(msg=msg, **(err.get("ctx") or {}))


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorNegocio)
    async def _negocio(_: Request, exc: ErrorNegocio):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.mensaje})

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError):
        errores = []
        for e in exc.errors():
            campo = ".".join(str(p) for p in e["loc"] if p not in ("body", "query", "path"))
            errores.append({"campo": campo or "general", "mensaje": _mensaje_campo(e)})
        resumen = "; ".join(
            f"{x['campo']}: {x['mensaje']}" if x["campo"] != "general" else x["mensaje"] for x in errores
        )
        return JSONResponse(status_code=422, content={"detail": f"Datos inválidos - {resumen}", "errores": errores})

    @app.exception_handler(IntegrityError)
    async def _integridad(_: Request, exc: IntegrityError):
        diag = getattr(exc.orig, "diag", None)
        constraint = getattr(diag, "constraint_name", None) or ""
        sqlstate = getattr(exc.orig, "sqlstate", "")
        if constraint in MENSAJES_CONSTRAINT:
            msg = MENSAJES_CONSTRAINT[constraint]
        elif sqlstate == "23503":
            msg = "Operación rechazada: el registro está relacionado con otros datos (integridad referencial)"
        elif sqlstate == "23505":
            msg = "Ya existe un registro con esos datos"
        elif sqlstate == "23514":
            msg = f"Los datos no cumplen una restricción de la base de datos ({constraint})"
        else:
            msg = "Error de integridad de datos"
        log.warning("IntegrityError %s %s", sqlstate, constraint)
        return JSONResponse(status_code=409, content={"detail": msg})

    @app.exception_handler(OperationalError)
    async def _bd_caida(_: Request, exc: OperationalError):
        log.error("Base de datos no disponible: %s", exc)
        return JSONResponse(status_code=503, content={"detail": "La base de datos no está disponible"})

    @app.exception_handler(Exception)
    async def _general(_: Request, exc: Exception):
        log.exception("Error no controlado")
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})
