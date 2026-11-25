"""Configuración central de rutas, constantes y directorios de MuniCertificados."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "MuniCertificados"
APP_SUBTITLE = "Municipalidad de San Roque — Área de Redes"
APP_VERSION = "1.0.0"

# Dimensiones A4 Apaisado (297mm x 210mm) a 300 DPI y en puntos PDF (72 pt/inch)
DEFAULT_DPI = 300
A4_LANDSCAPE_WIDTH_PX = 3508
A4_LANDSCAPE_HEIGHT_PX = 2480
A4_LANDSCAPE_WIDTH_PT = 841.89
A4_LANDSCAPE_HEIGHT_PT = 595.28

# Formatos aceptados para plantillas base, logos y firmas
SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
SUPPORTED_PDF_EXTENSIONS = (".pdf",)
SUPPORTED_ASSET_EXTENSIONS = SUPPORTED_PDF_EXTENSIONS + SUPPORTED_IMAGE_EXTENSIONS

FILEDIALOG_ASSET_TYPES = [
    ("Todos los formatos soportados", "*.pdf *.png *.jpg *.jpeg *.webp"),
    ("Documentos PDF", "*.pdf"),
    ("Imágenes (PNG, JPG, WEBP)", "*.png *.jpg *.jpeg *.webp"),
]


def get_resource_path(relative_path: str | Path) -> Path:
    """Resuelve rutas de recursos empaquetados (PyInstaller sys._MEIPASS) o locales."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path


ASSETS_DIR = get_resource_path("assets")
FONTS_DIR = ASSETS_DIR / "fonts"
PRESET_TEMPLATES_DIR = ASSETS_DIR / "templates"
ASSETS_LOGOS_DIR = ASSETS_DIR / "logos"


def get_user_documents_dir() -> Path:
    """Obtiene la carpeta Documentos del usuario de forma multiplataforma."""
    if os.name == "nt":
        try:
            import winreg  # type: ignore

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
            )
            docs, _ = winreg.QueryValueEx(key, "Personal")
            if docs:
                return Path(docs)
        except OSError:
            pass

    for candidate in (Path.home() / "Documents", Path.home() / "Documentos"):
        if candidate.exists():
            return candidate
    return Path.home() / "Documents"


APP_DATA_DIR = get_user_documents_dir() / "Muni_Certificados"
USER_TEMPLATES_DIR = APP_DATA_DIR / "01_Plantillas_y_Logos"
USER_COURSES_DIR = APP_DATA_DIR / "02_Cursos_y_Jornadas"
DB_DIR = APP_DATA_DIR / "Base_Datos"
DB_PATH = DB_DIR / "muni_certificados.db"


def ensure_app_directories() -> None:
    """Crea la estructura local de carpetas en Documentos si aún no existe."""
    for directory in (APP_DATA_DIR, USER_TEMPLATES_DIR, USER_COURSES_DIR, DB_DIR):
        directory.mkdir(parents=True, exist_ok=True)
