"""Genera el catálogo de plantillas institucionales en 300 DPI (A4 apaisado: 3508 x 2480 px).

Incluye:
- 10 plantillas con el formato oficial de Mosaico Geométrico de la Municipalidad de San Roque
  (Agro/Cultivos, Docentes/Educación, Guías Turísticos/Turismo, IA/Tecnología, Deportes,
   Salud, Emprendedores/Oficios, Cultura/Arte, Ambiente/Ecología e Institucional General).
- 3 plantillas clásicas ornamentales centradas.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

WIDTH = 3508
HEIGHT = 2480
DPI = (300, 300)

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"


# ==============================================================================
# Helpers de Iconografía Vectorial Minimalista para los Mosaicos (340 x 340 px)
# ==============================================================================


def _draw_sunburst_tile(
    draw: ImageDraw.ImageDraw, x0: int, y0: int, size: int, bg_color: str, ray_color: str
) -> None:
    """Azulejo 1: Fondo cálido con sol naciente y rayos geométricos (idéntico al certificado real)."""
    draw.rectangle((x0, y0, x0 + size, y0 + size), fill=bg_color)
    cx = x0 + size // 2
    cy = y0 + size - 18

    # Rayos trapezoidales / triangulares hacia arriba
    angles = [-72, -46, -22, 0, 22, 46, 72]
    for ang in angles:
        rad1 = math.radians(ang - 7)
        rad2 = math.radians(ang + 7)
        r_in = 70
        r_out = 165
        p1 = (cx + int(r_in * math.sin(rad1)), cy - int(r_in * math.cos(rad1)))
        p2 = (cx + int(r_out * math.sin(rad1)), cy - int(r_out * math.cos(rad1)))
        p3 = (cx + int(r_out * math.sin(rad2)), cy - int(r_out * math.cos(rad2)))
        p4 = (cx + int(r_in * math.sin(rad2)), cy - int(r_in * math.cos(rad2)))
        draw.polygon([p1, p2, p3, p4], fill=ray_color)

    # Semicírculo solar central en la base
    r_sun = 54
    draw.pieslice(
        (cx - r_sun, cy - r_sun, cx + r_sun, cy + r_sun),
        start=180,
        end=360,
        fill=ray_color,
    )


def _draw_leaf_shape(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    length: int,
    angle_deg: float,
    color: str,
    width: int = 8,
) -> None:
    """Dibuja una hoja orgánica con nervadura central usando arcos poligonales."""
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    pts_left = []
    pts_right = []
    steps = 20
    for i in range(steps + 1):
        t = i / steps
        px = (t - 0.5) * length
        py = math.sin(t * math.pi) * (length * 0.34)
        rx1 = cx + int(px * cos_a - py * sin_a)
        ry1 = cy + int(px * sin_a + py * cos_a)
        rx2 = cx + int(px * cos_a + py * sin_a)
        ry2 = cy + int(px * sin_a - py * cos_a)
        pts_left.append((rx1, ry1))
        pts_right.append((rx2, ry2))

    poly = pts_left + list(reversed(pts_right))
    draw.line(poly + [poly[0]], fill=color, width=width, joint="curve")
    # Nervadura central
    x_start = cx + int((-0.45 * length) * cos_a)
    y_start = cy + int((-0.45 * length) * sin_a)
    x_end = cx + int((0.35 * length) * cos_a)
    y_end = cy + int((0.35 * length) * sin_a)
    draw.line([(x_start, y_start), (x_end, y_end)], fill=color, width=max(4, width - 2))


def _icon_agro_top(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Dos hojas botánicas estilizadas (como en el certificado de Cultivos Hidropónicos)."""
    _draw_leaf_shape(draw, x0 + int(s * 0.44), y0 + int(s * 0.55), 160, -45, color, width=9)
    _draw_leaf_shape(draw, x0 + int(s * 0.64), y0 + int(s * 0.44), 120, -15, color, width=8)


def _icon_agro_bottom(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Brote / plántula creciendo sobre montículo de tierra."""
    cx = x0 + s // 2
    base_y = y0 + s - 45
    # Montículo de suelo
    draw.arc((cx - 95, base_y - 38, cx + 95, base_y + 45), start=180, end=360, fill=color, width=9)
    # Tallo vertical
    draw.line([(cx, base_y - 38), (cx, y0 + 85)], fill=color, width=9)
    # Dos hojas del brote
    _draw_leaf_shape(draw, cx - 48, y0 + 165, 95, -150, color, width=7)
    _draw_leaf_shape(draw, cx + 48, y0 + 125, 95, -30, color, width=7)


def _icon_educacion_top(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Libro abierto minimalista."""
    cx, cy = x0 + s // 2, y0 + s // 2 + 15
    w, h = 110, 130
    # Página izquierda y derecha
    draw.polygon(
        [(cx, cy - h // 2 + 15), (cx - w, cy - h // 2), (cx - w, cy + h // 2), (cx, cy + h // 2 + 15)],
        outline=color,
        width=8,
    )
    draw.polygon(
        [(cx, cy - h // 2 + 15), (cx + w, cy - h // 2), (cx + w, cy + h // 2), (cx, cy + h // 2 + 15)],
        outline=color,
        width=8,
    )
    for dy in (-25, 5, 35):
        draw.line([(cx - w + 24, cy + dy), (cx - 20, cy + dy + 10)], fill=color, width=5)
        draw.line([(cx + 20, cy + dy + 10), (cx + w - 24, cy + dy)], fill=color, width=5)


def _icon_educacion_bottom(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Birrete académico / graduación."""
    cx, cy = x0 + s // 2, y0 + s // 2 - 10
    draw.polygon(
        [(cx, cy - 65), (cx + 125, cy), (cx, cy + 65), (cx - 125, cy)],
        outline=color,
        width=8,
    )
    draw.line(
        [(cx - 75, cy + 28), (cx - 75, cy + 95), (cx, cy + 120), (cx + 75, cy + 95), (cx + 75, cy + 28)],
        fill=color,
        width=8,
    )
    draw.line([(cx + 115, cy + 5), (cx + 115, cy + 95)], fill=color, width=6)
    draw.ellipse((cx + 105, cy + 90, cx + 125, cy + 110), fill=color)


def _icon_turismo_top(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Rosa de los vientos / Brújula de guía turístico."""
    cx, cy = x0 + s // 2, y0 + s // 2
    r = 108
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=8)
    # Estrella de 4 puntas
    draw.polygon([(cx, cy - r + 18), (cx + 24, cy), (cx, cy + r - 18), (cx - 24, cy)], outline=color, width=7)
    draw.polygon([(cx - r + 18, cy), (cx, cy - 24), (cx + r - 18, cy), (cx, cy + 24)], outline=color, width=7)
    draw.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=color)


def _icon_turismo_bottom(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Pin de ubicación turística sobre ondas de río / naturaleza."""
    cx, cy = x0 + s // 2, y0 + s // 2 - 20
    r = 62
    draw.arc((cx - r, cy - r, cx + r, cy + r), start=150, end=390, fill=color, width=9)
    draw.line([(cx - int(r * 0.86), cy + 30), (cx, cy + 115), (cx + int(r * 0.86), cy + 30)], fill=color, width=9)
    draw.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), outline=color, width=8)
    # Ondas del río debajo
    for wy in (y0 + s - 65, y0 + s - 38):
        draw.line([(cx - 95, wy), (cx - 45, wy - 12), (cx + 5, wy), (cx + 55, wy - 12), (cx + 95, wy)], fill=color, width=6)


def _icon_ia_top(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Red neuronal / nodos de Inteligencia Artificial."""
    cx, cy = x0 + s // 2, y0 + s // 2
    nodes = [
        (cx, cy),
        (cx - 85, cy - 65),
        (cx + 85, cy - 65),
        (cx - 95, cy + 55),
        (cx + 95, cy + 55),
        (cx, cy - 105),
        (cx, cy + 105),
    ]
    for nx, ny in nodes[1:]:
        draw.line([(cx, cy), (nx, ny)], fill=color, width=6)
    draw.line([nodes[1], nodes[5], nodes[2], nodes[4], nodes[6], nodes[3], nodes[1]], fill=color, width=5)
    for idx, (nx, ny) in enumerate(nodes):
        rad = 26 if idx == 0 else 16
        draw.ellipse((nx - rad, ny - rad, nx + rad, ny + rad), fill=color)


def _icon_ia_bottom(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Microchip / Procesador de IA y Redes."""
    cx, cy = x0 + s // 2, y0 + s // 2
    box = 72
    draw.rounded_rectangle((cx - box, cy - box, cx + box, cy + box), radius=14, outline=color, width=9)
    draw.rectangle((cx - 34, cy - 34, cx + 34, cy + 34), outline=color, width=6)
    for offset in (-42, 0, 42):
        # Pines en los 4 lados
        draw.line([(cx + offset, cy - box), (cx + offset, cy - box - 32)], fill=color, width=7)
        draw.line([(cx + offset, cy + box), (cx + offset, cy + box + 32)], fill=color, width=7)
        draw.line([(cx - box, cy + offset), (cx - box - 32, cy + offset)], fill=color, width=7)
        draw.line([(cx + box, cy + offset), (cx + box + 32, cy + offset)], fill=color, width=7)


def _icon_deportes_top(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Copa / Trofeo deportivo."""
    cx, cy = x0 + s // 2, y0 + s // 2 - 15
    draw.polygon(
        [(cx - 75, cy - 75), (cx + 75, cy - 75), (cx + 55, cy + 25), (cx - 55, cy + 25)],
        outline=color,
        width=9,
    )
    # Asas laterales
    draw.arc((cx - 115, cy - 65, cx - 55, cy + 5), start=90, end=270, fill=color, width=8)
    draw.arc((cx + 55, cy - 65, cx + 115, cy + 5), start=270, end=90, fill=color, width=8)
    # Pedestal
    draw.line([(cx, cy + 25), (cx, cy + 95)], fill=color, width=9)
    draw.line([(cx - 65, cy + 95), (cx + 65, cy + 95)], fill=color, width=11)


def _icon_deportes_bottom(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Medalla deportiva con cintas."""
    cx, cy = x0 + s // 2, y0 + s // 2 + 25
    r = 68
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=9)
    draw.ellipse((cx - r + 18, cy - r + 18, cx + r - 18, cy + r - 18), outline=color, width=5)
    # Cintas superiores en V
    draw.line([(cx - 28, cy - r), (cx - 65, y0 + 50), (cx - 18, y0 + 50), (cx, cy - r)], fill=color, width=7)
    draw.line([(cx + 28, cy - r), (cx + 65, y0 + 50), (cx + 18, y0 + 50), (cx, cy - r)], fill=color, width=7)


def _icon_salud_top(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Cruz de Salud / Primeros Auxilios."""
    cx, cy = x0 + s // 2, y0 + s // 2
    arm, thick = 92, 34
    draw.polygon(
        [
            (cx - thick, cy - arm),
            (cx + thick, cy - arm),
            (cx + thick, cy - thick),
            (cx + arm, cy - thick),
            (cx + arm, cy + thick),
            (cx + thick, cy + thick),
            (cx + thick, cy + arm),
            (cx - thick, cy + arm),
            (cx - thick, cy + thick),
            (cx - arm, cy + thick),
            (cx - arm, cy - thick),
            (cx - thick, cy - thick),
        ],
        outline=color,
        width=9,
    )


def _icon_salud_bottom(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Pulso vital / ECG."""
    cx, cy = x0 + s // 2, y0 + s // 2
    r = 105
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=8)
    pts = [
        (cx - 85, cy),
        (cx - 40, cy),
        (cx - 20, cy - 58),
        (cx + 12, cy + 62),
        (cx + 35, cy - 25),
        (cx + 52, cy),
        (cx + 85, cy),
    ]
    draw.line(pts, fill=color, width=8, joint="curve")


def _icon_emprendedores_top(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Lámpara de ideas / innovación."""
    cx, cy = x0 + s // 2, y0 + s // 2 - 20
    r = 68
    draw.arc((cx - r, cy - r, cx + r, cy + r), start=135, end=45, fill=color, width=9)
    draw.line([(cx - 45, cy + 48), (cx - 32, cy + 92), (cx + 32, cy + 92), (cx + 45, cy + 48)], fill=color, width=8)
    draw.line([(cx - 26, cy + 112), (cx + 26, cy + 112)], fill=color, width=8)
    draw.line([(cx - 16, cy + 130), (cx + 16, cy + 130)], fill=color, width=8)


def _icon_emprendedores_bottom(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Barras de crecimiento y flecha ascendente."""
    base_y = y0 + s - 55
    x_left = x0 + 70
    for idx, bh in enumerate((65, 110, 160)):
        bx = x_left + idx * 72
        draw.rectangle((bx, base_y - bh, bx + 46, base_y), outline=color, width=8)
    draw.line([(x_left - 15, base_y), (x_left + 215, base_y)], fill=color, width=8)
    # Flecha ascendente
    draw.line([(x_left + 10, base_y - 95), (x_left + 175, base_y - 205)], fill=color, width=8)
    draw.line([(x_left + 135, base_y - 205), (x_left + 175, base_y - 205), (x_left + 175, base_y - 165)], fill=color, width=8)


def _icon_cultura_top(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Corchea / Nota musical."""
    cx, cy = x0 + s // 2, y0 + s // 2
    draw.ellipse((cx - 85, cy + 35, cx - 25, cy + 85), outline=color, width=9)
    draw.ellipse((cx + 15, cy + 15, cx + 75, cy + 65), outline=color, width=9)
    draw.line([(cx - 25, cy + 58), (cx - 25, cy - 75), (cx + 75, cy - 95), (cx + 75, cy + 38)], fill=color, width=9)
    draw.line([(cx - 25, cy - 45), (cx + 75, cy - 65)], fill=color, width=8)


def _icon_cultura_bottom(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Estrella / Sol cultural de 8 puntas."""
    cx, cy = x0 + s // 2, y0 + s // 2
    pts = []
    for i in range(16):
        ang = math.radians(i * 22.5)
        r = 108 if i % 2 == 0 else 48
        pts.append((cx + int(r * math.cos(ang)), cy + int(r * math.sin(ang))))
    draw.polygon(pts, outline=color, width=8)
    draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), outline=color, width=6)


def _icon_institucional_top(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Columnas / Edificio Institucional Municipal."""
    cx, cy = x0 + s // 2, y0 + s // 2
    # Frontón triangular
    draw.polygon([(cx, cy - 105), (cx + 115, cy - 40), (cx - 115, cy - 40)], outline=color, width=8)
    # 3 columnas
    for dx in (-70, 0, 70):
        draw.rectangle((cx + dx - 16, cy - 40, cx + dx + 16, cy + 75), outline=color, width=7)
    # Base escalonada
    draw.line([(cx - 115, cy + 75), (cx + 115, cy + 75)], fill=color, width=9)
    draw.line([(cx - 130, cy + 98), (cx + 130, cy + 98)], fill=color, width=11)


def _icon_institucional_bottom(draw: ImageDraw.ImageDraw, x0: int, y0: int, s: int, color: str) -> None:
    """Escudo / Emblema con laureles."""
    cx, cy = x0 + s // 2, y0 + s // 2
    draw.polygon(
        [(cx - 70, cy - 85), (cx + 70, cy - 85), (cx + 70, cy + 10), (cx, cy + 95), (cx - 70, cy + 10)],
        outline=color,
        width=9,
    )
    _draw_leaf_shape(draw, cx, cy - 10, 85, -90, color, width=6)


# ==============================================================================
# Generador del Mosaico Oficial de la Municipalidad de San Roque
# ==============================================================================


def _draw_dot_matrix(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    cols: int,
    rows: int,
    spacing: int,
    radius: int,
    color: str,
) -> None:
    """Dibuja la matriz decorativa de puntos (exactamente como en el certificado impreso)."""
    for r in range(rows):
        for c in range(cols):
            cx = x0 + c * spacing
            cy = y0 + r * spacing
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)


def _draw_muni_mosaic_template(
    out_path: Path,
    *,
    bg_color: str = "#F7F9FB",
    bar_color: str,
    tile_warm_bg: str,
    tile_warm_ray: str,
    tile_mid_bg: str,
    tile_mid_icon_color: str,
    circle_color: str,
    arch_top_color: str,
    arch_mid_color: str,
    tile_bot_bg: str,
    tile_bot_icon_color: str,
    floating_sq_color: str,
    dot_color: str,
    rule_color: str = "#CBD5E1",
    top_icon_fn: Callable[[ImageDraw.ImageDraw, int, int, int, str], None],
    bot_icon_fn: Callable[[ImageDraw.ImageDraw, int, int, int, str], None],
) -> None:
    """Construye la plantilla con el diseño exacto del certificado oficial de San Roque."""
    img = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Franja vertical izquierda con margen blanco exterior (idéntico al impreso)
    draw.rectangle((82, 0, 206, HEIGHT), fill=bar_color)

    # 2. Mosaico Geométrico Bauhaus en la esquina superior derecha (4 columnas x 2 filas + cuadrado flotante)
    tile = 340
    right_margin = 92
    grid_x0 = WIDTH - right_margin - 4 * tile  # 3508 - 92 - 1360 = 2056
    grid_y0 = 0

    c0 = grid_x0
    c1 = grid_x0 + tile
    c2 = grid_x0 + 2 * tile
    c3 = grid_x0 + 3 * tile
    r0 = grid_y0
    r1 = grid_y0 + tile

    # --- Fila Superior (Row 0: y = 0..340) ---
    # Col 0: Sol naciente con rayos geométricos
    _draw_sunburst_tile(draw, c0, r0, tile, tile_warm_bg, tile_warm_ray)

    # Col 1: Cuadrado temático con ícono lineal 1
    draw.rectangle((c1, r0, c1 + tile, r0 + tile), fill=tile_mid_bg)
    top_icon_fn(draw, c1, r0, tile, tile_mid_icon_color)

    # Col 2: Fondo claro con círculo central sólido
    draw.rectangle((c2, r0, c2 + tile, r0 + tile), fill=bg_color)
    cr = 86
    ccx, ccy = c2 + tile // 2, r0 + tile // 2
    draw.ellipse((ccx - cr, ccy - cr, ccx + cr, ccy + cr), fill=circle_color)

    # Col 3: Cuarto de círculo (arco superior derecho)
    draw.rectangle((c3, r0, c3 + tile, r0 + tile), fill=bg_color)
    draw.pieslice(
        (c3 - tile, r0, c3 + tile, r0 + 2 * tile),
        start=270,
        end=360,
        fill=arch_top_color,
    )

    # --- Fila Media (Row 1: y = 340..680) ---
    # Col 2: Cuarto de círculo cálido invertido (anclado arriba-izquierda de la celda)
    draw.rectangle((c2, r1, c2 + tile, r1 + tile), fill=bg_color)
    draw.pieslice(
        (c2 - tile, r1 - tile, c2 + tile, r1 + tile),
        start=0,
        end=90,
        fill=arch_mid_color,
    )

    # Col 3: Cuadrado vivo con ícono lineal 2
    draw.rectangle((c3, r1, c3 + tile, r1 + tile), fill=tile_bot_bg)
    bot_icon_fn(draw, c3, r1, tile, tile_bot_icon_color)

    # --- Cuadrado flotante inferior (Row 2: debajo de Col 3) ---
    sq_size = 180
    sq_x = c3 + 65
    sq_y = r1 + tile + 125
    draw.rectangle((sq_x, sq_y, sq_x + sq_size, sq_y + sq_size), fill=floating_sq_color)

    # 3. Detalles editoriales del certificado real:
    # Línea fina bajo la fecha superior
    draw.line([(320, 312), (1440, 312)], fill=rule_color, width=3)

    # Pequeño emblema de ondas amarillas a la izquierda de "CAPACITACIÓN"
    wx, wy = 262, 505
    draw.line([(wx - 16, wy - 8), (wx + 18, wy - 8)], fill=tile_warm_bg, width=6)
    draw.line([(wx - 22, wy + 4), (wx + 22, wy + 4)], fill=tile_warm_ray, width=6)
    draw.line([(wx - 12, wy + 16), (wx + 14, wy + 16)], fill=tile_warm_bg, width=6)

    # Matriz de puntos junto a "CAPACITACIÓN"
    _draw_dot_matrix(draw, x0=1140, y0=465, cols=8, rows=3, spacing=26, radius=4, color=dot_color)

    # Línea fina divisoria bajo el área del nombre del homenajeado (sobre el cuerpo)
    draw.line([(320, 1345), (1950, 1345)], fill=rule_color, width=3)

    # Matriz de puntos en la zona inferior derecha (sobre los logos)
    _draw_dot_matrix(draw, x0=2680, y0=1665, cols=8, rows=3, spacing=28, radius=4, color=dot_color)

    img.save(out_path, format="PNG", dpi=DPI)


# ==============================================================================
# 3 Plantillas Clásicas Centradas (Conservadas para actos protocolares)
# ==============================================================================


def _draw_corner_ornament(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    dx: int,
    dy: int,
    primary: str,
    accent: str,
    size: int = 120,
) -> None:
    draw.line(
        [(cx, cy + dy * size), (cx, cy), (cx + dx * size, cy)],
        fill=accent,
        width=6,
    )
    offset = 24
    inner = size - 30
    draw.line(
        [
            (cx + dx * offset, cy + dy * inner),
            (cx + dx * offset, cy + dy * offset),
            (cx + dx * inner, cy + dy * offset),
        ],
        fill=primary,
        width=4,
    )
    r = 14
    rx = cx + dx * 48
    ry = cy + dy * 48
    draw.polygon(
        [(rx, ry - r), (rx + r, ry), (rx, ry + r), (rx - r, ry)],
        fill=accent,
    )


def _draw_subtle_watermark_crest(
    img: Image.Image,
    color_rgba: tuple[int, int, int, int],
) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 40

    for radius, width in ((520, 4), (485, 2), (370, 2)):
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=color_rgba,
            width=width,
        )

    for deg in range(0, 360, 15):
        rad = math.radians(deg)
        x1 = cx + int(370 * math.cos(rad))
        y1 = cy + int(370 * math.sin(rad))
        x2 = cx + int(485 * math.cos(rad))
        y2 = cy + int(485 * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=color_rgba, width=2)

    combined = Image.alpha_composite(img.convert("RGBA"), overlay)
    return combined.convert("RGB")


def generate_classic_blue_gold(out_path: Path) -> None:
    bg, navy, gold, soft_gold = "#FAF8F2", "#14325C", "#B08432", "#D4B876"
    img = Image.new("RGB", (WIDTH, HEIGHT), bg)
    img = _draw_subtle_watermark_crest(img, (20, 50, 92, 16))
    draw = ImageDraw.Draw(img)

    draw.rectangle((85, 85, WIDTH - 85, HEIGHT - 85), outline=navy, width=14)
    draw.rectangle((112, 112, WIDTH - 112, HEIGHT - 112), outline=gold, width=5)
    draw.rectangle((132, 132, WIDTH - 132, HEIGHT - 132), outline=soft_gold, width=2)

    _draw_corner_ornament(draw, 155, 155, 1, 1, navy, gold, size=130)
    _draw_corner_ornament(draw, WIDTH - 155, 155, -1, 1, navy, gold, size=130)
    _draw_corner_ornament(draw, 155, HEIGHT - 155, 1, -1, navy, gold, size=130)
    _draw_corner_ornament(draw, WIDTH - 155, HEIGHT - 155, -1, -1, navy, gold, size=130)

    draw.line([(WIDTH // 2 - 420, 535), (WIDTH // 2 + 420, 535)], fill=gold, width=3)
    draw.polygon(
        [(WIDTH // 2, 523), (WIDTH // 2 + 12, 535), (WIDTH // 2, 547), (WIDTH // 2 - 12, 535)],
        fill=navy,
    )
    img.save(out_path, format="PNG", dpi=DPI)


def generate_modern_emerald_slate(out_path: Path) -> None:
    bg, emerald, teal, slate, gold_accent = "#F8FAFC", "#1B4332", "#2D6A4F", "#334155", "#C59B27"
    img = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(img)

    draw.polygon([(0, 0), (620, 0), (0, 620)], fill=emerald)
    draw.polygon([(0, 0), (470, 0), (0, 470)], fill=teal)
    draw.polygon([(0, 0), (140, 0), (0, 140)], fill=gold_accent)

    draw.polygon([(WIDTH, HEIGHT), (WIDTH - 620, HEIGHT), (WIDTH, HEIGHT - 620)], fill=emerald)
    draw.polygon([(WIDTH, HEIGHT), (WIDTH - 470, HEIGHT), (WIDTH, HEIGHT - 470)], fill=teal)
    draw.polygon([(WIDTH, HEIGHT), (WIDTH - 140, HEIGHT), (WIDTH, HEIGHT - 140)], fill=gold_accent)

    draw.rectangle((110, 110, WIDTH - 110, HEIGHT - 110), fill="#FFFFFF", outline=slate, width=4)
    draw.rectangle((130, 130, WIDTH - 130, HEIGHT - 130), outline=gold_accent, width=2)
    draw.rectangle((WIDTH // 2 - 360, 210, WIDTH // 2 + 360, 218), fill=emerald)
    draw.rectangle((WIDTH // 2 - 140, 210, WIDTH // 2 + 140, 218), fill=gold_accent)
    draw.line([(WIDTH // 2 - 380, 775), (WIDTH // 2 + 380, 775)], fill=teal, width=3)
    img.save(out_path, format="PNG", dpi=DPI)


def generate_solemn_burgundy_gold(out_path: Path) -> None:
    bg, burgundy, dark_burgundy, gold, soft_gold = "#FBF9F5", "#6B1D2F", "#4A101D", "#9E7B2F", "#D6BE8A"
    img = Image.new("RGB", (WIDTH, HEIGHT), bg)
    img = _draw_subtle_watermark_crest(img, (107, 29, 47, 15))
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, 56, HEIGHT), fill=burgundy)
    draw.rectangle((WIDTH - 56, 0, WIDTH, HEIGHT), fill=burgundy)
    draw.rectangle((56, 0, 70, HEIGHT), fill=gold)
    draw.rectangle((WIDTH - 70, 0, WIDTH - 56, HEIGHT), fill=gold)

    draw.rectangle((120, 95, WIDTH - 120, HEIGHT - 95), outline=dark_burgundy, width=8)
    draw.rectangle((140, 115, WIDTH - 140, HEIGHT - 115), outline=gold, width=4)
    draw.rectangle((156, 131, WIDTH - 156, HEIGHT - 131), outline=soft_gold, width=2)

    _draw_corner_ornament(draw, 175, 150, 1, 1, burgundy, gold, size=115)
    _draw_corner_ornament(draw, WIDTH - 175, 150, -1, 1, burgundy, gold, size=115)
    _draw_corner_ornament(draw, 175, HEIGHT - 150, 1, -1, burgundy, gold, size=115)
    _draw_corner_ornament(draw, WIDTH - 175, HEIGHT - 150, -1, -1, burgundy, gold, size=115)

    draw.line([(WIDTH // 2 - 460, 535), (WIDTH // 2 + 460, 535)], fill=gold, width=3)
    draw.ellipse((WIDTH // 2 - 10, 525, WIDTH // 2 + 10, 545), fill=burgundy, outline=gold, width=2)
    img.save(out_path, format="PNG", dpi=DPI)


# ==============================================================================
# 10 Plantillas Oficiales Muni San Roque (Mosaico Temático)
# ==============================================================================


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Agro, Cultivos e Hidroponía (idéntica al certificado real de la foto)
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_agro_cultivos.png",
        bar_color="#4D7C2B",
        tile_warm_bg="#E59A28",
        tile_warm_ray="#F2C94C",
        tile_mid_bg="#558B2F",
        tile_mid_icon_color="#8BC34A",
        circle_color="#7CB518",
        arch_top_color="#689F38",
        arch_mid_color="#E59A28",
        tile_bot_bg="#8BC34A",
        tile_bot_icon_color="#4D7C2B",
        floating_sq_color="#689F38",
        dot_color="#D99B4E",
        top_icon_fn=_icon_agro_top,
        bot_icon_fn=_icon_agro_bottom,
    )

    # 2. Educación y Capacitación Docente
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_educacion_docente.png",
        bar_color="#1B4965",
        tile_warm_bg="#E59A28",
        tile_warm_ray="#F4D35E",
        tile_mid_bg="#1E6091",
        tile_mid_icon_color="#76C893",
        circle_color="#2B9EB3",
        arch_top_color="#1E6091",
        arch_mid_color="#E59A28",
        tile_bot_bg="#52B69A",
        tile_bot_icon_color="#1B4965",
        floating_sq_color="#2B9EB3",
        dot_color="#C59B27",
        top_icon_fn=_icon_educacion_top,
        bot_icon_fn=_icon_educacion_bottom,
    )

    # 3. Turismo, Guías Turísticos y Naturaleza
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_turismo_guias.png",
        bar_color="#116A7B",
        tile_warm_bg="#F48C06",
        tile_warm_ray="#FFBA08",
        tile_mid_bg="#148F77",
        tile_mid_icon_color="#A3E4D7",
        circle_color="#2EC4B6",
        arch_top_color="#116A7B",
        arch_mid_color="#F48C06",
        tile_bot_bg="#48CAE4",
        tile_bot_icon_color="#0B4F6C",
        floating_sq_color="#2EC4B6",
        dot_color="#E09F3E",
        top_icon_fn=_icon_turismo_top,
        bot_icon_fn=_icon_turismo_bottom,
    )

    # 4. Inteligencia Artificial, Redes y Tecnología
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_tecnologia_redes.png",
        bar_color="#1E3A8A",
        tile_warm_bg="#F59E0B",
        tile_warm_ray="#FDE047",
        tile_mid_bg="#1D4ED8",
        tile_mid_icon_color="#67E8F9",
        circle_color="#06B6D4",
        arch_top_color="#2563EB",
        arch_mid_color="#F59E0B",
        tile_bot_bg="#22D3EE",
        tile_bot_icon_color="#1E3A8A",
        floating_sq_color="#0284C7",
        dot_color="#38BDF8",
        top_icon_fn=_icon_ia_top,
        bot_icon_fn=_icon_ia_bottom,
    )

    # 5. Deportes, Recreación y Vida Sana
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_deportes_recreacion.png",
        bar_color="#1D3557",
        tile_warm_bg="#F77F00",
        tile_warm_ray="#FCBF49",
        tile_mid_bg="#0077B6",
        tile_mid_icon_color="#90E0EF",
        circle_color="#F77F00",
        arch_top_color="#0077B6",
        arch_mid_color="#FCBF49",
        tile_bot_bg="#48CAE4",
        tile_bot_icon_color="#1D3557",
        floating_sq_color="#0096C7",
        dot_color="#F77F00",
        top_icon_fn=_icon_deportes_top,
        bot_icon_fn=_icon_deportes_bottom,
    )

    # 6. Salud, Bienestar y Primeros Auxilios (RCP)
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_comunidad_salud.png",
        bar_color="#0F766E",
        tile_warm_bg="#E59A28",
        tile_warm_ray="#FDE047",
        tile_mid_bg="#0D9488",
        tile_mid_icon_color="#99F6E4",
        circle_color="#10B981",
        arch_top_color="#0F766E",
        arch_mid_color="#E59A28",
        tile_bot_bg="#34D399",
        tile_bot_icon_color="#065F46",
        floating_sq_color="#10B981",
        dot_color="#0D9488",
        top_icon_fn=_icon_salud_top,
        bot_icon_fn=_icon_salud_bottom,
    )

    # 7. Emprendedores, Oficios y Ferias
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_emprendimiento.png",
        bar_color="#9A3412",
        tile_warm_bg="#EA580C",
        tile_warm_ray="#FBBF24",
        tile_mid_bg="#1E3A5F",
        tile_mid_icon_color="#FDBA74",
        circle_color="#EA580C",
        arch_top_color="#C2410C",
        arch_mid_color="#F59E0B",
        tile_bot_bg="#FDBA74",
        tile_bot_icon_color="#7C2D12",
        floating_sq_color="#EA580C",
        dot_color="#D97706",
        top_icon_fn=_icon_emprendedores_top,
        bot_icon_fn=_icon_emprendedores_bottom,
    )

    # 8. Cultura, Arte y Música
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_cultura_arte.png",
        bar_color="#6B21A8",
        tile_warm_bg="#F97316",
        tile_warm_ray="#FACC15",
        tile_mid_bg="#7E22CE",
        tile_mid_icon_color="#E9D5FF",
        circle_color="#F97316",
        arch_top_color="#9333EA",
        arch_mid_color="#F59E0B",
        tile_bot_bg="#C084FC",
        tile_bot_icon_color="#4C1D95",
        floating_sq_color="#9333EA",
        dot_color="#D97706",
        top_icon_fn=_icon_cultura_top,
        bot_icon_fn=_icon_cultura_bottom,
    )

    # 9. Ambiente, Ecología y Espacios Verdes
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_ambiente_ecologia.png",
        bar_color="#1B4332",
        tile_warm_bg="#D97706",
        tile_warm_ray="#FCD34D",
        tile_mid_bg="#2D6A4F",
        tile_mid_icon_color="#95D5B2",
        circle_color="#40916C",
        arch_top_color="#2D6A4F",
        arch_mid_color="#D97706",
        tile_bot_bg="#74C69D",
        tile_bot_icon_color="#1B4332",
        floating_sq_color="#52B788",
        dot_color="#B7950B",
        top_icon_fn=_icon_agro_top,
        bot_icon_fn=_icon_turismo_bottom,
    )

    # 10. Gestión Municipal y Cursos Generales
    _draw_muni_mosaic_template(
        OUT_DIR / "plantilla_muni_general.png",
        bar_color="#14325C",
        tile_warm_bg="#D97706",
        tile_warm_ray="#FCD34D",
        tile_mid_bg="#1E40AF",
        tile_mid_icon_color="#93C5FD",
        circle_color="#0284C7",
        arch_top_color="#1E3A8A",
        arch_mid_color="#D97706",
        tile_bot_bg="#60A5FA",
        tile_bot_icon_color="#14325C",
        floating_sq_color="#2563EB",
        dot_color="#C59B27",
        top_icon_fn=_icon_institucional_top,
        bot_icon_fn=_icon_institucional_bottom,
    )

    # 11-13. Las 3 plantillas clásicas
    generate_classic_blue_gold(OUT_DIR / "plantilla_clasica_azul_oro.png")
    generate_modern_emerald_slate(OUT_DIR / "plantilla_moderna_pizarra.png")
    generate_solemn_burgundy_gold(OUT_DIR / "plantilla_solemne_borgona.png")

    # 14. Generar ícono oficial de Windows (assets/app_icon.ico) a partir del escudo municipal
    assets_dir = OUT_DIR.parent
    escudo_path = assets_dir / "logos" / "logo_san_roque_escudo.png"
    ico_path = assets_dir / "app_icon.ico"
    if escudo_path.is_file():
        with Image.open(escudo_path) as escudo:
            rgba = escudo.convert("RGBA")
            side = max(rgba.width, rgba.height, 256)
            square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            square.alpha_composite(
                rgba,
                dest=((side - rgba.width) // 2, (side - rgba.height) // 2),
            )
            square = square.resize((256, 256), Image.Resampling.LANCZOS)
            square.save(
                ico_path,
                format="ICO",
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
            )
        print(f"Ícono de aplicación generado en {ico_path}")

    print(f"13 plantillas institucionales generadas en {OUT_DIR}")


if __name__ == "__main__":
    main()
