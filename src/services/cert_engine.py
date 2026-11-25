"""Motor de composición de certificados (Pillow + PyMuPDF) en 300 DPI."""

from __future__ import annotations

import copy
import io
import re
from pathlib import Path
from typing import Any, Sequence

import pymupdf
from PIL import Image, ImageDraw, ImageFont, ImageOps

from src.config import (
    A4_LANDSCAPE_HEIGHT_PT,
    A4_LANDSCAPE_HEIGHT_PX,
    A4_LANDSCAPE_WIDTH_PT,
    A4_LANDSCAPE_WIDTH_PX,
    ASSETS_LOGOS_DIR,
    DEFAULT_DPI,
    FONTS_DIR,
    SUPPORTED_PDF_EXTENSIONS,
)
from src.services.validators import format_dni_display, is_supported_asset, normalize_name

SAFE_PRINT_MARGIN_PX = 180
LOGO_SLOT_KEYS = ("main", "secondary", "logo_3", "logo_4")


def font_display_name(filename: str) -> str:
    """Convierte un nombre de archivo .ttf en un nombre legible para el selector."""
    stem = Path(filename).stem
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", stem).replace("-", " ").replace("_", " ")
    return " ".join(spaced.split())


def list_available_fonts() -> list[tuple[str, str]]:
    """Lista dinámicamente todas las fuentes .ttf de assets/fonts/ como (nombre_visible, archivo)."""
    if not FONTS_DIR.is_dir():
        return []
    items = [(font_display_name(p.name), p.name) for p in FONTS_DIR.glob("*.ttf")]
    return sorted(items, key=lambda pair: pair[0].lower())


_INSTITUTIONAL_LOGO_LABELS = {
    "logo_avanzamos_juntos.png": "# Avanzamos Juntos (Lema)",
    "logo_san_roque_escudo.png": "Escudo San Roque Municipio",
    "logo_san_roque_puente.png": "San Roque Puente (#AvanzamosJuntos)",
}


def list_institutional_logos() -> list[tuple[str, str]]:
    """Lista los logos institucionales precargados en assets/logos/ como (nombre_visible, ruta)."""
    if not ASSETS_LOGOS_DIR.is_dir():
        return []
    items: list[tuple[str, str]] = []
    for p in sorted(ASSETS_LOGOS_DIR.iterdir()):
        if p.is_file() and is_supported_asset(p):
            label = _INSTITUTIONAL_LOGO_LABELS.get(
                p.name, font_display_name(p.stem)
            )
            items.append((label, str(p)))
    return items


def resolve_x_px(val: float | int | None, default_px: int = 1754) -> int:
    """Convierte una coordenada X (normalizada 0..1 o en píxeles) a píxeles A4 (0..3508)."""
    if val is None:
        return default_px
    try:
        fval = float(val)
    except (TypeError, ValueError):
        return default_px
    if 0.0 < fval <= 1.0:
        return int(round(fval * A4_LANDSCAPE_WIDTH_PX))
    return int(round(fval))


def resolve_y_px(val: float | int | None, default_px: int = 1240) -> int:
    """Convierte una coordenada Y (normalizada 0..1 o en píxeles) a píxeles A4 (0..2480)."""
    if val is None:
        return default_px
    try:
        fval = float(val)
    except (TypeError, ValueError):
        return default_px
    if 0.0 < fval <= 1.0:
        return int(round(fval * A4_LANDSCAPE_HEIGHT_PX))
    return int(round(fval))


def _clamp_safe_x(x_px: float, margin: int = SAFE_PRINT_MARGIN_PX) -> float:
    return max(float(margin), min(float(A4_LANDSCAPE_WIDTH_PX - margin), x_px))


def _clamp_safe_y(y_px: float, margin: int = SAFE_PRINT_MARGIN_PX) -> float:
    return max(float(margin), min(float(A4_LANDSCAPE_HEIGHT_PX - margin), y_px))


def _resolve_font_path(font_name: str) -> Path:
    candidate = Path(font_name)
    if candidate.is_file():
        return candidate
    bundled = FONTS_DIR / font_name
    if bundled.is_file():
        return bundled
    fallback = FONTS_DIR / "NotoSans-Regular.ttf"
    if fallback.is_file():
        return fallback
    raise FileNotFoundError(f"No se encontró la fuente tipográfica: {font_name}")


def _load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    font_path = _resolve_font_path(font_name)
    return ImageFont.truetype(str(font_path), max(8, int(size)))


def remove_white_background(
    image: Image.Image, threshold: int = 235, soft_edge: int = 20
) -> Image.Image:
    """Remueve el fondo blanco o casi blanco de logos/firmas JPG/PNG/WEBP/PDF."""
    rgba = image.convert("RGBA")
    threshold = max(150, min(255, int(threshold)))
    soft_start = max(0, threshold - max(1, int(soft_edge)))

    pixels = (
        rgba.get_flattened_data()
        if hasattr(rgba, "get_flattened_data")
        else rgba.getdata()
    )
    new_pixels: list[tuple[int, int, int, int]] = []
    for r, g, b, a in pixels:
        if a == 0:
            new_pixels.append((r, g, b, 0))
            continue

        min_channel = min(r, g, b)
        if min_channel >= threshold:
            new_pixels.append((r, g, b, 0))
        elif min_channel > soft_start:
            factor = (threshold - min_channel) / (threshold - soft_start)
            new_alpha = int(a * factor)
            new_pixels.append((r, g, b, new_alpha))
        else:
            new_pixels.append((r, g, b, a))

    result = Image.new("RGBA", rgba.size)
    result.putdata(new_pixels)
    return result


def tint_logo_image(image: Image.Image, hex_color: str) -> Image.Image:
    """Reemplaza los píxeles visibles de un logo por el color elegido conservando su transparencia alfa."""
    cleaned = str(hex_color or "").strip()
    if not (cleaned.startswith("#") and len(cleaned) in (4, 7)):
        cleaned = "#14325C"
    rgba = image.convert("RGBA")
    _, _, _, alpha = rgba.split()
    tinted = Image.new("RGBA", rgba.size, cleaned)
    tinted.putalpha(alpha)
    return tinted


def load_visual_asset(
    asset_path: str | Path,
    *,
    target_size: tuple[int, int] | None = None,
    transparent: bool = True,
    dpi: int = DEFAULT_DPI,
) -> Image.Image:
    """Carga una plantilla, logo o firma desde .pdf, .png, .jpg, .jpeg o .webp."""
    path = Path(asset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Recurso visual no encontrado: {path}")
    if not is_supported_asset(path):
        raise ValueError(f"Formato visual no soportado: {path.suffix}")

    if path.suffix.lower() in SUPPORTED_PDF_EXTENSIONS:
        with pymupdf.open(str(path)) as doc:
            if len(doc) == 0:
                raise ValueError(f"El archivo PDF está vacío: {path}")
            page = doc[0]
            if target_size is not None:
                zoom_x = target_size[0] / max(1.0, page.rect.width)
                zoom_y = target_size[1] / max(1.0, page.rect.height)
                scale = max(zoom_x, zoom_y)
                matrix = pymupdf.Matrix(scale, scale)
            else:
                zoom = dpi / 72.0
                matrix = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=transparent)
            mode = "RGBA" if pix.alpha else "RGB"
            img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    else:
        with Image.open(path) as opened:
            transposed = ImageOps.exif_transpose(opened)
            img = transposed.convert("RGBA" if transparent else "RGB")

    if target_size is not None:
        img = img.resize(target_size, Image.Resampling.LANCZOS)
    return img


def _fit_text_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_name: str,
    start_size: int,
    min_size: int,
    max_width_px: int,
) -> ImageFont.FreeTypeFont:
    size = int(start_size)
    min_s = max(12, int(min_size))
    while size > min_s:
        font = _load_font(font_name, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width_px:
            return font
        size -= 2
    return _load_font(font_name, min_s)


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width_px: int,
) -> list[str]:
    lines: list[str] = []
    for paragraph in str(text).splitlines():
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if (bbox[2] - bbox[0]) <= max_width_px:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _draw_aligned_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x_px: float,
    y_px: float,
    font: ImageFont.FreeTypeFont,
    color: str,
    align: str = "center",
) -> None:
    if not text:
        return
    anchor = "lm" if str(align).lower() == "left" else "mm"
    draw.text((x_px, y_px), text, font=font, fill=color, anchor=anchor)


def _paste_centered_asset(
    canvas: Image.Image,
    asset_path: str | Path,
    center_x: float,
    center_y: float,
    max_width: int,
    max_height: int,
    *,
    remove_white_bg: bool = False,
    white_threshold: int = 235,
    tint_enabled: bool = False,
    tint_color: str = "#14325C",
) -> None:
    if not asset_path:
        return
    path = Path(asset_path)
    if not path.is_file():
        bundled_candidate = ASSETS_LOGOS_DIR / path.name
        if bundled_candidate.is_file():
            path = bundled_candidate
        else:
            return

    img = load_visual_asset(path, transparent=True)
    if remove_white_bg:
        img = remove_white_background(img, threshold=white_threshold)
    if tint_enabled and tint_color:
        img = tint_logo_image(img, tint_color)

    img.thumbnail((max(40, max_width), max(40, max_height)), Image.Resampling.LANCZOS)
    x = int(center_x - img.width / 2)
    y = int(center_y - img.height / 2)
    canvas.alpha_composite(img, dest=(x, y))


def _build_placeholders(
    person_data: dict[str, Any], course_data: dict[str, Any]
) -> dict[str, str]:
    raw_name = person_data.get("full_name", "")
    raw_dni = person_data.get("dni", "")
    ev_type = str(course_data.get("event_type", "Curso")).strip()
    course_title = str(course_data.get("title", "")).strip()
    return {
        "nombre": normalize_name(raw_name),
        "NOMBRE": normalize_name(raw_name).upper(),
        "dni": format_dni_display(raw_dni),
        "curso": course_title,
        "CURSO": course_title.upper(),
        "tipo_evento": ev_type.lower(),
        "TIPO_EVENTO": ev_type.upper(),
        "fecha": str(course_data.get("event_date", "")).strip(),
        "carga_horaria": str(course_data.get("hours", "")).strip()
        or "sin carga horaria especificada",
        "lugar": str(course_data.get("location", "San Roque, Corrientes")).strip(),
    }


def _format_template_string(template_str: str, placeholders: dict[str, str]) -> str:
    result = template_str
    for key, value in placeholders.items():
        result = result.replace(f"{{{key}}}", value)
    # Evitar duplicación si {CURSO} ya empieza con el mismo tipo de evento (ej. "CURSO DE CURSO DE...")
    result = re.sub(
        r"\b(?P<ev>CURSO|TALLER|JORNADA|CAPACITACI[ÓO]N)\s+(?:DE\s+|EN\s+)?(?P<q>«)?(?P=ev)\b",
        r"\g<q>\g<ev>",
        result,
        flags=re.IGNORECASE,
    )
    return result


def _resolve_logo_path(
    slot_key: str, slot_cfg: dict[str, Any], template_data: dict[str, Any]
) -> str:
    path = str(slot_cfg.get("image_path", "") or "").strip()
    if not path:
        if slot_key == "main":
            path = str(template_data.get("logo_main_path", "") or "").strip()
        elif slot_key == "secondary":
            path = str(template_data.get("logo_sec_path", "") or "").strip()
    if not path:
        return ""
    p = Path(path)
    if p.is_file():
        return str(p)
    bundled = ASSETS_LOGOS_DIR / p.name
    if bundled.is_file():
        return str(bundled)
    return path


def render_certificate_image(
    template_data: dict[str, Any],
    course_data: dict[str, Any],
    person_data: dict[str, Any],
) -> Image.Image:
    """Compone el certificado completo en alta resolución (3508 x 2480 px, 300 DPI)."""
    width = A4_LANDSCAPE_WIDTH_PX
    height = A4_LANDSCAPE_HEIGHT_PX
    config: dict[str, Any] = template_data.get("config", {})
    placeholders = _build_placeholders(person_data, course_data)

    bg_path = template_data.get("bg_path", "")
    if bg_path and Path(bg_path).is_file():
        canvas = load_visual_asset(
            bg_path, target_size=(width, height), transparent=True
        )
    else:
        canvas = Image.new("RGBA", (width, height), (250, 248, 242, 255))

    # 1. Hasta 4 Logos Institucionales con posición X/Y y tamaño libres
    logos_cfg = config.get("logos", {})
    default_logo_coords = {
        "main": (490, 360),
        "secondary": (3015, 360),
        "logo_3": (2790, 2140),
        "logo_4": (3110, 2140),
    }
    for slot_key in LOGO_SLOT_KEYS:
        slot_cfg = logos_cfg.get(slot_key, {})
        if not isinstance(slot_cfg, dict):
            continue
        asset_path = _resolve_logo_path(slot_key, slot_cfg, template_data)
        if not asset_path:
            continue
        def_x, def_y = default_logo_coords.get(slot_key, (2400, 2140))
        lx = _clamp_safe_x(resolve_x_px(slot_cfg.get("x"), def_x), margin=120)
        ly = _clamp_safe_y(resolve_y_px(slot_cfg.get("y"), def_y), margin=100)
        max_w = int(slot_cfg.get("max_width", 260))
        max_h = int(slot_cfg.get("max_height", max(180, int(max_w * 0.85))))
        _paste_centered_asset(
            canvas,
            asset_path,
            lx,
            ly,
            max_w,
            max_h,
            remove_white_bg=bool(slot_cfg.get("remove_white_bg", False)),
            white_threshold=int(slot_cfg.get("white_threshold", 235)),
            tint_enabled=bool(slot_cfg.get("tint_enabled", False)),
            tint_color=str(slot_cfg.get("tint_color", "#14325C")),
        )

    draw = ImageDraw.Draw(canvas)

    # 2. Bloques de texto simples (con soporte de alineación 'left' o 'center' y X/Y libres)
    show_dni = bool(config.get("show_dni", True))
    for key in (
        "header_institution",
        "header_area",
        "title",
        "subtitle",
        "recipient_dni",
        "footer_date",
    ):
        if key == "recipient_dni" and not show_dni:
            continue
        block = config.get(key)
        if not block:
            continue
        text = _format_template_string(str(block.get("text", "")), placeholders).strip()
        if not text:
            continue
        align = str(block.get("align", "center")).lower()
        bx = _clamp_safe_x(resolve_x_px(block.get("x"), 320 if align == "left" else width // 2))
        by = _clamp_safe_y(resolve_y_px(block.get("y"), height // 2))
        max_avail_w = (
            int(width - SAFE_PRINT_MARGIN_PX - bx)
            if align == "left"
            else int(width - 2 * SAFE_PRINT_MARGIN_PX)
        )
        font = _fit_text_font(
            draw,
            text,
            block.get("font", "NotoSans-Regular.ttf"),
            int(block.get("size", 32)),
            20,
            max(400, max_avail_w),
        )
        _draw_aligned_text(
            draw,
            text,
            bx,
            by,
            font,
            block.get("color", "#1B365D"),
            align=align,
        )

    # 3. Franja / Pastilla destacada de Nombre del Curso (course_banner)
    banner_cfg = config.get("course_banner", {})
    if banner_cfg and bool(banner_cfg.get("enabled", False)):
        banner_text = _format_template_string(
            str(banner_cfg.get("text", "{curso}")), placeholders
        ).strip()
        if banner_text:
            align = str(banner_cfg.get("align", "left")).lower()
            bx = _clamp_safe_x(
                resolve_x_px(banner_cfg.get("x"), 320 if align == "left" else width // 2)
            )
            by = _clamp_safe_y(resolve_y_px(banner_cfg.get("y"), 440))
            max_banner_w = (
                int(width - SAFE_PRINT_MARGIN_PX - bx - 80)
                if align == "left"
                else int(width * 0.78)
            )
            b_font = _fit_text_font(
                draw,
                banner_text,
                banner_cfg.get("font", "Poppins-Bold.ttf"),
                int(banner_cfg.get("size", 48)),
                24,
                max(400, max_banner_w),
            )
            anchor = "lm" if align == "left" else "mm"
            if bool(banner_cfg.get("pill_enabled", True)):
                pad_x = int(banner_cfg.get("pill_padding_x", 22))
                pad_y = int(banner_cfg.get("pill_padding_y", 14))
                pill_radius = int(banner_cfg.get("pill_radius", 4))
                text_x = bx + pad_x if align == "left" else bx
                bbox = draw.textbbox((text_x, by), banner_text, font=b_font, anchor=anchor)
                pill_rect = (
                    bbox[0] - pad_x,
                    bbox[1] - pad_y,
                    bbox[2] + pad_x,
                    bbox[3] + pad_y,
                )
                draw.rounded_rectangle(
                    pill_rect,
                    radius=pill_radius,
                    fill=banner_cfg.get("pill_color", "#76B02A"),
                )
                draw.text(
                    (text_x, by),
                    banner_text,
                    font=b_font,
                    fill=banner_cfg.get("color", "#FFFFFF"),
                    anchor=anchor,
                )
            else:
                _draw_aligned_text(
                    draw,
                    banner_text,
                    bx,
                    by,
                    b_font,
                    banner_cfg.get("color", "#14325C"),
                    align=align,
                )

    # 4. Nombre del Homenajeado con autoajuste matemático y línea inferior opcional
    name_cfg = config.get("recipient_name", {})
    name_text = placeholders["nombre"]
    name_align = str(name_cfg.get("align", "center")).lower()
    nx = _clamp_safe_x(
        resolve_x_px(name_cfg.get("x"), 320 if name_align == "left" else width // 2)
    )
    ny = _clamp_safe_y(resolve_y_px(name_cfg.get("y"), int(height * 0.445)))
    if name_align == "left":
        max_name_width = min(
            int(width * float(name_cfg.get("max_width_ratio", 0.78))),
            int(width - SAFE_PRINT_MARGIN_PX - nx),
        )
    else:
        max_name_width = int(width * float(name_cfg.get("max_width_ratio", 0.78)))

    name_font = _fit_text_font(
        draw,
        name_text,
        name_cfg.get("font", "NotoSerif-Bold.ttf"),
        int(name_cfg.get("size", 92)),
        int(name_cfg.get("min_size", 44)),
        max(500, max_name_width),
    )
    _draw_aligned_text(
        draw,
        name_text,
        nx,
        ny,
        name_font,
        name_cfg.get("color", "#0F2442"),
        align=name_align,
    )

    if bool(name_cfg.get("underline", False)):
        ul_color = name_cfg.get("underline_color") or name_cfg.get("color", "#14325C")
        if name_text:
            anchor = "lm" if name_align == "left" else "mm"
            nbbox = draw.textbbox((nx, ny), name_text, font=name_font, anchor=anchor)
            line_y = nbbox[3] + 18
            if name_align == "left":
                line_end_x = min(width - SAFE_PRINT_MARGIN_PX, max(nbbox[2] + 40, nx + 760))
                draw.line([(nx, line_y), (line_end_x, line_y)], fill=ul_color, width=4)
            else:
                half_w = max((nbbox[2] - nbbox[0]) // 2 + 40, 420)
                draw.line([(nx - half_w, line_y), (nx + half_w, line_y)], fill=ul_color, width=4)
        else:
            line_y = ny + 55
            if name_align == "left":
                draw.line([(nx, line_y), (min(width - SAFE_PRINT_MARGIN_PX, nx + 1350), line_y)], fill=ul_color, width=3)
            else:
                draw.line([(nx - 580, line_y), (nx + 580, line_y)], fill=ul_color, width=3)

    # 5. Cuerpo del certificado con word-wrapping, soporte de líneas en negrita (**...**) y alineación
    body_cfg = config.get("body", {})
    body_text = _format_template_string(str(body_cfg.get("text", "")), placeholders)
    body_size = int(body_cfg.get("size", 44))
    body_font_name = body_cfg.get("font", "Poppins-Regular.ttf")
    body_font = _load_font(body_font_name, body_size)
    body_bold_font = _load_font(
        body_cfg.get("bold_font", "Poppins-Bold.ttf"), body_size
    )
    body_align = str(body_cfg.get("align", "center")).lower()
    body_x = _clamp_safe_x(
        resolve_x_px(body_cfg.get("x"), 320 if body_align == "left" else width // 2)
    )
    start_y = _clamp_safe_y(resolve_y_px(body_cfg.get("y"), int(height * 0.615)))

    ratio_w = int(width * float(body_cfg.get("max_width_ratio", 0.76)))
    if body_align == "left":
        max_body_width = max(500, min(ratio_w, int(width - SAFE_PRINT_MARGIN_PX - body_x)))
    else:
        max_body_width = max(500, ratio_w)

    rendered_lines: list[tuple[str, ImageFont.FreeTypeFont]] = []
    for raw_para in body_text.splitlines():
        stripped = raw_para.strip()
        is_bold_para = stripped.startswith("**") and stripped.endswith("**") and len(stripped) > 4
        clean_para = stripped[2:-2].strip() if is_bold_para else stripped
        active_font = body_bold_font if is_bold_para else body_font
        for wrapped_line in _wrap_text(draw, clean_para, active_font, max_body_width):
            rendered_lines.append((wrapped_line, active_font))

    line_height = body_size * float(body_cfg.get("line_spacing", 1.38))
    for idx, (line_str, line_font) in enumerate(rendered_lines):
        _draw_aligned_text(
            draw,
            line_str,
            body_x,
            start_y + idx * line_height,
            line_font,
            body_cfg.get("color", "#1E293B"),
            align=body_align,
        )

    # 6. Bloques de firmas (1 o 2 firmas, alineación izquierda o centrada)
    sig_name_font = _load_font("NotoSans-Bold.ttf", 28)
    sig_role_font = _load_font("NotoSans-Regular.ttf", 24)
    for sig in config.get("signatures", []):
        if not sig.get("enabled", True):
            continue
        s_name = str(sig.get("name", "")).strip()
        s_role = str(sig.get("role", "")).strip()
        sig_img_path = str(sig.get("image_path", "")).strip()
        if not s_name and not s_role and not sig_img_path:
            continue

        sig_align = str(sig.get("align", "center")).lower()
        raw_x = resolve_x_px(sig.get("x"), 320 if sig_align == "left" else width // 2)
        sig_y = _clamp_safe_y(resolve_y_px(sig.get("y"), int(height * 0.845)))
        line_width = 480

        if sig_align == "left":
            line_x1 = _clamp_safe_x(raw_x, margin=SAFE_PRINT_MARGIN_PX)
            line_x2 = min(float(width - SAFE_PRINT_MARGIN_PX), line_x1 + line_width)
            center_x = (line_x1 + line_x2) / 2.0
        else:
            center_x = _clamp_safe_x(raw_x, margin=SAFE_PRINT_MARGIN_PX + 120)
            line_x1 = center_x - line_width / 2.0
            line_x2 = center_x + line_width / 2.0

        if sig_img_path:
            _paste_centered_asset(
                canvas,
                sig_img_path,
                center_x,
                sig_y - 68,
                int(sig.get("max_width", 360)),
                int(sig.get("max_height", 130)),
                remove_white_bg=bool(sig.get("remove_white_bg", True)),
                white_threshold=int(sig.get("white_threshold", 235)),
            )

        draw.line([(line_x1, sig_y), (line_x2, sig_y)], fill="#475569", width=3)
        _draw_aligned_text(
            draw,
            s_name,
            center_x,
            sig_y + 30,
            sig_name_font,
            "#1E293B",
            align="center",
        )
        _draw_aligned_text(
            draw,
            s_role,
            center_x,
            sig_y + 66,
            sig_role_font,
            "#475569",
            align="center",
        )

    return canvas.convert("RGB")


def render_preview_image(
    template_data: dict[str, Any],
    course_data: dict[str, Any],
    person_data: dict[str, Any],
    *,
    max_width: int = 1100,
) -> Image.Image:
    """Genera una vista previa escalada en memoria para mostrar en la interfaz."""
    full_img = render_certificate_image(template_data, course_data, person_data)
    ratio = max_width / full_img.width
    target_height = max(1, int(full_img.height * ratio))
    return full_img.resize((max_width, target_height), Image.Resampling.LANCZOS)


def export_certificate_pdf(
    image: Image.Image, output_pdf_path: str | Path
) -> Path:
    """Exporta un certificado renderizado a PDF A4 Apaisado de alta calidad."""
    out_path = Path(output_pdf_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    buffer = io.BytesIO()
    image.convert("RGB").save(
        buffer, format="JPEG", quality=95, dpi=(DEFAULT_DPI, DEFAULT_DPI)
    )
    img_bytes = buffer.getvalue()

    doc = pymupdf.open()
    page = doc.new_page(width=A4_LANDSCAPE_WIDTH_PT, height=A4_LANDSCAPE_HEIGHT_PT)
    page.insert_image(page.rect, stream=img_bytes)
    doc.save(str(out_path), deflate=True)
    doc.close()
    return out_path


def generate_certificate_pdf(
    template_data: dict[str, Any],
    course_data: dict[str, Any],
    person_data: dict[str, Any],
    output_pdf_path: str | Path,
) -> Path:
    """Renderiza y exporta directamente el certificado individual en PDF."""
    img = render_certificate_image(template_data, course_data, person_data)
    return export_certificate_pdf(img, output_pdf_path)


def generate_blank_contingency_pdf(
    template_data: dict[str, Any],
    course_data: dict[str, Any],
    output_pdf_path: str | Path,
) -> Path:
    """Genera un certificado en blanco (sin nombre ni DNI) manteniendo líneas, firmas y datos del curso."""
    blank_tpl = copy.deepcopy(template_data)
    cfg = blank_tpl.setdefault("config", {})
    cfg["show_dni"] = False
    cfg.setdefault("recipient_dni", {})["text"] = ""
    # Si es una plantilla clásica sin línea impresa en el fondo, activar línea para escritura manual
    bg_name = Path(str(blank_tpl.get("bg_path", ""))).name
    if any(k in bg_name for k in ("clasica", "moderna_pizarra", "solemne")):
        cfg.setdefault("recipient_name", {})["underline"] = True
    blank_person = {"full_name": "", "dni": ""}
    img = render_certificate_image(blank_tpl, course_data, blank_person)
    return export_certificate_pdf(img, output_pdf_path)


def merge_pdfs_for_print(
    pdf_paths: Sequence[str | Path], output_pdf_path: str | Path
) -> Path:
    """Une múltiples certificados individuales en un único PDF para impresión masiva."""
    valid_paths = [Path(p) for p in pdf_paths if Path(p).is_file()]
    if not valid_paths:
        raise ValueError("No hay archivos PDF válidos para unir.")

    out_path = Path(output_pdf_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    merged = pymupdf.open()
    try:
        for pdf_path in valid_paths:
            with pymupdf.open(str(pdf_path)) as src:
                merged.insert_pdf(src)
        merged.save(str(out_path), deflate=True)
    finally:
        merged.close()

    return out_path
