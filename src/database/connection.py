"""Conexión SQLite, creación de tablas y carga inicial de plantillas institucionales."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from src.config import ASSETS_LOGOS_DIR, DB_PATH, PRESET_TEMPLATES_DIR, ensure_app_directories

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    is_preset INTEGER NOT NULL DEFAULT 0,
    bg_path TEXT NOT NULL DEFAULT '',
    logo_main_path TEXT NOT NULL DEFAULT '',
    logo_sec_path TEXT NOT NULL DEFAULT '',
    config_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'Curso',
    event_date TEXT NOT NULL,
    hours TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT 'San Roque, Corrientes',
    template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL,
    folder_path TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS people (
    dni TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    institution_or_role TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS attendees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    dni TEXT NOT NULL REFERENCES people(dni) ON DELETE CASCADE,
    attended INTEGER NOT NULL DEFAULT 1,
    cert_generated INTEGER NOT NULL DEFAULT 0,
    cert_file_path TEXT NOT NULL DEFAULT '',
    generated_at TEXT NOT NULL DEFAULT '',
    UNIQUE(course_id, dni)
);

CREATE INDEX IF NOT EXISTS idx_attendees_course ON attendees(course_id);
CREATE INDEX IF NOT EXISTS idx_people_name ON people(full_name);
"""


def default_template_config(
    *,
    accent_color: str = "#1B365D",
    secondary_color: str = "#B8860B",
    name_color: str = "#0F2442",
    body_color: str = "#2B3440",
    title_font: str = "NotoSerif-Bold.ttf",
    name_font: str = "NotoSerif-Bold.ttf",
    body_font: str = "NotoSans-Regular.ttf",
    show_dni: bool = True,
) -> dict:
    """Genera la configuración clásica centrada."""
    return {
        "show_dni": show_dni,
        "header_institution": {
            "text": "MUNICIPALIDAD DE SAN ROQUE — CORRIENTES",
            "x": 1754,
            "y": 360,
            "font": body_font,
            "size": 34,
            "color": secondary_color,
            "align": "center",
        },
        "header_area": {
            "text": "ÁREA DE REDES Y MODERNIZACIÓN",
            "x": 1754,
            "y": 445,
            "font": body_font,
            "size": 26,
            "color": body_color,
            "align": "center",
        },
        "course_banner": {
            "enabled": False,
            "text": "{CURSO}",
            "x": 1754,
            "y": 520,
            "font": "Poppins-Bold.ttf",
            "size": 44,
            "color": "#FFFFFF",
            "align": "center",
            "pill_enabled": False,
            "pill_color": accent_color,
            "pill_radius": 4,
        },
        "title": {
            "text": "CERTIFICADO",
            "x": 1754,
            "y": 635,
            "font": title_font,
            "size": 118,
            "color": accent_color,
            "align": "center",
        },
        "subtitle": {
            "text": "Se otorga el presente reconocimiento a:",
            "x": 1754,
            "y": 890,
            "font": "NotoSerif-Italic.ttf",
            "size": 42,
            "color": body_color,
            "align": "center",
        },
        "recipient_name": {
            "x": 1754,
            "y": 1105,
            "font": name_font,
            "size": 92,
            "min_size": 44,
            "max_width_ratio": 0.78,
            "color": name_color,
            "align": "center",
            "underline": False,
            "underline_color": secondary_color,
        },
        "recipient_dni": {
            "text": "D.N.I. N° {dni}",
            "x": 1754,
            "y": 1300,
            "font": "NotoSans-Bold.ttf",
            "size": 34,
            "color": secondary_color,
            "align": "center",
        },
        "body": {
            "text": (
                "Por haber participado y completado satisfactoriamente el {tipo_evento} "
                "«{curso}», realizado en {lugar} el {fecha}, con una carga horaria de {carga_horaria}."
            ),
            "x": 1754,
            "y": 1525,
            "font": body_font,
            "size": 36,
            "max_width_ratio": 0.76,
            "line_spacing": 1.38,
            "color": body_color,
            "align": "center",
        },
        "footer_date": {
            "text": "{lugar}, {fecha}",
            "x": 1754,
            "y": 1820,
            "font": "NotoSerif-Italic.ttf",
            "size": 30,
            "color": body_color,
            "align": "center",
        },
        "logos": {
            "main": {
                "image_path": "",
                "x": 490,
                "y": 360,
                "max_width": 260,
                "max_height": 200,
                "remove_white_bg": False,
                "white_threshold": 240,
                "tint_enabled": False,
                "tint_color": accent_color,
            },
            "secondary": {
                "image_path": "",
                "x": 3015,
                "y": 360,
                "max_width": 260,
                "max_height": 200,
                "remove_white_bg": False,
                "white_threshold": 240,
                "tint_enabled": False,
                "tint_color": accent_color,
            },
            "logo_3": {
                "image_path": "",
                "x": 2700,
                "y": 2110,
                "max_width": 240,
                "max_height": 190,
                "remove_white_bg": False,
                "white_threshold": 240,
                "tint_enabled": False,
                "tint_color": accent_color,
            },
            "logo_4": {
                "image_path": "",
                "x": 3060,
                "y": 2110,
                "max_width": 240,
                "max_height": 190,
                "remove_white_bg": False,
                "white_threshold": 240,
                "tint_enabled": False,
                "tint_color": accent_color,
            },
        },
        "signatures": [
            {
                "enabled": True,
                "name": "Intendente Municipal",
                "role": "Municipalidad de San Roque",
                "image_path": "",
                "x": 1050,
                "y": 2095,
                "align": "center",
                "max_width": 360,
                "max_height": 130,
                "remove_white_bg": True,
                "white_threshold": 235,
            },
            {
                "enabled": True,
                "name": "Responsable Área de Redes",
                "role": "Coordinación Técnica",
                "image_path": "",
                "x": 2455,
                "y": 2095,
                "align": "center",
                "max_width": 360,
                "max_height": 130,
                "remove_white_bg": True,
                "white_threshold": 235,
            },
        ],
    }


def muni_mosaic_template_config(
    *,
    accent_color: str = "#3E6B24",
    pill_color: str = "#76B02A",
    secondary_color: str = "#4D7C2B",
    name_color: str = "#111827",
    body_color: str = "#1E293B",
    signer_role_title: str = "Dirección / Coordinación",
    show_dni: bool = True,
) -> dict:
    """Configuración idéntica al certificado oficial de Mosaico de la Municipalidad de San Roque."""
    return {
        "show_dni": show_dni,
        "header_institution": {
            "text": "{lugar} {fecha}",
            "x": 320,
            "y": 265,
            "font": "Poppins-Regular.ttf",
            "size": 34,
            "color": accent_color,
            "align": "left",
        },
        "header_area": {
            "text": "{TIPO_EVENTO}",
            "x": 320,
            "y": 505,
            "font": "Poppins-Bold.ttf",
            "size": 52,
            "color": "#111827",
            "align": "left",
        },
        "course_banner": {
            "enabled": True,
            "text": "{CURSO}",
            "x": 320,
            "y": 625,
            "font": "Poppins-Bold.ttf",
            "size": 62,
            "color": "#FFFFFF",
            "align": "left",
            "pill_enabled": True,
            "pill_color": pill_color,
            "pill_radius": 4,
            "pill_padding_x": 20,
            "pill_padding_y": 12,
        },
        "title": {
            "text": "CERTIFICADO DE RECONOCIMIENTO",
            "x": 320,
            "y": 925,
            "font": "Poppins-Bold.ttf",
            "size": 64,
            "color": accent_color,
            "align": "left",
        },
        "subtitle": {
            "text": "SE OTORGA EL PRESENTE CERTIFICADO A:",
            "x": 320,
            "y": 1020,
            "font": "Poppins-Bold.ttf",
            "size": 30,
            "color": "#1E293B",
            "align": "left",
        },
        "recipient_name": {
            "x": 320,
            "y": 1200,
            "font": "Poppins-Bold.ttf",
            "size": 84,
            "min_size": 44,
            "max_width_ratio": 0.68,
            "color": name_color,
            "align": "left",
            "underline": False,
            "underline_color": pill_color,
        },
        "recipient_dni": {
            "text": "D.N.I. N° {dni}",
            "x": 320,
            "y": 1295,
            "font": "Poppins-Regular.ttf",
            "size": 28,
            "color": secondary_color,
            "align": "left",
        },
        "body": {
            "text": (
                "EN RECONOCIMIENTO A SU PARTICIPACIÓN EN\n"
                "**{CURSO}.**"
            ),
            "x": 320,
            "y": 1420,
            "font": "Poppins-Regular.ttf",
            "bold_font": "Poppins-Bold.ttf",
            "size": 44,
            "max_width_ratio": 0.68,
            "line_spacing": 1.38,
            "color": body_color,
            "align": "left",
        },
        "footer_date": {
            "text": "",
            "x": 320,
            "y": 1650,
            "font": "Poppins-Regular.ttf",
            "size": 26,
            "color": accent_color,
            "align": "left",
        },
        "logos": {
            "main": {
                "image_path": str(ASSETS_LOGOS_DIR / "logo_avanzamos_juntos.png"),
                "x": 1660,
                "y": 2110,
                "max_width": 290,
                "max_height": 210,
                "remove_white_bg": False,
                "white_threshold": 240,
                "tint_enabled": False,
                "tint_color": accent_color,
            },
            "secondary": {
                "image_path": str(ASSETS_LOGOS_DIR / "logo_san_roque_escudo.png"),
                "x": 2140,
                "y": 2110,
                "max_width": 230,
                "max_height": 220,
                "remove_white_bg": False,
                "white_threshold": 240,
                "tint_enabled": False,
                "tint_color": accent_color,
            },
            "logo_3": {
                "image_path": "",
                "x": 2620,
                "y": 2110,
                "max_width": 290,
                "max_height": 210,
                "remove_white_bg": False,
                "white_threshold": 240,
                "tint_enabled": False,
                "tint_color": accent_color,
            },
            "logo_4": {
                "image_path": "",
                "x": 3080,
                "y": 2110,
                "max_width": 270,
                "max_height": 220,
                "remove_white_bg": False,
                "white_threshold": 240,
                "tint_enabled": False,
                "tint_color": accent_color,
            },
        },
        "signatures": [
            {
                "enabled": True,
                "name": signer_role_title,
                "role": "Municipalidad de San Roque",
                "image_path": "",
                "x": 520,
                "y": 2075,
                "align": "left",
                "max_width": 360,
                "max_height": 130,
                "remove_white_bg": True,
                "white_threshold": 235,
            },
            {
                "enabled": False,
                "name": "Intendente Municipal",
                "role": "Municipalidad de San Roque",
                "image_path": "",
                "x": 1060,
                "y": 2075,
                "align": "left",
                "max_width": 360,
                "max_height": 130,
                "remove_white_bg": True,
                "white_threshold": 235,
            },
        ],
    }


PRESET_DEFINITIONS = [
    {
        "name": "Muni San Roque — Agro, Cultivos y Producción",
        "bg_filename": "plantilla_agro_cultivos.png",
        "config": muni_mosaic_template_config(
            accent_color="#3E6B24",
            pill_color="#76B02A",
            secondary_color="#4D7C2B",
            signer_role_title="Dirección de Producción",
        ),
    },
    {
        "name": "Muni San Roque — Docentes y Educación",
        "bg_filename": "plantilla_educacion_docente.png",
        "config": muni_mosaic_template_config(
            accent_color="#1B4965",
            pill_color="#2B9EB3",
            secondary_color="#1E6091",
            signer_role_title="Dirección de Educación",
        ),
    },
    {
        "name": "Muni San Roque — Guías Turísticos y Turismo",
        "bg_filename": "plantilla_turismo_guias.png",
        "config": muni_mosaic_template_config(
            accent_color="#0F5C6E",
            pill_color="#148F77",
            secondary_color="#116A7B",
            signer_role_title="Dirección de Turismo",
        ),
    },
    {
        "name": "Muni San Roque — Inteligencia Artificial, Redes e IT",
        "bg_filename": "plantilla_tecnologia_redes.png",
        "config": muni_mosaic_template_config(
            accent_color="#1E3A8A",
            pill_color="#0284C7",
            secondary_color="#2563EB",
            signer_role_title="Área de Redes y Modernización",
        ),
    },
    {
        "name": "Muni San Roque — Deportes y Recreación",
        "bg_filename": "plantilla_deportes_recreacion.png",
        "config": muni_mosaic_template_config(
            accent_color="#1D3557",
            pill_color="#0077B6",
            secondary_color="#F77F00",
            signer_role_title="Dirección de Deportes",
        ),
    },
    {
        "name": "Muni San Roque — Salud, RCP y Bienestar",
        "bg_filename": "plantilla_comunidad_salud.png",
        "config": muni_mosaic_template_config(
            accent_color="#0F766E",
            pill_color="#10B981",
            secondary_color="#0D9488",
            signer_role_title="Dirección de Salud y Acción Social",
        ),
    },
    {
        "name": "Muni San Roque — Emprendedores, Oficios y Comercio",
        "bg_filename": "plantilla_emprendimiento.png",
        "config": muni_mosaic_template_config(
            accent_color="#9A3412",
            pill_color="#EA580C",
            secondary_color="#D97706",
            signer_role_title="Coordinación de Desarrollo Local",
        ),
    },
    {
        "name": "Muni San Roque — Cultura, Arte y Música",
        "bg_filename": "plantilla_cultura_arte.png",
        "config": muni_mosaic_template_config(
            accent_color="#581C87",
            pill_color="#9333EA",
            secondary_color="#7E22CE",
            signer_role_title="Dirección de Cultura",
        ),
    },
    {
        "name": "Muni San Roque — Ambiente, Ecología y Reciclaje",
        "bg_filename": "plantilla_ambiente_ecologia.png",
        "config": muni_mosaic_template_config(
            accent_color="#1B4332",
            pill_color="#2D6A4F",
            secondary_color="#40916C",
            signer_role_title="Dirección de Ambiente",
        ),
    },
    {
        "name": "Muni San Roque — Institucional General",
        "bg_filename": "plantilla_muni_general.png",
        "config": muni_mosaic_template_config(
            accent_color="#14325C",
            pill_color="#2563EB",
            secondary_color="#1E40AF",
            signer_role_title="Municipalidad de San Roque",
        ),
    },
    {
        "name": "Clásico Institucional (Azul y Oro)",
        "bg_filename": "plantilla_clasica_azul_oro.png",
        "config": default_template_config(
            accent_color="#14325C",
            secondary_color="#A87C2D",
            name_color="#0E2444",
            body_color="#2A3441",
        ),
    },
    {
        "name": "Moderno Municipal (Verde y Pizarra)",
        "bg_filename": "plantilla_moderna_pizarra.png",
        "config": default_template_config(
            accent_color="#1B4332",
            secondary_color="#2D6A4F",
            name_color="#14213D",
            body_color="#334155",
        ),
    },
    {
        "name": "Distinción Solemne (Borgoña y Dorado)",
        "bg_filename": "plantilla_solemne_borgona.png",
        "config": default_template_config(
            accent_color="#6B1D2F",
            secondary_color="#9E7B2F",
            name_color="#2B1218",
            body_color="#362F32",
        ),
    },
]


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Abre una conexión SQLite con RowFactory y claves foráneas activadas."""
    target = db_path or DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db_session(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Context manager transaccional para operaciones con SQLite."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_preset_templates(conn: sqlite3.Connection) -> None:
    """Sincroniza las 13 plantillas institucionales precargadas sin tocar las creadas por el usuario."""
    # Eliminar presets antiguos que cambiaron de nombre (solo si no están referenciados o actualizarlos)
    valid_preset_names = {p["name"] for p in PRESET_DEFINITIONS}
    old_presets = conn.execute(
        "SELECT id, name FROM templates WHERE is_preset = 1"
    ).fetchall()
    for row in old_presets:
        if row["name"] not in valid_preset_names:
            conn.execute("DELETE FROM templates WHERE id = ? AND is_preset = 1", (row["id"],))

    existing = conn.execute(
        "SELECT id, name, logo_main_path, logo_sec_path, config_json FROM templates WHERE is_preset = 1"
    ).fetchall()
    existing_by_name = {row["name"]: dict(row) for row in existing}

    for preset in PRESET_DEFINITIONS:
        bg_path = str(PRESET_TEMPLATES_DIR / preset["bg_filename"])
        logos_cfg = preset["config"].get("logos", {})
        logo_main = logos_cfg.get("main", {}).get("image_path", "")
        logo_sec = logos_cfg.get("secondary", {}).get("image_path", "")

        if preset["name"] in existing_by_name:
            row = existing_by_name[preset["name"]]
            try:
                cfg = json.loads(row["config_json"])
            except Exception:
                cfg = preset["config"]
            updated = False

            # Si aún tenía los logos vacíos, completar los 2 logos oficiales
            if (logo_main or logo_sec) and not row.get("logo_main_path") and not row.get("logo_sec_path"):
                cfg_logos = cfg.setdefault("logos", {})
                if logo_main and not cfg_logos.setdefault("main", {}).get("image_path"):
                    cfg_logos["main"]["image_path"] = logo_main
                if logo_sec and not cfg_logos.setdefault("secondary", {}).get("image_path"):
                    cfg_logos["secondary"]["image_path"] = logo_sec
                updated = True

            # Actualizar cuerpo por defecto en plantillas Mosaico si aún tenía el tamaño pequeño (32) o texto antiguo
            body_cfg = cfg.get("body", {})
            preset_body = preset["config"].get("body", {})
            if body_cfg.get("size") in (32, 34, 35) or "{TIPO_EVENTO} DE {CURSO}" in str(body_cfg.get("text", "")):
                cfg["body"] = preset_body
                for k in ("header_institution", "recipient_dni", "footer_date"):
                    if cfg.get(k, {}).get("font") == "Montserrat-Regular.ttf":
                        cfg[k]["font"] = "Poppins-Regular.ttf"
                updated = True

            if updated:
                conn.execute(
                    """
                    UPDATE templates
                    SET logo_main_path = ?, logo_sec_path = ?, config_json = ?
                    WHERE id = ? AND is_preset = 1
                    """,
                    (
                        row.get("logo_main_path") or logo_main,
                        row.get("logo_sec_path") or logo_sec,
                        json.dumps(cfg, ensure_ascii=False),
                        row["id"],
                    ),
                )
            continue

        conn.execute(
            """
            INSERT INTO templates (name, is_preset, bg_path, logo_main_path, logo_sec_path, config_json)
            VALUES (?, 1, ?, ?, ?, ?)
            """,
            (
                preset["name"],
                bg_path,
                logo_main,
                logo_sec,
                json.dumps(preset["config"], ensure_ascii=False),
            ),
        )


def init_db(db_path: Path | None = None) -> None:
    """Inicializa directorios locales, esquema SQLite y plantillas precargadas."""
    ensure_app_directories()
    with db_session(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        seed_preset_templates(conn)
