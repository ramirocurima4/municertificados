"""Validadores, limpieza de DNI, normalización de nombres y sanitización de rutas."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from src.config import SUPPORTED_ASSET_EXTENSIONS

_LOWERCASE_PARTICLES = {"de", "del", "la", "las", "los", "y", "e", "san"}
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def clean_dni(raw_dni: str | int) -> str:
    """Extrae únicamente los dígitos de un DNI."""
    return re.sub(r"\D", "", str(raw_dni or ""))


def is_valid_dni(raw_dni: str | int) -> bool:
    """Valida que el DNI limpio tenga entre 6 y 9 dígitos numéricos."""
    digits = clean_dni(raw_dni)
    return 6 <= len(digits) <= 9


def format_dni_display(raw_dni: str | int) -> str:
    """Formatea un DNI con separadores de miles por puntos (ej. 35.123.456)."""
    digits = clean_dni(raw_dni)
    if not digits:
        return ""
    return f"{int(digits):,}".replace(",", ".")


def normalize_text(raw_text: str) -> str:
    """Elimina espacios redundantes y saltos de línea."""
    return " ".join(str(raw_text or "").strip().split())


def normalize_name(raw_name: str) -> str:
    """Normaliza nombres y apellidos en Formato Título respetando partículas."""
    cleaned = normalize_text(raw_name)
    if not cleaned:
        return ""
    words = cleaned.lower().split(" ")
    normalized: list[str] = []
    for idx, word in enumerate(words):
        if idx > 0 and word in _LOWERCASE_PARTICLES:
            normalized.append(word)
        else:
            normalized.append("-".join(part.capitalize() for part in word.split("-")))
    return " ".join(normalized)


def sanitize_filename(text: str, max_length: int = 80) -> str:
    """Convierte un texto en un segmento seguro para nombres de archivo y carpetas."""
    normalized = unicodedata.normalize("NFKD", normalize_text(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", ascii_text)
    safe = re.sub(r"_+", "_", safe).strip("_-")
    if max_length > 0:
        safe = safe[:max_length].rstrip("_-")
    return safe or "sin_nombre"


def build_certificate_filename(dni: str, full_name: str) -> str:
    """Genera el nombre estándar de certificado individual: DNI_Nombre_Normalizado.pdf."""
    safe_dni = clean_dni(dni) or "00000000"
    safe_name = sanitize_filename(normalize_name(full_name), max_length=60)
    return f"{safe_dni}_{safe_name}.pdf"


def is_valid_email(email: str) -> bool:
    """Valida formato básico de correo electrónico (vacío se considera válido/opcional)."""
    cleaned = normalize_text(email)
    if not cleaned:
        return True
    return bool(_EMAIL_RE.match(cleaned))


def is_supported_asset(file_path: str | Path) -> bool:
    """Verifica que el archivo tenga extensión soportada (.pdf, .png, .jpg, .jpeg, .webp)."""
    return Path(file_path).suffix.lower() in SUPPORTED_ASSET_EXTENSIONS


_DNI_TOKEN_RE = re.compile(r"\b(?:\d{1,3}(?:\.\d{3}){2}|\d{6,9})\b")
_LEADING_INDEX_RE = re.compile(r"^\s*(?:[-•*]+|\d{1,4}\s*[.)º°:\-|]+)\s*")
_DNI_LABEL_RE = re.compile(
    r"\b(?:d\.?n\.?i\.?|documento|doc\.?|nro\.?|n[°º])\b[:\s#\-]*",
    re.IGNORECASE,
)


def parse_whatsapp_list(raw_text: str) -> list[dict[str, str]]:
    """Extrae pares de {'dni', 'full_name'} desde listas o tablas pegadas de WhatsApp."""
    results: list[dict[str, str]] = []
    for raw_line in str(raw_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        dni_match = _DNI_TOKEN_RE.search(line)
        if not dni_match:
            continue

        dni = clean_dni(dni_match.group(0))
        if not is_valid_dni(dni):
            continue

        without_dni = (line[: dni_match.start()] + " " + line[dni_match.end() :]).strip()

        if "|" in without_dni:
            parts = [p.strip(" *_~`\t") for p in without_dni.split("|")]
            name_parts = [
                p
                for p in parts
                if p
                and not re.match(r"^\d{1,4}[.)º°]?$", p)
                and not re.match(r"^(?:n\.?[º°o]?|dni|documento)$", p, re.IGNORECASE)
            ]
            candidate_name = " ".join(name_parts)
        else:
            candidate_name = _LEADING_INDEX_RE.sub("", without_dni)

        candidate_name = _DNI_LABEL_RE.sub(" ", candidate_name)
        candidate_name = candidate_name.replace(",", " ")
        candidate_name = re.sub(r"[|()*_~`•\-:;]+", " ", candidate_name)
        full_name = normalize_name(candidate_name)

        if len(full_name) < 2 or not any(ch.isalpha() for ch in full_name):
            continue
        if full_name.lower() in ("apellido y nombre", "nombre y apellido", "nombre completo"):
            continue

        results.append({"dni": dni, "full_name": full_name})

    return results
