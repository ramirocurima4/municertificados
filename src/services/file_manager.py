"""Gestión de carpetas locales por curso, copia de recursos y apertura en explorador."""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.config import DB_PATH, USER_COURSES_DIR, USER_TEMPLATES_DIR, ensure_app_directories
from src.services.validators import is_supported_asset, sanitize_filename


def _extract_year_month(event_date: str) -> str:
    """Extrae YYYY-MM desde una fecha textual o usa el mes actual como respaldo."""
    text = str(event_date or "").strip()
    iso_match = re.search(r"(\d{4})[-/](\d{1,2})", text)
    if iso_match:
        return f"{iso_match.group(1)}-{int(iso_match.group(2)):02d}"

    latam_match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", text)
    if latam_match:
        return f"{latam_match.group(3)}-{int(latam_match.group(2)):02d}"

    return datetime.now().strftime("%Y-%m")


def build_course_folder_name(event_date: str, title: str) -> str:
    """Genera el nombre de carpeta estándar: <YYYY-MM>_<Nombre_Curso>."""
    ym = _extract_year_month(event_date)
    safe_title = sanitize_filename(title, max_length=60)
    return f"{ym}_{safe_title}"


def ensure_course_directories(event_date: str, title: str) -> tuple[Path, Path]:
    """Crea la carpeta del curso y su subcarpeta Certificados_Individuales."""
    ensure_app_directories()
    folder_name = build_course_folder_name(event_date, title)
    course_dir = USER_COURSES_DIR / folder_name
    certs_dir = course_dir / "Certificados_Individuales"
    certs_dir.mkdir(parents=True, exist_ok=True)
    return course_dir, certs_dir


def import_asset_to_local_store(
    source_path: str | Path, category: str = "general"
) -> Path:
    """Valida y copia una plantilla, logo o firma a 01_Plantillas_y_Logos."""
    src = Path(source_path)
    if not src.is_file():
        raise FileNotFoundError(f"No se encontró el archivo: {src}")
    if not is_supported_asset(src):
        raise ValueError(
            f"Formato no soportado ({src.suffix}). Use .pdf, .png, .jpg, .jpeg o .webp."
        )

    ensure_app_directories()
    dest_dir = USER_TEMPLATES_DIR / sanitize_filename(category, max_length=30)
    dest_dir.mkdir(parents=True, exist_ok=True)

    stem = sanitize_filename(src.stem, max_length=50)
    ext = src.suffix.lower()
    dest = dest_dir / f"{stem}{ext}"

    if dest.exists() and dest.resolve() != src.resolve():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = dest_dir / f"{stem}_{stamp}{ext}"

    if dest.resolve() != src.resolve():
        shutil.copy2(src, dest)
    return dest


def open_folder_in_explorer(folder_path: str | Path) -> None:
    """Abre una carpeta en el explorador de archivos nativo del sistema operativo."""
    target = Path(folder_path)
    target.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        os.startfile(str(target))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])


def backup_database(dest_path: str | Path) -> Path:
    """Crea una copia de seguridad consistente de la base de datos SQLite."""
    target = Path(dest_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(DB_PATH)) as src_conn:
        with sqlite3.connect(str(target)) as dst_conn:
            src_conn.backup(dst_conn)
    return target
