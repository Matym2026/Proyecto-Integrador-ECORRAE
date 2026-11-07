"""Dispositivos RAEE: registro, consulta, edición, eliminación y trazabilidad."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas as s
from ..crud import guardar, obtener
from ..database import get_db
from ..errors import ErrorNegocio
from ..storage import storage

router = APIRouter(prefix="/api/dispositivos", tags=["Dispositivos"])


def _siguiente_codigo(db: Session) -> str:
    anio = datetime.now().year
    prefijo = f"RAEE-{anio}-"
    ultimo = db.scalar(
        select(func.max(m.Dispositivo.codigo_trazabilidad)).where(
            m.Dispositivo.codigo_trazabilidad.like(f"{prefijo}%")
        )
    )
    n = int(ultimo.rsplit("-", 1)[1]) + 1 if ultimo else 1
    return f"{prefijo}{n:05d}"


@router.get("", response_model=list[s.DispositivoOut])
def listar(
    q: str | None = Query(None, description="Código, marca, modelo o serie"),
    estado: s.EstadoDispositivo | None = None,
    tipo: s.TipoDispositivo | None = None,
    centro_id: int | None = None,
    lote_id: int | None = None,
    sin_lote: bool = False,
    db: Session = Depends(get_db),
):
    stmt = select(m.Dispositivo).order_by(m.Dispositivo.id.desc())
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(
            m.Dispositivo.codigo_trazabilidad.ilike(patron), m.Dispositivo.marca.ilike(patron),
            m.Dispositivo.modelo.ilike(patron), m.Dispositivo.numero_serie.ilike(patron),
        ))
    if estado:
        stmt = stmt.where(m.Dispositivo.estado == estado)
    if tipo:
        stmt = stmt.where(m.Dispositivo.tipo == tipo)
    if centro_id:
        stmt = stmt.where(m.Dispositivo.centro_actual_id == centro_id)
    if lote_id:
        stmt = stmt.where(m.Dispositivo.lote_id == lote_id)
    if sin_lote:
        stmt = stmt.where(m.Dispositivo.lote_id.is_(None))
    return db.scalars(stmt).unique().all()


@router.get("/{id_}", response_model=s.DispositivoOut)
def consultar(id_: int, db: Session = Depends(get_db)):
    return obtener(db, m.Dispositivo, id_, "Dispositivo")


@router.post("", response_model=s.DispositivoOut, status_code=status.HTTP_201_CREATED)
def registrar(datos: s.DispositivoIn, db: Session = Depends(get_db)):
    """Registra un RAEE: genera su código de trazabilidad y crea el
    movimiento de INGRESO al centro de acopio en la misma transacción."""
    centro = obtener(db, m.Centro, datos.centro_actual_id, "Centro")
    if not centro.activo:
        raise ErrorNegocio("El centro seleccionado está inactivo")
    if datos.registrado_por:
        obtener(db, m.Usuario, datos.registrado_por, "Usuario")

    disp = m.Dispositivo(**datos.model_dump(), codigo_trazabilidad=_siguiente_codigo(db), estado="REGISTRADO")
    db.add(disp)
    db.flush()  # obtiene el id sin cerrar la transacción
    db.add(m.Movimiento(
        tipo="INGRESO", dispositivo_id=disp.id, centro_destino_id=centro.id,
        responsable_id=datos.registrado_por, observaciones="Ingreso inicial al centro de acopio",
    ))
    db.commit()
    db.refresh(disp)
    return disp


@router.put("/{id_}", response_model=s.DispositivoOut)
def actualizar(id_: int, datos: s.DispositivoUpdate, db: Session = Depends(get_db)):
    disp = obtener(db, m.Dispositivo, id_, "Dispositivo")
    if disp.estado == "EN_DESTINO":
        raise ErrorNegocio("No se puede editar un dispositivo que ya fue entregado a su destino final")
    for k, v in datos.model_dump().items():
        setattr(disp, k, v)
    return guardar(db, disp)


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_: int, db: Session = Depends(get_db)):
    disp = obtener(db, m.Dispositivo, id_, "Dispositivo")
    if disp.estado in ("EN_LOTE", "EN_DESTINO"):
        raise ErrorNegocio(
            "Solo se pueden eliminar dispositivos REGISTRADOS o EVALUADOS que no estén en un lote "
            "(los demás forman parte del historial de trazabilidad)", 409
        )
    claves = db.scalars(select(m.Evidencia.clave_objeto).where(m.Evidencia.dispositivo_id == id_)).all()
    db.delete(disp)  # evaluaciones, movimientos y evidencias se eliminan en cascada (FK)
    db.commit()
    for c in claves:
        storage.eliminar(c)


@router.get("/{id_}/trazabilidad", response_model=s.TrazabilidadOut)
def trazabilidad(id_: int, db: Session = Depends(get_db)):
    """Historial completo del dispositivo: desde su registro hasta su destino final."""
    disp = obtener(db, m.Dispositivo, id_, "Dispositivo")
    evals = db.scalars(
        select(m.Evaluacion).where(m.Evaluacion.dispositivo_id == id_).order_by(m.Evaluacion.fecha)
    ).all()
    condicion = m.Movimiento.dispositivo_id == id_
    if disp.lote_id:
        condicion = or_(condicion, m.Movimiento.lote_id == disp.lote_id)
    movs = db.scalars(select(m.Movimiento).where(condicion).order_by(m.Movimiento.fecha)).all()
    condicion_ev = m.Evidencia.dispositivo_id == id_
    if disp.lote_id:
        condicion_ev = or_(condicion_ev, m.Evidencia.lote_id == disp.lote_id)
    evid = db.scalars(select(m.Evidencia).where(condicion_ev).order_by(m.Evidencia.fecha)).all()

    linea: list[s.EventoTraza] = [s.EventoTraza(
        fecha=disp.fecha_registro, tipo="REGISTRO", titulo="Dispositivo registrado",
        detalle=f"{disp.tipo} {disp.marca} {disp.modelo or ''} · {disp.peso_kg} kg · origen: {disp.origen or 'N/D'}",
    )]
    for e in evals:
        linea.append(s.EventoTraza(
            fecha=e.fecha, tipo="EVALUACION", titulo=f"Evaluación técnica → {e.recomendacion}",
            detalle=f"Estado {e.estado_fisico}, {'funcional' if e.funcional else 'no funcional'}"
                    f"{', con componentes peligrosos' if e.contiene_peligrosos else ''}"
                    f"{', datos borrados' if e.datos_borrados else ''} · evaluador: {e.evaluador.nombre}",
        ))
    for mv in movs:
        sujeto = f" (lote {mv.lote.codigo})" if mv.lote_id else ""
        if mv.tipo == "INGRESO":
            titulo, det = "Ingreso a centro de acopio", mv.centro_destino.nombre if mv.centro_destino else None
        elif mv.tipo == "TRASLADO":
            titulo = f"Traslado{sujeto}"
            det = f"{mv.centro_origen.nombre} → {mv.centro_destino.nombre}"
        else:
            titulo = f"Entrega a destino final{sujeto}"
            det = f"{mv.destino.nombre} ({mv.destino.tipo})"
        if mv.guia_remision:
            det = f"{det} · guía {mv.guia_remision}"
        linea.append(s.EventoTraza(fecha=mv.fecha, tipo=mv.tipo, titulo=titulo, detalle=det))
    for ev in evid:
        linea.append(s.EventoTraza(
            fecha=ev.fecha, tipo="EVIDENCIA", titulo="Evidencia adjuntada",
            detalle=f"{ev.nombre_archivo}{' - ' + ev.descripcion if ev.descripcion else ''}",
        ))
    linea.sort(key=lambda x: x.fecha)
    return s.TrazabilidadOut(dispositivo=disp, evaluaciones=evals, movimientos=movs,
                             evidencias=evid, linea_tiempo=linea)
