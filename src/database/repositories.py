"""Repositorios CRUD para Plantillas, Cursos, Padrón de Personas y Asistentes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.database.connection import db_session
from src.services.validators import clean_dni, normalize_name, normalize_text


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row is not None else {}


class TemplateRepository:
    """Operaciones CRUD sobre la tabla `templates`."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path

    def list_all(self) -> list[dict[str, Any]]:
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM templates ORDER BY is_preset DESC, id ASC"
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["config"] = json.loads(item["config_json"])
            result.append(item)
        return result

    def get_by_id(self, template_id: int) -> dict[str, Any] | None:
        with db_session(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM templates WHERE id = ?", (template_id,)
            ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["config"] = json.loads(item["config_json"])
        return item

    def create(
        self,
        *,
        name: str,
        bg_path: str,
        config: dict[str, Any],
        logo_main_path: str = "",
        logo_sec_path: str = "",
        is_preset: bool = False,
    ) -> int:
        with db_session(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO templates (name, is_preset, bg_path, logo_main_path, logo_sec_path, config_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    normalize_text(name),
                    1 if is_preset else 0,
                    bg_path,
                    logo_main_path,
                    logo_sec_path,
                    json.dumps(config, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def update(
        self,
        template_id: int,
        *,
        name: str | None = None,
        bg_path: str | None = None,
        logo_main_path: str | None = None,
        logo_sec_path: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        fields: list[str] = []
        values: list[Any] = []
        if name is not None:
            fields.append("name = ?")
            values.append(normalize_text(name))
        if bg_path is not None:
            fields.append("bg_path = ?")
            values.append(bg_path)
        if logo_main_path is not None:
            fields.append("logo_main_path = ?")
            values.append(logo_main_path)
        if logo_sec_path is not None:
            fields.append("logo_sec_path = ?")
            values.append(logo_sec_path)
        if config is not None:
            fields.append("config_json = ?")
            values.append(json.dumps(config, ensure_ascii=False))

        if not fields:
            return
        fields.append("updated_at = datetime('now', 'localtime')")
        values.append(template_id)

        with db_session(self.db_path) as conn:
            conn.execute(
                f"UPDATE templates SET {', '.join(fields)} WHERE id = ?", values
            )

    def delete(self, template_id: int) -> bool:
        with db_session(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM templates WHERE id = ? AND is_preset = 0", (template_id,)
            )
            return cursor.rowcount > 0


class CourseRepository:
    """Operaciones CRUD sobre la tabla `courses`."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path

    def list_all(self) -> list[dict[str, Any]]:
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT c.*, t.name AS template_name,
                       (SELECT COUNT(*) FROM attendees a WHERE a.course_id = c.id) AS total_attendees,
                       (SELECT COUNT(*) FROM attendees a WHERE a.course_id = c.id AND a.cert_generated = 1) AS total_generated
                FROM courses c
                LEFT JOIN templates t ON c.template_id = t.id
                ORDER BY c.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, course_id: int) -> dict[str, Any] | None:
        with db_session(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM courses WHERE id = ?", (course_id,)
            ).fetchone()
        return _row_to_dict(row) if row is not None else None

    def create(
        self,
        *,
        title: str,
        event_type: str,
        event_date: str,
        hours: str = "",
        location: str = "San Roque, Corrientes",
        template_id: int | None = None,
        folder_path: str = "",
    ) -> int:
        with db_session(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO courses (title, event_type, event_date, hours, location, template_id, folder_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalize_text(title),
                    normalize_text(event_type) or "Curso",
                    normalize_text(event_date),
                    normalize_text(hours),
                    normalize_text(location) or "San Roque, Corrientes",
                    template_id,
                    folder_path,
                ),
            )
            return int(cursor.lastrowid)

    def update(
        self,
        course_id: int,
        *,
        title: str,
        event_type: str,
        event_date: str,
        hours: str,
        location: str,
        template_id: int | None,
        folder_path: str | None = None,
    ) -> None:
        with db_session(self.db_path) as conn:
            if folder_path is not None:
                conn.execute(
                    """
                    UPDATE courses
                    SET title = ?, event_type = ?, event_date = ?, hours = ?, location = ?, template_id = ?, folder_path = ?
                    WHERE id = ?
                    """,
                    (
                        normalize_text(title),
                        normalize_text(event_type),
                        normalize_text(event_date),
                        normalize_text(hours),
                        normalize_text(location),
                        template_id,
                        folder_path,
                        course_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE courses
                    SET title = ?, event_type = ?, event_date = ?, hours = ?, location = ?, template_id = ?
                    WHERE id = ?
                    """,
                    (
                        normalize_text(title),
                        normalize_text(event_type),
                        normalize_text(event_date),
                        normalize_text(hours),
                        normalize_text(location),
                        template_id,
                        course_id,
                    ),
                )

    def delete(self, course_id: int) -> None:
        with db_session(self.db_path) as conn:
            conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))


class PersonRepository:
    """Padrón histórico local para autocompletado rápido por DNI."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path

    def get_by_dni(self, raw_dni: str) -> dict[str, Any] | None:
        dni = clean_dni(raw_dni)
        if not dni:
            return None
        with db_session(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM people WHERE dni = ?", (dni,)
            ).fetchone()
        return dict(row) if row is not None else None

    def upsert(
        self,
        *,
        dni: str,
        full_name: str,
        email: str = "",
        phone: str = "",
        institution_or_role: str = "",
        profile: str = "",
    ) -> str:
        cleaned_dni = clean_dni(dni)
        normalized_name = normalize_name(full_name)
        clean_inst = normalize_text(institution_or_role)
        clean_prof = normalize_text(profile)
        if clean_prof and clean_inst and clean_prof.lower() not in clean_inst.lower():
            final_role = f"{clean_prof} — {clean_inst}"
        else:
            final_role = clean_inst or clean_prof

        with db_session(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO people (dni, full_name, email, phone, institution_or_role, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
                ON CONFLICT(dni) DO UPDATE SET
                    full_name = excluded.full_name,
                    email = excluded.email,
                    phone = excluded.phone,
                    institution_or_role = excluded.institution_or_role,
                    updated_at = datetime('now', 'localtime')
                """,
                (
                    cleaned_dni,
                    normalized_name,
                    normalize_text(email),
                    normalize_text(phone),
                    final_role,
                ),
            )
        return cleaned_dni

    def search(self, query: str, limit: int = 30) -> list[dict[str, Any]]:
        pattern = f"%{normalize_text(query)}%"
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM people
                WHERE dni LIKE ? OR full_name LIKE ?
                ORDER BY full_name ASC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()
        return [dict(row) for row in rows]


class AttendeeRepository:
    """Inscripciones, asistencia y estado de emisión por curso."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path

    def enroll(self, course_id: int, raw_dni: str, attended: bool = True) -> int:
        dni = clean_dni(raw_dni)
        with db_session(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO attendees (course_id, dni, attended)
                VALUES (?, ?, ?)
                ON CONFLICT(course_id, dni) DO UPDATE SET attended = excluded.attended
                """,
                (course_id, dni, 1 if attended else 0),
            )
            row = conn.execute(
                "SELECT id FROM attendees WHERE course_id = ? AND dni = ?",
                (course_id, dni),
            ).fetchone()
        return int(row["id"])

    def list_by_course(
        self, course_id: int, search_query: str = ""
    ) -> list[dict[str, Any]]:
        query = normalize_text(search_query)
        with db_session(self.db_path) as conn:
            if query:
                pattern = f"%{query}%"
                rows = conn.execute(
                    """
                    SELECT a.*, p.full_name, p.email, p.phone, p.institution_or_role
                    FROM attendees a
                    JOIN people p ON a.dni = p.dni
                    WHERE a.course_id = ? AND (p.dni LIKE ? OR p.full_name LIKE ?)
                    ORDER BY p.full_name ASC
                    """,
                    (course_id, pattern, pattern),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT a.*, p.full_name, p.email, p.phone, p.institution_or_role
                    FROM attendees a
                    JOIN people p ON a.dni = p.dni
                    WHERE a.course_id = ?
                    ORDER BY p.full_name ASC
                    """,
                    (course_id,),
                ).fetchall()
        return [dict(row) for row in rows]

    def set_attended(self, attendee_id: int, attended: bool) -> None:
        with db_session(self.db_path) as conn:
            conn.execute(
                "UPDATE attendees SET attended = ? WHERE id = ?",
                (1 if attended else 0, attendee_id),
            )

    def mark_certificate_generated(
        self, attendee_id: int, cert_file_path: str
    ) -> None:
        with db_session(self.db_path) as conn:
            conn.execute(
                """
                UPDATE attendees
                SET cert_generated = 1,
                    cert_file_path = ?,
                    generated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (cert_file_path, attendee_id),
            )

    def remove(self, attendee_id: int) -> None:
        with db_session(self.db_path) as conn:
            conn.execute("DELETE FROM attendees WHERE id = ?", (attendee_id,))
