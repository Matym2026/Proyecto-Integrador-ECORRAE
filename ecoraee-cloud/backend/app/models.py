"""Modelos ORM. Reflejan exactamente las tablas de database/01_schema.sql."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    rol: Mapped[str] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Centro(Base):
    __tablename__ = "centros"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    tipo: Mapped[str] = mapped_column(String(20))
    ciudad: Mapped[str] = mapped_column(String(80))
    direccion: Mapped[str | None] = mapped_column(String(200))
    responsable: Mapped[str | None] = mapped_column(String(120))
    telefono: Mapped[str | None] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Destino(Base):
    __tablename__ = "destinos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    tipo: Mapped[str] = mapped_column(String(20))
    ruc: Mapped[str | None] = mapped_column(String(13))
    licencia_ambiental: Mapped[str | None] = mapped_column(String(60))
    ciudad: Mapped[str] = mapped_column(String(80))
    contacto: Mapped[str | None] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Lote(Base):
    __tablename__ = "lotes"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    centro_id: Mapped[int] = mapped_column(ForeignKey("centros.id"))
    destino_id: Mapped[int | None] = mapped_column(ForeignKey("destinos.id"))
    estado: Mapped[str] = mapped_column(String(20), default="ABIERTO")
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime)

    centro: Mapped[Centro] = relationship(lazy="joined")
    destino: Mapped[Destino | None] = relationship(lazy="joined")
    dispositivos: Mapped[list["Dispositivo"]] = relationship(
        back_populates="lote", passive_deletes=True
    )


class Dispositivo(Base):
    __tablename__ = "dispositivos"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_trazabilidad: Mapped[str] = mapped_column(String(30), unique=True)
    tipo: Mapped[str] = mapped_column(String(30))
    marca: Mapped[str] = mapped_column(String(60))
    modelo: Mapped[str | None] = mapped_column(String(80))
    numero_serie: Mapped[str | None] = mapped_column(String(80), unique=True)
    peso_kg: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    estado: Mapped[str] = mapped_column(String(20), default="REGISTRADO")
    centro_actual_id: Mapped[int] = mapped_column(ForeignKey("centros.id"))
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes.id", ondelete="SET NULL"))
    registrado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    origen: Mapped[str | None] = mapped_column(String(150))
    observaciones: Mapped[str | None] = mapped_column(Text)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    centro_actual: Mapped[Centro] = relationship(lazy="joined")
    lote: Mapped[Lote | None] = relationship(back_populates="dispositivos")


class Evaluacion(Base):
    __tablename__ = "evaluaciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    dispositivo_id: Mapped[int] = mapped_column(ForeignKey("dispositivos.id", ondelete="CASCADE"))
    evaluador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    estado_fisico: Mapped[str] = mapped_column(String(10))
    funcional: Mapped[bool] = mapped_column(Boolean)
    contiene_peligrosos: Mapped[bool] = mapped_column(Boolean, default=False)
    datos_borrados: Mapped[bool] = mapped_column(Boolean, default=False)
    recomendacion: Mapped[str] = mapped_column(String(20))
    observaciones: Mapped[str | None] = mapped_column(Text)

    dispositivo: Mapped[Dispositivo] = relationship(lazy="joined")
    evaluador: Mapped[Usuario] = relationship(lazy="joined")


class Movimiento(Base):
    __tablename__ = "movimientos"
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20))
    dispositivo_id: Mapped[int | None] = mapped_column(ForeignKey("dispositivos.id", ondelete="CASCADE"))
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes.id", ondelete="CASCADE"))
    centro_origen_id: Mapped[int | None] = mapped_column(ForeignKey("centros.id"))
    centro_destino_id: Mapped[int | None] = mapped_column(ForeignKey("centros.id"))
    destino_id: Mapped[int | None] = mapped_column(ForeignKey("destinos.id"))
    responsable_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    guia_remision: Mapped[str | None] = mapped_column(String(40))
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    observaciones: Mapped[str | None] = mapped_column(Text)

    dispositivo: Mapped[Dispositivo | None] = relationship(lazy="joined")
    lote: Mapped[Lote | None] = relationship(lazy="joined")
    centro_origen: Mapped[Centro | None] = relationship(foreign_keys=[centro_origen_id], lazy="joined")
    centro_destino: Mapped[Centro | None] = relationship(foreign_keys=[centro_destino_id], lazy="joined")
    destino: Mapped[Destino | None] = relationship(lazy="joined")
    responsable: Mapped[Usuario | None] = relationship(lazy="joined")


class Evidencia(Base):
    __tablename__ = "evidencias"
    id: Mapped[int] = mapped_column(primary_key=True)
    dispositivo_id: Mapped[int | None] = mapped_column(ForeignKey("dispositivos.id", ondelete="CASCADE"))
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes.id", ondelete="CASCADE"))
    nombre_archivo: Mapped[str] = mapped_column(String(255))
    clave_objeto: Mapped[str] = mapped_column(String(400), unique=True)
    tipo_mime: Mapped[str] = mapped_column(String(100))
    tamano_bytes: Mapped[int] = mapped_column(Integer)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    subido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
