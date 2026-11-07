"""Evidencias (fotos, actas, certificados) asociadas a dispositivos o lotes.
El archivo va al almacenamiento de objetos; la BD guarda solo los metadatos."""
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas as s
from ..config import MAX_UPLOAD_MB
from ..crud import obtener
from ..database import get_db
from ..errors import ErrorNegocio
from ..storage import storage

router = APIRouter(prefix="/api/evidencias", tags=["Evidencias"])

TIPOS_PERMITIDOS = {
    "image/jpeg", "image/png", "image/webp", "application/pdf",
}


@router.get("", response_model=list[s.EvidenciaOut])
def listar(dispositivo_id: int | None = None, lote_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(m.Evidencia).order_by(m.Evidencia.fecha.desc())
    if dispositivo_id:
        stmt = stmt.where(m.Evidencia.dispositivo_id == dispositivo_id)
    if lote_id:
        stmt = stmt.where(m.Evidencia.lote_id == lote_id)
    return db.scalars(stmt).all()


@router.post("", response_model=s.EvidenciaOut, status_code=status.HTTP_201_CREATED)
async def subir(
    archivo: UploadFile = File(...),
    dispositivo_id: int | None = Form(None),
    lote_id: int | None = Form(None),
    descripcion: str | None = Form(None),
    subido_por: int | None = Form(None),
    db: Session = Depends(get_db),
):
    if bool(dispositivo_id) == bool(lote_id):
        raise ErrorNegocio("La evidencia debe asociarse a un dispositivo o a un lote (solo uno)")
    if archivo.content_type not in TIPOS_PERMITIDOS:
        raise ErrorNegocio("Tipo de archivo no permitido. Use JPG, PNG, WEBP o PDF", 415)
    contenido = await archivo.read()
    if not contenido:
        raise ErrorNegocio("El archivo está vacío")
    if len(contenido) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ErrorNegocio(f"El archivo supera el máximo de {MAX_UPLOAD_MB} MB", 413)

    if dispositivo_id:
        obtener(db, m.Dispositivo, dispositivo_id, "Dispositivo")
        prefijo = f"dispositivos/{dispositivo_id}"
    else:
        obtener(db, m.Lote, lote_id, "Lote")
        prefijo = f"lotes/{lote_id}"

    clave = storage.generar_clave(prefijo, archivo.filename or "archivo")
    storage.guardar(clave, contenido)
    ev = m.Evidencia(
        dispositivo_id=dispositivo_id, lote_id=lote_id, nombre_archivo=archivo.filename or "archivo",
        clave_objeto=clave, tipo_mime=archivo.content_type, tamano_bytes=len(contenido),
        descripcion=(descripcion or "").strip()[:255] or None, subido_por=subido_por,
    )
    try:
        db.add(ev)
        db.commit()
    except Exception:
        storage.eliminar(clave)  # no dejar archivos huérfanos si falla la BD
        raise
    db.refresh(ev)
    return ev


@router.get("/{id_}/archivo")
def descargar(id_: int, db: Session = Depends(get_db)):
    ev = obtener(db, m.Evidencia, id_, "Evidencia")
    ruta = storage.ruta_lectura(ev.clave_objeto)
    if not ruta.exists():
        raise ErrorNegocio("El archivo no se encuentra en el almacenamiento", 404)
    return FileResponse(ruta, media_type=ev.tipo_mime, filename=ev.nombre_archivo,
                        content_disposition_type="inline")


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_: int, db: Session = Depends(get_db)):
    ev = obtener(db, m.Evidencia, id_, "Evidencia")
    clave = ev.clave_objeto
    db.delete(ev)
    db.commit()
    storage.eliminar(clave)
