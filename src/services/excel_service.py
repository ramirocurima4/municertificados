"""Importación y exportación de nóminas Excel usando exclusivamente openpyxl."""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from src.services.validators import (
    clean_dni,
    format_dni_display,
    is_valid_dni,
    normalize_name,
    normalize_text,
)


def _norm_header(value: Any) -> str:
    text = normalize_text(str(value or "")).lower()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def _detect_columns(header_row: tuple[Any, ...]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for idx, cell in enumerate(header_row):
        h = _norm_header(cell)
        if not h:
            continue
        if "dni" in h or "documento" in h or h == "doc":
            mapping.setdefault("dni", idx)
        elif any(k in h for k in ("apellido y nombre", "nombre completo", "apenom", "participante", "asistente")):
            mapping.setdefault("full_name", idx)
        elif h in ("apellido", "apellidos"):
            mapping.setdefault("last_name", idx)
        elif h in ("nombre", "nombres"):
            mapping.setdefault("first_name", idx)
        elif "mail" in h or "correo" in h:
            mapping.setdefault("email", idx)
        elif "tel" in h or "cel" in h or "whatsapp" in h:
            mapping.setdefault("phone", idx)
        elif any(k in h for k in ("perfil", "rol", "tipo de asistente", "condicion", "categoria")):
            mapping.setdefault("profile", idx)
        elif any(
            k in h
            for k in (
                "institucion",
                "cargo",
                "area",
                "organismo",
                "empresa",
                "escuela",
                "dependencia",
                "establecimiento",
            )
        ):
            mapping.setdefault("institution", idx)
    return mapping


def import_attendees_from_excel(
    file_path: str | Path,
) -> tuple[list[dict[str, str]], list[str]]:
    """Importa asistentes desde .xlsx/.xlsm con detección automática de columnas."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo Excel: {path}")

    wb = load_workbook(filename=str(path), read_only=True, data_only=True)
    try:
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)

        col_map: dict[str, int] = {}
        header_found = False
        for row in rows_iter:
            if not row or not any(row):
                continue
            candidate = _detect_columns(row)
            if "dni" in candidate and (
                "full_name" in candidate
                or "first_name" in candidate
                or "last_name" in candidate
            ):
                col_map = candidate
                header_found = True
                break

        if not header_found:
            raise ValueError(
                "No se detectaron columnas válidas de DNI y Nombre/Apellido en la planilla."
            )

        records: list[dict[str, str]] = []
        warnings: list[str] = []

        for row_num, row in enumerate(rows_iter, start=2):
            if not row or not any(row):
                continue

            raw_dni = row[col_map["dni"]] if col_map["dni"] < len(row) else ""
            dni = clean_dni(raw_dni)
            if not is_valid_dni(dni):
                warnings.append(f"Fila {row_num}: DNI inválido ({raw_dni!r}), omitida.")
                continue

            if "full_name" in col_map and col_map["full_name"] < len(row):
                raw_name = str(row[col_map["full_name"]] or "")
            else:
                last_n = (
                    str(row[col_map["last_name"]] or "")
                    if "last_name" in col_map and col_map["last_name"] < len(row)
                    else ""
                )
                first_n = (
                    str(row[col_map["first_name"]] or "")
                    if "first_name" in col_map and col_map["first_name"] < len(row)
                    else ""
                )
                raw_name = f"{first_n} {last_n}".strip()

            full_name = normalize_name(raw_name)
            if not full_name:
                warnings.append(f"Fila {row_num}: Nombre vacío para DNI {dni}, omitida.")
                continue

            email = (
                normalize_text(str(row[col_map["email"]] or ""))
                if "email" in col_map and col_map["email"] < len(row)
                else ""
            )
            phone = (
                normalize_text(str(row[col_map["phone"]] or ""))
                if "phone" in col_map and col_map["phone"] < len(row)
                else ""
            )
            institution = (
                normalize_text(str(row[col_map["institution"]] or ""))
                if "institution" in col_map and col_map["institution"] < len(row)
                else ""
            )
            profile = (
                normalize_text(str(row[col_map["profile"]] or ""))
                if "profile" in col_map and col_map["profile"] < len(row)
                else ""
            )

            if profile and institution and profile.lower() not in institution.lower():
                combined_role = f"{profile} — {institution}"
            else:
                combined_role = institution or profile

            records.append(
                {
                    "dni": dni,
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "profile": profile,
                    "institution_or_role": combined_role,
                }
            )
    finally:
        wb.close()

    return records, warnings


def export_attendees_excel(
    course_data: dict[str, Any],
    attendees: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Exporta la nómina oficial Nomina_Asistentes.xlsx con formato institucional."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Nómina de Asistentes"

    navy_fill = PatternFill("solid", fgColor="14325C")
    sub_fill = PatternFill("solid", fgColor="E2E8F0")
    zebra_fill = PatternFill("solid", fgColor="F8FAFC")
    thin_side = Side(style="thin", color="CBD5E1")
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    # Encabezado institucional
    ws.merge_cells("A1:I1")
    ws["A1"] = "MUNICIPALIDAD DE SAN ROQUE — ÁREA DE REDES"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    ws["A1"].fill = navy_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:I2")
    ws["A2"] = (
        f"{course_data.get('event_type', 'Curso')}: {course_data.get('title', '')}  |  "
        f"Fecha: {course_data.get('event_date', '')}  |  "
        f"Carga horaria: {course_data.get('hours', '-') or '-'}  |  "
        f"Lugar: {course_data.get('location', 'San Roque, Corrientes')}"
    )
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="1E293B")
    ws["A2"].fill = sub_fill
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    headers = [
        "N°",
        "DNI",
        "Apellido y Nombre",
        "Institución / Cargo",
        "Email",
        "Teléfono",
        "Asistencia",
        "Certificado Emitido",
        "Fecha de Emisión",
    ]
    header_row_idx = 4
    ws.row_dimensions[header_row_idx].height = 24
    for col_idx, title in enumerate(headers, start=1):
        cell = ws.cell(row=header_row_idx, column=col_idx, value=title)
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    for idx, att in enumerate(attendees, start=1):
        r = header_row_idx + idx
        ws.row_dimensions[r].height = 20
        values = [
            idx,
            format_dni_display(att.get("dni", "")),
            att.get("full_name", ""),
            att.get("institution_or_role", ""),
            att.get("email", ""),
            att.get("phone", ""),
            "Presente" if att.get("attended", 1) else "Ausente",
            "Sí" if att.get("cert_generated", 0) else "Pendiente",
            att.get("generated_at", "") or "-",
        ]
        for c_idx, val in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c_idx, value=val)
            cell.font = Font(name="Calibri", size=10, color="0F172A")
            cell.border = border
            if idx % 2 == 0:
                cell.fill = zebra_fill
            align_h = "center" if c_idx in (1, 2, 7, 8, 9) else "left"
            cell.alignment = Alignment(horizontal=align_h, vertical="center")

    col_widths = [6, 15, 34, 26, 28, 18, 13, 20, 20]
    for col_idx, width in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.freeze_panes = f"A{header_row_idx + 1}"
    wb.save(str(out))
    return out
