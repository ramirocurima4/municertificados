"""Componentes visuales, paleta institucional y selector de colores para CustomTkinter."""

from __future__ import annotations

from tkinter import colorchooser
from typing import Callable

import customtkinter as ctk

# Paleta Institucional (Dark Mode por defecto — customtkinter-desktop-ui.md)
BG_WINDOW = "#0B1120"
BG_PANEL = "#111827"
BG_CARD = "#1E293B"
BORDER_SUBTLE = "#334155"

ACCENT_PRIMARY = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
ACCENT_GOLD = "#D4AF37"

COLOR_SUCCESS = "#10B981"
COLOR_WARNING = "#F59E0B"
COLOR_DANGER = "#EF4444"

TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#94A3B8"

# 12 colores institucionales y temáticos para el selector rápido
INSTITUTIONAL_SWATCHES: list[tuple[str, str]] = [
    ("Azul Marino Muni", "#14325C"),
    ("Celeste Institucional", "#0284C7"),
    ("Dorado", "#B8860B"),
    ("Verde Agro", "#2E7D32"),
    ("Amarillo Ocre", "#D97706"),
    ("Turquesa Tech", "#0D9488"),
    ("Naranja Emprendedor", "#EA580C"),
    ("Bordó Solemne", "#6B1D2F"),
    ("Verde Agua", "#059669"),
    ("Gris Pizarra", "#334155"),
    ("Negro", "#111827"),
    ("Blanco", "#FFFFFF"),
]


class SectionCard(ctk.CTkFrame):
    """Tarjeta contenedora con bordes sutiles y radios consistentes."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        kwargs.setdefault("fg_color", BG_CARD)
        kwargs.setdefault("border_color", BORDER_SUBTLE)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 8)
        super().__init__(master, **kwargs)


class StatusBanner(ctk.CTkFrame):
    """Banner de retroalimentación semántica no bloqueante."""

    _STYLES = {
        "info": ("#1E3A8A", "#93C5FD"),
        "success": ("#064E3B", "#6EE7B7"),
        "warning": ("#78350F", "#FCD34D"),
        "error": ("#7F1D1D", "#FCA5A5"),
    }

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, corner_radius=6, height=34, fg_color=BG_CARD)
        self.grid_propagate(False)
        self.label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        self.label.pack(fill="both", expand=True, padx=12, pady=4)
        self._clear_job: str | None = None

    def show(self, message: str, level: str = "info", auto_clear_ms: int = 5000) -> None:
        bg, fg = self._STYLES.get(level, self._STYLES["info"])
        self.configure(fg_color=bg)
        self.label.configure(text=message, text_color=fg)
        if self._clear_job is not None:
            self.after_cancel(self._clear_job)
            self._clear_job = None
        if auto_clear_ms > 0:
            self._clear_job = self.after(auto_clear_ms, self.clear)

    def clear(self) -> None:
        self.configure(fg_color="transparent")
        self.label.configure(text="")
        self._clear_job = None


class ColorPickerButton(ctk.CTkFrame):
    """Selector visual de color con muestra actual, 12 swatches institucionales y diálogo nativo."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        initial_color: str = "#14325C",
        on_change: Callable[[str], None] | None = None,
        label_text: str = "Color",
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._color = self._normalize_hex(initial_color)
        self._on_change = on_change

        self.grid_columnconfigure(1, weight=1)

        # Fila superior: cuadradito de color actual + código Hex + botón "🎨 Más colores..."
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(2, 4))

        ctk.CTkLabel(
            top_row,
            text=f"{label_text}:",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 6))

        self.preview_box = ctk.CTkButton(
            top_row,
            text="",
            width=26,
            height=24,
            corner_radius=4,
            fg_color=self._color,
            hover_color=self._color,
            border_width=1,
            border_color="#94A3B8",
            command=self._open_color_dialog,
        )
        self.preview_box.pack(side="left", padx=(0, 6))

        self.lbl_hex = ctk.CTkLabel(
            top_row,
            text=self._color,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_PRIMARY,
            width=64,
            anchor="w",
        )
        self.lbl_hex.pack(side="left", padx=(0, 6))

        self.btn_more = ctk.CTkButton(
            top_row,
            text="🎨 Más colores...",
            height=24,
            width=115,
            corner_radius=5,
            fg_color="#334155",
            hover_color="#475569",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_color_dialog,
        )
        self.btn_more.pack(side="right")

        # Fila inferior: paleta rápida clicable de 12 swatches institucionales
        swatches_row = ctk.CTkFrame(self, fg_color="transparent")
        swatches_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 2))

        for idx, (_name, hex_val) in enumerate(INSTITUTIONAL_SWATCHES):
            btn = ctk.CTkButton(
                swatches_row,
                text="",
                width=22,
                height=20,
                corner_radius=4,
                fg_color=hex_val,
                hover_color=hex_val,
                border_width=1,
                border_color="#64748B",
                command=lambda c=hex_val: self._select_color(c),
            )
            btn.grid(row=0, column=idx, padx=2, pady=1)

    @staticmethod
    def _normalize_hex(val: str) -> str:
        cleaned = str(val or "").strip().upper()
        if cleaned.startswith("#") and len(cleaned) in (4, 7):
            return cleaned
        return "#14325C"

    def get(self) -> str:
        return self._color

    def set(self, hex_color: str, *, trigger: bool = False) -> None:
        self._color = self._normalize_hex(hex_color)
        self.preview_box.configure(fg_color=self._color, hover_color=self._color)
        self.lbl_hex.configure(text=self._color)
        if trigger and self._on_change is not None:
            self._on_change(self._color)

    def _select_color(self, hex_color: str) -> None:
        self.set(hex_color, trigger=True)

    def _open_color_dialog(self) -> None:
        _, chosen_hex = colorchooser.askcolor(
            color=self._color, title="Seleccionar Color Institucional"
        )
        if chosen_hex:
            self.set(chosen_hex.upper(), trigger=True)


def make_primary_button(
    master: ctk.CTkBaseClass, text: str, command=None, **kwargs
) -> ctk.CTkButton:
    kwargs.setdefault("fg_color", ACCENT_PRIMARY)
    kwargs.setdefault("hover_color", ACCENT_HOVER)
    kwargs.setdefault("text_color", TEXT_PRIMARY)
    kwargs.setdefault("corner_radius", 6)
    kwargs.setdefault("height", 36)
    kwargs.setdefault("font", ctk.CTkFont(size=13, weight="bold"))
    return ctk.CTkButton(master, text=text, command=command, **kwargs)


def make_secondary_button(
    master: ctk.CTkBaseClass, text: str, command=None, **kwargs
) -> ctk.CTkButton:
    kwargs.setdefault("fg_color", "#334155")
    kwargs.setdefault("hover_color", "#475569")
    kwargs.setdefault("text_color", TEXT_PRIMARY)
    kwargs.setdefault("corner_radius", 6)
    kwargs.setdefault("height", 36)
    kwargs.setdefault("font", ctk.CTkFont(size=12, weight="bold"))
    return ctk.CTkButton(master, text=text, command=command, **kwargs)


def make_entry(master: ctk.CTkBaseClass, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
    kwargs.setdefault("height", 36)
    kwargs.setdefault("corner_radius", 6)
    kwargs.setdefault("fg_color", BG_PANEL)
    kwargs.setdefault("border_color", BORDER_SUBTLE)
    kwargs.setdefault("text_color", TEXT_PRIMARY)
    return ctk.CTkEntry(master, placeholder_text=placeholder, **kwargs)
