"""Almacenamiento de evidencias.

En local los archivos se guardan en STORAGE_DIR con la misma estructura de
claves que tendrá el bucket S3 (p. ej. dispositivos/5/<uuid>_foto.jpg).
Para la migración a AWS basta con implementar S3Storage con boto3
(put_object / get_object / delete_object) y cambiar la instancia `storage`.
"""
import re
import uuid
from pathlib import Path

from .config import STORAGE_DIR


class LocalStorage:
    def __init__(self, raiz: Path):
        self.raiz = raiz
        self.raiz.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generar_clave(prefijo: str, nombre_original: str) -> str:
        limpio = re.sub(r"[^A-Za-z0-9._-]", "_", Path(nombre_original).name)[-120:]
        return f"{prefijo}/{uuid.uuid4().hex}_{limpio}"

    def _ruta(self, clave: str) -> Path:
        ruta = (self.raiz / clave).resolve()
        if self.raiz.resolve() not in ruta.parents:
            raise ValueError("Clave de objeto inválida")
        return ruta

    def guardar(self, clave: str, contenido: bytes) -> None:
        ruta = self._ruta(clave)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(contenido)

    def ruta_lectura(self, clave: str) -> Path:
        return self._ruta(clave)

    def eliminar(self, clave: str) -> None:
        self._ruta(clave).unlink(missing_ok=True)


storage = LocalStorage(STORAGE_DIR)
