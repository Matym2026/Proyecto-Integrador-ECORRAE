import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://ecoraee:ecoraee123@localhost:5432/ecoraee"
)
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage"))
if not STORAGE_DIR.is_absolute():
    STORAGE_DIR = (BASE_DIR / STORAGE_DIR).resolve()
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
