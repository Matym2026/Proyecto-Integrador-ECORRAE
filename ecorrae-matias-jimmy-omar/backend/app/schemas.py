"""Esquemas Pydantic: validan los datos que llegan del frontend
y dan forma a las respuestas de la API."""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Rol = Literal["ADMIN", "OPERADOR", "EVALUADOR", "AUDITOR"]
TipoCentro = Literal["ACOPIO", "ALMACEN", "TRATAMIENTO"]
TipoDestino = Literal["REUTILIZACION", "RECICLAJE", "DISPOSICION_FINAL", "DONACION"]
TipoDispositivo = Literal[
    "COMPUTADOR", "PORTATIL", "MONITOR", "IMPRESORA", "CELULAR", "TABLET",
    "SERVIDOR", "EQUIPO_RED", "ELECTRODOMESTICO", "OTRO",
]
EstadoDispositivo = Literal["REGISTRADO", "EVALUADO", "EN_LOTE", "EN_DESTINO"]
EstadoLote = Literal["ABIERTO", "CERRADO", "ENTREGADO"]
EstadoFisico = Literal["BUENO", "REGULAR", "MALO"]
Recomendacion = Literal["REUTILIZACION", "RECICLAJE", "DISPOSICION_FINAL"]
TipoMovimiento = Literal["INGRESO", "TRASLADO", "ENTREGA_DESTINO"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _strip(v):
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


# ------------------------------- Usuarios -------------------------------
class UsuarioIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    email: EmailStr
    rol: Rol
    activo: bool = True

    _s = field_validator("nombre", mode="before")(_strip)


class UsuarioOut(ORM):
    id: int
    nombre: str
    email: str
    rol: str
    activo: bool
    creado_en: datetime


# -------------------------------- Centros --------------------------------
class CentroIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    tipo: TipoCentro
    ciudad: str = Field(min_length=2, max_length=80)
    direccion: str | None = Field(default=None, max_length=200)
    responsable: str | None = Field(default=None, max_length=120)
    telefono: str | None = Field(default=None, pattern=r"^\+?[0-9]{7,15}$")
    activo: bool = True

    _s = field_validator("nombre", "ciudad", "direccion", "responsable", "telefono", mode="before")(_strip)


class CentroOut(ORM):
    id: int
    nombre: str
    tipo: str
    ciudad: str
    direccion: str | None
    responsable: str | None
    telefono: str | None
    activo: bool


class CentroMini(ORM):
    id: int
    nombre: str
    ciudad: str


# -------------------------------- Destinos --------------------------------
class DestinoIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    tipo: TipoDestino
    ruc: str | None = Field(default=None, pattern=r"^[0-9]{13}$")
    licencia_ambiental: str | None = Field(default=None, max_length=60)
    ciudad: str = Field(min_length=2, max_length=80)
    contacto: str | None = Field(default=None, max_length=120)
    activo: bool = True

    _s = field_validator("nombre", "ruc", "licencia_ambiental", "ciudad", "contacto", mode="before")(_strip)


class DestinoOut(ORM):
    id: int
    nombre: str
    tipo: str
    ruc: str | None
    licencia_ambiental: str | None
    ciudad: str
    contacto: str | None
    activo: bool


class DestinoMini(ORM):
    id: int
    nombre: str
    tipo: str


# ------------------------------ Dispositivos ------------------------------
class DispositivoIn(BaseModel):
    tipo: TipoDispositivo
    marca: str = Field(min_length=2, max_length=60)
    modelo: str | None = Field(default=None, max_length=80)
    numero_serie: str | None = Field(default=None, max_length=80)
    peso_kg: Decimal = Field(gt=0, le=2000, decimal_places=2)
    centro_actual_id: int = Field(gt=0)
    registrado_por: int | None = None
    origen: str | None = Field(default=None, max_length=150)
    observaciones: str | None = None

    _s = field_validator("marca", "modelo", "numero_serie", "origen", "observaciones", mode="before")(_strip)


class DispositivoUpdate(BaseModel):
    """Campos editables. El estado, centro y lote cambian solo por procesos
    (evaluación, asignación a lote, movimientos) para no romper la trazabilidad."""
    tipo: TipoDispositivo
    marca: str = Field(min_length=2, max_length=60)
    modelo: str | None = Field(default=None, max_length=80)
    numero_serie: str | None = Field(default=None, max_length=80)
    peso_kg: Decimal = Field(gt=0, le=2000, decimal_places=2)
    origen: str | None = Field(default=None, max_length=150)
    observaciones: str | None = None

    _s = field_validator("marca", "modelo", "numero_serie", "origen", "observaciones", mode="before")(_strip)


class LoteMini(ORM):
    id: int
    codigo: str
    estado: str


class DispositivoOut(ORM):
    id: int
    codigo_trazabilidad: str
    tipo: str
    marca: str
    modelo: str | None
    numero_serie: str | None
    peso_kg: Decimal
    estado: str
    centro_actual_id: int
    centro_actual: CentroMini
    lote_id: int | None
    lote: LoteMini | None
    registrado_por: int | None
    origen: str | None
    observaciones: str | None
    fecha_registro: datetime


class DispositivoMini(ORM):
    id: int
    codigo_trazabilidad: str
    tipo: str
    marca: str


# --------------------------------- Lotes ---------------------------------
class LoteIn(BaseModel):
    codigo: str | None = Field(default=None, pattern=r"^LOTE-[0-9]{4}-[0-9]{3,}$")
    descripcion: str | None = Field(default=None, max_length=255)
    centro_id: int = Field(gt=0)
    creado_por: int | None = None

    _s = field_validator("codigo", "descripcion", mode="before")(_strip)


class LoteUpdate(BaseModel):
    descripcion: str | None = Field(default=None, max_length=255)
    _s = field_validator("descripcion", mode="before")(_strip)


class LoteOut(ORM):
    id: int
    codigo: str
    descripcion: str | None
    centro_id: int
    centro: CentroMini
    destino_id: int | None
    destino: DestinoMini | None
    estado: str
    creado_por: int | None
    fecha_creacion: datetime
    fecha_cierre: datetime | None
    total_dispositivos: int = 0
    peso_total_kg: Decimal = Decimal("0")


class AsignarDispositivos(BaseModel):
    dispositivo_ids: list[int] = Field(min_length=1)


# ------------------------------ Evaluaciones ------------------------------
class EvaluacionIn(BaseModel):
    dispositivo_id: int = Field(gt=0)
    evaluador_id: int = Field(gt=0)
    estado_fisico: EstadoFisico
    funcional: bool
    contiene_peligrosos: bool = False
    datos_borrados: bool = False
    recomendacion: Recomendacion
    observaciones: str | None = None

    _s = field_validator("observaciones", mode="before")(_strip)

    @model_validator(mode="after")
    def reglas(self):
        if self.recomendacion == "REUTILIZACION" and not (self.funcional and self.datos_borrados):
            raise ValueError("Para recomendar REUTILIZACION el equipo debe ser funcional y tener los datos borrados")
        if self.contiene_peligrosos and self.recomendacion == "REUTILIZACION":
            raise ValueError("Un equipo con componentes peligrosos no puede recomendarse para REUTILIZACION")
        return self


class UsuarioMini(ORM):
    id: int
    nombre: str


class EvaluacionOut(ORM):
    id: int
    dispositivo_id: int
    dispositivo: DispositivoMini
    evaluador_id: int
    evaluador: UsuarioMini
    fecha: datetime
    estado_fisico: str
    funcional: bool
    contiene_peligrosos: bool
    datos_borrados: bool
    recomendacion: str
    observaciones: str | None


# ------------------------------- Movimientos -------------------------------
class MovimientoIn(BaseModel):
    """Registrar un traslado entre centros o la entrega final a un destino.
    Se aplica a un dispositivo suelto o a un lote completo."""
    tipo: Literal["TRASLADO", "ENTREGA_DESTINO"]
    dispositivo_id: int | None = None
    lote_id: int | None = None
    centro_destino_id: int | None = None
    destino_id: int | None = None
    responsable_id: int | None = None
    guia_remision: str | None = Field(default=None, max_length=40)
    observaciones: str | None = None

    _s = field_validator("guia_remision", "observaciones", mode="before")(_strip)

    @model_validator(mode="after")
    def reglas(self):
        if bool(self.dispositivo_id) == bool(self.lote_id):
            raise ValueError("Indique un dispositivo o un lote (solo uno de los dos)")
        if self.tipo == "TRASLADO" and not self.centro_destino_id:
            raise ValueError("El traslado requiere el centro de destino")
        if self.tipo == "ENTREGA_DESTINO" and not self.destino_id:
            raise ValueError("La entrega requiere el destino final (gestor)")
        return self


class MovimientoOut(ORM):
    id: int
    tipo: str
    dispositivo_id: int | None
    dispositivo: DispositivoMini | None
    lote_id: int | None
    lote: LoteMini | None
    centro_origen: CentroMini | None
    centro_destino: CentroMini | None
    destino: DestinoMini | None
    responsable: UsuarioMini | None
    guia_remision: str | None
    fecha: datetime
    observaciones: str | None


# ------------------------------- Evidencias -------------------------------
class EvidenciaOut(ORM):
    id: int
    dispositivo_id: int | None
    lote_id: int | None
    nombre_archivo: str
    clave_objeto: str
    tipo_mime: str
    tamano_bytes: int
    descripcion: str | None
    subido_por: int | None
    fecha: datetime


# ------------------------------ Trazabilidad ------------------------------
class EventoTraza(BaseModel):
    fecha: datetime
    tipo: str
    titulo: str
    detalle: str | None = None


class TrazabilidadOut(BaseModel):
    dispositivo: DispositivoOut
    evaluaciones: list[EvaluacionOut]
    movimientos: list[MovimientoOut]
    evidencias: list[EvidenciaOut]
    linea_tiempo: list[EventoTraza]
