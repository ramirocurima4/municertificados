"""Estudio Visual de Diplomas con Modo Simple guiado y Modo Avanzado desplegable."""

from __future__ import annotations

import copy
import threading
from pathlib import Path
from tkinter import filedialog, simpledialog
from typing import Any, Callable

import customtkinter as ctk

from src.config import FILEDIALOG_ASSET_TYPES
from src.database.repositories import CourseRepository, TemplateRepository
from src.services.cert_engine import (
    LOGO_SLOT_KEYS,
    font_display_name,
    list_available_fonts,
    list_institutional_logos,
    render_preview_image,
    resolve_x_px,
    resolve_y_px,
)
from src.services.file_manager import import_asset_to_local_store
from src.ui.components.widgets import (
    ACCENT_GOLD,
    BG_PANEL,
    COLOR_SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    ColorPickerButton,
    SectionCard,
    make_entry,
    make_primary_button,
    make_secondary_button,
)

LOGO_TAB_NAMES = ["Logo 1", "Logo 2", "Logo 3", "Logo 4"]
LOGO_TAB_TO_KEY = {
    "Logo 1": "main",
    "Logo 2": "secondary",
    "Logo 3": "logo_3",
    "Logo 4": "logo_4",
}
LOGO_DESCRIPTIONS = {
    "main": "Logo 1 (ej. #Avanzamos Juntos)",
    "secondary": "Logo 2 (ej. Escudo San Roque Municipio)",
    "logo_3": "Logo 3 (ej. Dirección / Área Municipal)",
    "logo_4": "Logo 4 (ej. Institución: INTA / ISFD)",
}


class DesignerView(ctk.CTkFrame):
    """Estudio visual simplificado con plantillas temáticas listas para usar y panel avanzado opcional."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        get_active_course_id: Callable[[], int | None],
        notify: Callable[[str, str], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.get_active_course_id = get_active_course_id
        self.notify = notify

        self.template_repo = TemplateRepository()
        self.course_repo = CourseRepository()

        self._templates_by_name: dict[str, dict[str, Any]] = {}
        self._current_template: dict[str, Any] | None = None
        self._font_display_to_file: dict[str, str] = {}
        self._font_file_to_display: dict[str, str] = {}
        self._inst_logo_label_to_path: dict[str, str] = {}
        self._debounce_job: str | None = None
        self._render_seq: int = 0
        self._loading_ui: bool = False
        self._advanced_open: bool = False
        self.preview_ctk_image: ctk.CTkImage | None = None

        self.grid_columnconfigure(0, weight=0, minsize=455)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._load_font_catalog()
        self._build_controls_panel()
        self._build_preview_panel()

    def _load_font_catalog(self) -> None:
        fonts = list_available_fonts()
        self._font_display_to_file = {disp: fname for disp, fname in fonts}
        self._font_file_to_display = {fname: disp for disp, fname in fonts}
        inst_logos = list_institutional_logos()
        self._inst_logo_label_to_path = {label: path for label, path in inst_logos}

    @staticmethod
    def _align_to_ui(align: str) -> str:
        return "Izquierda" if str(align).lower() == "left" else "Centro"

    @staticmethod
    def _ui_to_align(ui_val: str) -> str:
        return "left" if str(ui_val).lower().startswith("izq") else "center"

    def _build_controls_panel(self) -> None:
        card = SectionCard(self)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="Diseño del Certificado",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))

        self.scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=6, pady=4)
        self.scroll.grid_columnconfigure(0, weight=1)

        # ======================================================================
        # 1. PLANTILLA TEMÁTICA (Listas para usar por rubro)
        # ======================================================================
        self._add_section_title("1. Elegir Plantilla Temática")
        self.opt_template = ctk.CTkOptionMenu(
            self.scroll,
            values=["Cargando..."],
            command=self._on_template_selected,
            height=36,
            corner_radius=6,
            fg_color=BG_PANEL,
        )
        self.opt_template.pack(fill="x", padx=8, pady=(2, 6))

        tpl_btns = ctk.CTkFrame(self.scroll, fg_color="transparent")
        tpl_btns.pack(fill="x", padx=8, pady=(0, 6))
        tpl_btns.grid_columnconfigure((0, 1), weight=1)

        self.btn_save_tpl = make_primary_button(
            tpl_btns, "Guardar Cambios", command=self._save_current_template
        )
        self.btn_save_tpl.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=(0, 6))

        make_secondary_button(
            tpl_btns,
            "Guardar como Nueva",
            fg_color=COLOR_SUCCESS,
            hover_color="#059669",
            command=self._save_as_new_template,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=(0, 6))

        make_secondary_button(
            tpl_btns,
            "Cargar Fondo Propio (.pdf/.png/.jpg/.webp)",
            height=30,
            command=self._pick_background,
        ).grid(row=1, column=0, columnspan=2, sticky="ew")

        # ======================================================================
        # 2. LOGOS DEL PIE (Hasta 4 logos en pestañas limpias)
        # ======================================================================
        self._add_section_title("2. Logos Institucionales (Hasta 4 Logos)")
        logos_container = ctk.CTkFrame(self.scroll, fg_color=BG_PANEL, corner_radius=6)
        logos_container.pack(fill="x", padx=8, pady=4)

        preset_row = ctk.CTkFrame(logos_container, fg_color="transparent")
        preset_row.pack(fill="x", padx=8, pady=(6, 4))
        preset_row.grid_columnconfigure((0, 1, 2), weight=1)

        make_secondary_button(
            preset_row,
            "Abajo Derecha",
            height=26,
            command=lambda: self._apply_logos_preset("bottom_right_row"),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        make_secondary_button(
            preset_row,
            "Arriba Centro",
            height=26,
            command=lambda: self._apply_logos_preset("top_center"),
        ).grid(row=0, column=1, sticky="ew", padx=2)
        make_secondary_button(
            preset_row,
            "Arriba Izq.",
            height=26,
            command=lambda: self._apply_logos_preset("top_left"),
        ).grid(row=0, column=2, sticky="ew", padx=(2, 0))

        self.seg_logo_tab = ctk.CTkSegmentedButton(
            logos_container,
            values=LOGO_TAB_NAMES,
            command=self._switch_logo_tab,
            height=30,
        )
        self.seg_logo_tab.set("Logo 1")
        self.seg_logo_tab.pack(fill="x", padx=8, pady=(4, 4))

        self.logo_frames: dict[str, ctk.CTkFrame] = {}
        self.logo_widgets: dict[str, dict[str, Any]] = {}
        for slot_key in LOGO_SLOT_KEYS:
            frame, widgets = self._build_single_logo_pane(
                logos_container, slot_key, LOGO_DESCRIPTIONS[slot_key]
            )
            self.logo_frames[slot_key] = frame
            self.logo_widgets[slot_key] = widgets
        self._switch_logo_tab("Logo 1")

        # ======================================================================
        # 3. TEXTOS PRINCIPALES Y COLOR DE FRANJA DEL CURSO
        # ======================================================================
        self._add_section_title("3. Textos del Certificado")
        simple_text_box = ctk.CTkFrame(self.scroll, fg_color=BG_PANEL, corner_radius=6)
        simple_text_box.pack(fill="x", padx=8, pady=4)

        font_names = list(self._font_display_to_file.keys()) or ["Noto Sans Regular"]
        self.block_widgets: dict[str, dict[str, Any]] = {}

        # Creamos los bloques; sus entradas de texto viven en la vista simple,
        # y sus controles de fuente/X/Y/color viven en el panel avanzado desplegable.
        self.adv_container = ctk.CTkFrame(self.scroll, fg_color="transparent")

        self.block_widgets["header_institution"] = self._create_split_text_block(
            simple_parent=simple_text_box,
            adv_parent=self.adv_container,
            label="Fecha y Lugar Superior (ej. {lugar} {fecha})",
            font_names=font_names,
        )
        self.block_widgets["header_area"] = self._create_split_text_block(
            simple_parent=simple_text_box,
            adv_parent=self.adv_container,
            label="Tipo de Evento (ej. {TIPO_EVENTO} o CAPACITACIÓN)",
            font_names=font_names,
        )
        self.course_banner_widgets = self._create_split_course_banner(
            simple_parent=simple_text_box,
            adv_parent=self.adv_container,
            font_names=font_names,
        )
        self.block_widgets["title"] = self._create_split_text_block(
            simple_parent=simple_text_box,
            adv_parent=self.adv_container,
            label="Título Principal",
            font_names=font_names,
        )
        self.block_widgets["subtitle"] = self._create_split_text_block(
            simple_parent=simple_text_box,
            adv_parent=self.adv_container,
            label="Subtítulo",
            font_names=font_names,
        )

        self.sw_show_dni = ctk.CTkSwitch(
            simple_text_box,
            text="Mostrar D.N.I. debajo del nombre",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._schedule_preview,
        )
        self.sw_show_dni.select()
        self.sw_show_dni.pack(fill="x", padx=10, pady=(6, 4))

        self.body_widgets = self._create_split_body_block(
            simple_parent=simple_text_box,
            adv_parent=self.adv_container,
            font_names=font_names,
        )
        self.name_widgets = self._create_split_recipient_name_block(
            adv_parent=self.adv_container,
            font_names=font_names,
        )
        self.block_widgets["recipient_dni"] = self._create_split_text_block(
            simple_parent=self.adv_container,
            adv_parent=self.adv_container,
            label="Texto DNI (vacío si no se desea mostrar en el diploma)",
            font_names=font_names,
        )
        self.block_widgets["footer_date"] = self._create_split_text_block(
            simple_parent=self.adv_container,
            adv_parent=self.adv_container,
            label="Texto Pie Adicional (opcional)",
            font_names=font_names,
        )

        # ======================================================================
        # 4. FIRMAS Y AUTORIDADES (Pestañas Firma 1 / Firma 2)
        # ======================================================================
        self._add_section_title("4. Firma y Cargo de Autoridad")
        sigs_container = ctk.CTkFrame(self.scroll, fg_color=BG_PANEL, corner_radius=6)
        sigs_container.pack(fill="x", padx=8, pady=4)

        self.seg_sig_tab = ctk.CTkSegmentedButton(
            sigs_container,
            values=["Firma 1 (Principal)", "Firma 2 (Opcional)"],
            command=self._switch_sig_tab,
            height=30,
        )
        self.seg_sig_tab.set("Firma 1 (Principal)")
        self.seg_sig_tab.pack(fill="x", padx=8, pady=(8, 4))

        self.sig_frames: list[ctk.CTkFrame] = []
        self.sig_widgets: list[dict[str, Any]] = []
        for idx in range(2):
            s_frame, s_widgets = self._build_signature_pane(sigs_container, idx)
            self.sig_frames.append(s_frame)
            self.sig_widgets.append(s_widgets)
        self._switch_sig_tab("Firma 1 (Principal)")

        # ======================================================================
        # 5. BOTÓN DESPLEGABLE DE AJUSTES AVANZADOS (Oculto por defecto)
        # ======================================================================
        self.btn_toggle_adv = make_secondary_button(
            self.scroll,
            "⚙️ Mostrar Ajustes Avanzados (Posiciones X/Y, Fuentes y Colores)",
            height=34,
            command=self._toggle_advanced_panel,
        )
        self.btn_toggle_adv.pack(fill="x", padx=8, pady=(14, 6))

        # Barra de alineación rápida dentro del contenedor avanzado
        align_bar = ctk.CTkFrame(self.adv_container, fg_color=BG_PANEL, corner_radius=6)
        align_bar.pack(fill="x", padx=8, pady=(4, 6))
        align_bar.grid_columnconfigure((0, 1), weight=1)

        make_secondary_button(
            align_bar,
            "Alinear Todo a la Izquierda (x=320)",
            height=28,
            command=lambda: self._apply_global_alignment("left"),
        ).grid(row=0, column=0, sticky="ew", padx=(6, 3), pady=6)

        make_secondary_button(
            align_bar,
            "Centrar Todo Clásico (x=1754)",
            height=28,
            command=lambda: self._apply_global_alignment("center"),
        ).grid(row=0, column=1, sticky="ew", padx=(3, 6), pady=6)

    def _add_section_title(self, text: str) -> None:
        ctk.CTkLabel(
            self.scroll,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        ).pack(fill="x", padx=8, pady=(10, 3))

    def _switch_logo_tab(self, tab_name: str) -> None:
        active_key = LOGO_TAB_TO_KEY.get(tab_name, "main")
        for k, frame in self.logo_frames.items():
            if k == active_key:
                frame.pack(fill="x", padx=6, pady=(0, 6))
            else:
                frame.pack_forget()

    def _switch_sig_tab(self, tab_name: str) -> None:
        active_idx = 0 if "1" in tab_name else 1
        for idx, frame in enumerate(self.sig_frames):
            if idx == active_idx:
                frame.pack(fill="x", padx=6, pady=(0, 6))
            else:
                frame.pack_forget()

    def _toggle_advanced_panel(self) -> None:
        self._advanced_open = not self._advanced_open
        if self._advanced_open:
            self.btn_toggle_adv.configure(
                text="🔼 Ocultar Ajustes Avanzados (Posiciones X/Y, Fuentes y Colores)"
            )
            self.adv_container.pack(fill="x", padx=0, pady=(0, 10))
        else:
            self.btn_toggle_adv.configure(
                text="⚙️ Mostrar Ajustes Avanzados (Posiciones X/Y, Fuentes y Colores)"
            )
            self.adv_container.pack_forget()

    def _build_single_logo_pane(
        self, parent: ctk.CTkFrame, slot_key: str, title: str
    ) -> tuple[ctk.CTkFrame, dict[str, Any]]:
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            box,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=(2, 2))

        lbl_file = ctk.CTkLabel(
            box,
            text="(Sin archivo)",
            font=ctk.CTkFont(size=10),
            text_color=TEXT_SECONDARY,
            anchor="e",
        )
        lbl_file.grid(row=0, column=2, sticky="e", padx=6, pady=(2, 2))

        inst_options = ["Logo Oficial..."] + list(self._inst_logo_label_to_path.keys())
        opt_inst_logo = ctk.CTkOptionMenu(
            box,
            values=inst_options,
            height=28,
            corner_radius=6,
            command=lambda val, s=slot_key: self._on_pick_institutional_logo(s, val),
        )
        opt_inst_logo.set("Logo Oficial...")
        opt_inst_logo.grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=(2, 4))

        make_secondary_button(
            box,
            "Examinar archivo (.pdf/.png/.jpg/.webp)",
            height=28,
            command=lambda s=slot_key: self._pick_logo(s),
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=(6, 4), pady=(2, 4))

        make_secondary_button(
            box,
            "Quitar",
            width=70,
            height=28,
            command=lambda s=slot_key: self._clear_logo(s),
        ).grid(row=2, column=2, sticky="ew", padx=(4, 6), pady=(2, 4))

        sw_bg = ctk.CTkSwitch(
            box,
            text="Quitar fondo blanco (ideal logos JPG)",
            font=ctk.CTkFont(size=11),
            command=self._schedule_preview,
        )
        sw_bg.grid(row=3, column=0, columnspan=3, sticky="w", padx=6, pady=(2, 2))

        sw_tint = ctk.CTkSwitch(
            box,
            text="Teñir logo del color de la plantilla / elegido",
            font=ctk.CTkFont(size=11),
            command=self._schedule_preview,
        )
        sw_tint.grid(row=4, column=0, columnspan=3, sticky="w", padx=6, pady=(2, 2))

        tint_color_picker = ColorPickerButton(
            box,
            initial_color="#14325C",
            label_text="Color Logo",
            on_change=lambda _c: self._schedule_preview(),
        )
        tint_color_picker.grid(row=5, column=0, columnspan=3, sticky="ew", padx=6, pady=(0, 4))

        size_row = ctk.CTkFrame(box, fg_color="transparent")
        size_row.grid(row=6, column=0, columnspan=3, sticky="ew", padx=6, pady=2)
        size_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            size_row, text="Tamaño (px):", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY
        ).grid(row=0, column=0, padx=(0, 6))

        entry_size = make_entry(size_row, "290", width=58, height=28)
        entry_size.grid(row=0, column=2, padx=(6, 0))

        def _on_size_slider(val: float) -> None:
            if self._loading_ui:
                return
            self._set_entry(entry_size, str(int(round(val))))
            self._schedule_preview()

        slider_size = ctk.CTkSlider(
            size_row, from_=80, to=600, number_of_steps=130, command=_on_size_slider
        )
        slider_size.grid(row=0, column=1, sticky="ew")
        entry_size.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        xy_row = ctk.CTkFrame(box, fg_color="transparent")
        xy_row.grid(row=7, column=0, columnspan=3, sticky="ew", padx=6, pady=(2, 4))
        xy_row.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(xy_row, text="Pos X:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).grid(
            row=0, column=0, padx=(0, 4)
        )
        entry_x = make_entry(xy_row, "1660", width=64, height=28)
        entry_x.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        entry_x.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        ctk.CTkLabel(xy_row, text="Pos Y:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).grid(
            row=0, column=2, padx=(0, 4)
        )
        entry_y = make_entry(xy_row, "2110", width=64, height=28)
        entry_y.grid(row=0, column=3, sticky="ew")
        entry_y.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        return box, {
            "lbl_file": lbl_file,
            "opt_inst_logo": opt_inst_logo,
            "remove_bg": sw_bg,
            "tint_enabled": sw_tint,
            "tint_color": tint_color_picker,
            "slider_size": slider_size,
            "entry_size": entry_size,
            "entry_x": entry_x,
            "entry_y": entry_y,
        }

    def _create_split_text_block(
        self,
        *,
        simple_parent: ctk.CTkFrame,
        adv_parent: ctk.CTkFrame,
        label: str,
        font_names: list[str],
    ) -> dict[str, Any]:
        ctk.CTkLabel(
            simple_parent,
            text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(6, 1))

        entry_text = make_entry(simple_parent, label, height=30)
        entry_text.pack(fill="x", padx=10, pady=(0, 4))
        entry_text.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        adv_box = ctk.CTkFrame(adv_parent, fg_color=BG_PANEL, corner_radius=6)
        adv_box.pack(fill="x", padx=8, pady=3)
        ctk.CTkLabel(
            adv_box,
            text=f"Ajustes: {label}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(4, 2))
        controls = self._build_alignment_xy_font_controls(adv_box, font_names)
        return {"text": entry_text, **controls}

    def _create_split_course_banner(
        self,
        *,
        simple_parent: ctk.CTkFrame,
        adv_parent: ctk.CTkFrame,
        font_names: list[str],
    ) -> dict[str, Any]:
        ctk.CTkLabel(
            simple_parent,
            text="Título del Curso Destacado (ej. {CURSO})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(6, 1))

        entry_text = make_entry(simple_parent, "{CURSO}", height=30)
        entry_text.pack(fill="x", padx=10, pady=(0, 4))
        entry_text.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        sw_row = ctk.CTkFrame(simple_parent, fg_color="transparent")
        sw_row.pack(fill="x", padx=10, pady=(0, 2))

        sw_enabled = ctk.CTkSwitch(
            sw_row,
            text="Mostrar franja",
            font=ctk.CTkFont(size=11),
            command=self._schedule_preview,
        )
        sw_enabled.pack(side="left", padx=(0, 12))

        sw_pill = ctk.CTkSwitch(
            sw_row,
            text="Pastilla de color",
            font=ctk.CTkFont(size=11),
            command=self._schedule_preview,
        )
        sw_pill.pack(side="left")

        pill_color_picker = ColorPickerButton(
            simple_parent,
            initial_color="#76B02A",
            label_text="Color Franja Curso",
            on_change=lambda _c: self._schedule_preview(),
        )
        pill_color_picker.pack(fill="x", padx=10, pady=(2, 6))

        adv_box = ctk.CTkFrame(adv_parent, fg_color=BG_PANEL, corner_radius=6)
        adv_box.pack(fill="x", padx=8, pady=3)
        ctk.CTkLabel(
            adv_box,
            text="Ajustes: Franja de Curso ({CURSO})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(4, 2))
        controls = self._build_alignment_xy_font_controls(
            adv_box, font_names, color_label="Color Texto Curso"
        )
        return {
            "enabled": sw_enabled,
            "pill_enabled": sw_pill,
            "pill_color": pill_color_picker,
            "text": entry_text,
            **controls,
        }

    def _create_split_body_block(
        self,
        *,
        simple_parent: ctk.CTkFrame,
        adv_parent: ctk.CTkFrame,
        font_names: list[str],
    ) -> dict[str, Any]:
        ctk.CTkLabel(
            simple_parent,
            text="Texto de Reconocimiento (usá **...** para línea en negrita)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(6, 1))

        txt_body = ctk.CTkTextbox(
            simple_parent,
            height=76,
            corner_radius=6,
            fg_color="#0B1120",
            border_color="#334155",
            border_width=1,
            text_color=TEXT_PRIMARY,
        )
        txt_body.pack(fill="x", padx=10, pady=(0, 8))
        txt_body.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        adv_box = ctk.CTkFrame(adv_parent, fg_color=BG_PANEL, corner_radius=6)
        adv_box.pack(fill="x", padx=8, pady=3)
        ctk.CTkLabel(
            adv_box,
            text="Ajustes: Cuerpo del Certificado",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(4, 2))
        controls = self._build_alignment_xy_font_controls(adv_box, font_names)
        return {"textbox": txt_body, **controls}

    def _create_split_recipient_name_block(
        self,
        *,
        adv_parent: ctk.CTkFrame,
        font_names: list[str],
    ) -> dict[str, Any]:
        adv_box = ctk.CTkFrame(adv_parent, fg_color=BG_PANEL, corner_radius=6)
        adv_box.pack(fill="x", padx=8, pady=3)

        ctk.CTkLabel(
            adv_box,
            text="Ajustes: Nombre del Homenajeado ({nombre})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(4, 2))

        sw_underline = ctk.CTkSwitch(
            adv_box,
            text="Dibujar línea extra bajo el nombre",
            font=ctk.CTkFont(size=11),
            command=self._schedule_preview,
        )
        sw_underline.pack(fill="x", padx=10, pady=(2, 2))

        ul_color_picker = ColorPickerButton(
            adv_box,
            initial_color="#76B02A",
            label_text="Color Línea",
            on_change=lambda _c: self._schedule_preview(),
        )
        ul_color_picker.pack(fill="x", padx=10, pady=(0, 4))

        controls = self._build_alignment_xy_font_controls(
            adv_box, font_names, color_label="Color Nombre"
        )
        return {
            "underline": sw_underline,
            "underline_color": ul_color_picker,
            **controls,
        }

    def _build_alignment_xy_font_controls(
        self,
        parent: ctk.CTkFrame,
        font_names: list[str],
        *,
        color_label: str = "Color Texto",
    ) -> dict[str, Any]:
        row_pos = ctk.CTkFrame(parent, fg_color="transparent")
        row_pos.pack(fill="x", padx=10, pady=2)
        row_pos.grid_columnconfigure(0, weight=1)

        seg_align = ctk.CTkSegmentedButton(
            row_pos,
            values=["Izquierda", "Centro"],
            height=26,
            command=lambda _v: self._schedule_preview(),
        )
        seg_align.set("Izquierda")
        seg_align.grid(row=0, column=0, sticky="w", padx=(0, 6))

        ctk.CTkLabel(row_pos, text="X:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).grid(
            row=0, column=1, padx=2
        )
        entry_x = make_entry(row_pos, "320", width=56, height=26)
        entry_x.grid(row=0, column=2, padx=(0, 4))
        entry_x.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        ctk.CTkLabel(row_pos, text="Y:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).grid(
            row=0, column=3, padx=2
        )
        entry_y = make_entry(row_pos, "600", width=56, height=26)
        entry_y.grid(row=0, column=4)
        entry_y.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        row_font = ctk.CTkFrame(parent, fg_color="transparent")
        row_font.pack(fill="x", padx=10, pady=(2, 2))
        row_font.grid_columnconfigure(0, weight=1)

        opt_font = ctk.CTkOptionMenu(
            row_font,
            values=font_names,
            command=lambda _v: self._schedule_preview(),
            height=28,
            corner_radius=6,
        )
        opt_font.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkLabel(
            row_font, text="Tam:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY
        ).grid(row=0, column=1, padx=(0, 2))
        entry_size = make_entry(row_font, "36", width=52, height=28)
        entry_size.grid(row=0, column=2)
        entry_size.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        color_picker = ColorPickerButton(
            parent,
            initial_color="#14325C",
            label_text=color_label,
            on_change=lambda _c: self._schedule_preview(),
        )
        color_picker.pack(fill="x", padx=10, pady=(0, 6))

        return {
            "align": seg_align,
            "x": entry_x,
            "y": entry_y,
            "font": opt_font,
            "size": entry_size,
            "color": color_picker,
        }

    def _build_signature_pane(
        self, parent: ctk.CTkFrame, idx: int
    ) -> tuple[ctk.CTkFrame, dict[str, Any]]:
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid_columnconfigure(0, weight=1)

        sw_enabled = ctk.CTkSwitch(
            box,
            text=f"Mostrar Firma {idx + 1} en el diploma",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._schedule_preview,
        )
        sw_enabled.select()
        sw_enabled.grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(2, 4))

        e_name = make_entry(box, "Cargo o Nombre (ej. Directora de Producción)", height=30)
        e_name.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 4))
        e_name.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        e_role = make_entry(box, "Institución (ej. Municipalidad de San Roque)", height=30)
        e_role.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 4))
        e_role.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        make_secondary_button(
            box,
            "Cargar Firma (.pdf/.png/.jpg/.webp)",
            height=28,
            command=lambda i=idx: self._pick_signature_img(i),
        ).grid(row=3, column=0, sticky="ew", padx=(6, 4), pady=(2, 4))

        make_secondary_button(
            box,
            "Quitar",
            width=70,
            height=28,
            command=lambda i=idx: self._clear_signature_img(i),
        ).grid(row=3, column=1, sticky="ew", padx=(4, 6), pady=(2, 4))

        sw_bg = ctk.CTkSwitch(
            box,
            text="Quitar fondo blanco",
            font=ctk.CTkFont(size=11),
            command=self._schedule_preview,
        )
        sw_bg.select()
        sw_bg.grid(row=4, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 4))

        pos_row = ctk.CTkFrame(box, fg_color="transparent")
        pos_row.grid(row=5, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 4))
        pos_row.grid_columnconfigure(0, weight=1)

        seg_align = ctk.CTkSegmentedButton(
            pos_row,
            values=["Izquierda", "Centro"],
            height=26,
            command=lambda _v: self._schedule_preview(),
        )
        seg_align.set("Izquierda")
        seg_align.grid(row=0, column=0, sticky="w", padx=(0, 6))

        ctk.CTkLabel(pos_row, text="X:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).grid(
            row=0, column=1, padx=2
        )
        entry_x = make_entry(pos_row, "520", width=56, height=26)
        entry_x.grid(row=0, column=2, padx=(0, 4))
        entry_x.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        ctk.CTkLabel(pos_row, text="Y:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).grid(
            row=0, column=3, padx=2
        )
        entry_y = make_entry(pos_row, "2075", width=56, height=26)
        entry_y.grid(row=0, column=4)
        entry_y.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        return box, {
            "enabled": sw_enabled,
            "name": e_name,
            "role": e_role,
            "align": seg_align,
            "x": entry_x,
            "y": entry_y,
            "remove_bg": sw_bg,
        }

    def _build_preview_panel(self) -> None:
        card = SectionCard(self)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top,
            text="Vista Previa en Vivo (A4 Apaisado 300 DPI)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.entry_sample_name = make_entry(top, "Nombre de prueba", width=240, height=32)
        self.entry_sample_name.insert(0, "María José Fernández")
        self.entry_sample_name.grid(row=0, column=1, sticky="e", padx=8)
        self.entry_sample_name.bind("<KeyRelease>", lambda _e: self._schedule_preview())

        make_primary_button(
            top, "Actualizar", width=105, height=32, command=self._trigger_preview_render
        ).grid(row=0, column=2)

        self.preview_container = ctk.CTkFrame(card, fg_color=BG_PANEL, corner_radius=8)
        self.preview_container.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.preview_container.grid_columnconfigure(0, weight=1)
        self.preview_container.grid_rowconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(
            self.preview_container,
            text="Generando vista previa...",
            text_color=TEXT_SECONDARY,
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def on_show(self) -> None:
        self._load_font_catalog()
        templates = self.template_repo.list_all()
        self._templates_by_name = {t["name"]: t for t in templates}
        names = list(self._templates_by_name.keys())
        if not names:
            return
        self.opt_template.configure(values=names)

        target_name = names[0]
        active_cid = self.get_active_course_id()
        if active_cid is not None:
            course = self.course_repo.get_by_id(active_cid)
            if course and course.get("template_id"):
                for t in templates:
                    if int(t["id"]) == int(course["template_id"]):
                        target_name = t["name"]
                        break

        if self._current_template and self._current_template["name"] in self._templates_by_name:
            target_name = self._current_template["name"]

        self.opt_template.set(target_name)
        self._on_template_selected(target_name)

    def _on_template_selected(self, name: str) -> None:
        tpl = self._templates_by_name.get(name)
        if not tpl:
            return
        self._current_template = copy.deepcopy(tpl)
        self._populate_fields_from_template()
        self._trigger_preview_render()

    def _populate_fields_from_template(self) -> None:
        if not self._current_template:
            return
        self._loading_ui = True
        try:
            cfg = self._current_template["config"]

            # 1. Poblar los 4 logos
            logos_cfg = cfg.setdefault("logos", {})
            default_coords = {
                "main": (1660, 2110),
                "secondary": (2140, 2110),
                "logo_3": (2620, 2110),
                "logo_4": (3080, 2110),
            }
            for slot_key in LOGO_SLOT_KEYS:
                slot = logos_cfg.setdefault(slot_key, {})
                w = self.logo_widgets[slot_key]
                path_str = slot.get("image_path", "")
                if not path_str and slot_key == "main":
                    path_str = self._current_template.get("logo_main_path", "")
                elif not path_str and slot_key == "secondary":
                    path_str = self._current_template.get("logo_sec_path", "")

                w["lbl_file"].configure(
                    text=Path(path_str).name[:22] if path_str else "(Sin archivo)"
                )
                matched_label = "Logo Oficial..."
                if path_str:
                    fname = Path(path_str).name
                    for lbl, full_p in self._inst_logo_label_to_path.items():
                        if Path(full_p).name == fname:
                            matched_label = lbl
                            break
                w["opt_inst_logo"].set(matched_label)
                if slot.get("remove_white_bg", False):
                    w["remove_bg"].select()
                else:
                    w["remove_bg"].deselect()

                if slot.get("tint_enabled", False):
                    w["tint_enabled"].select()
                else:
                    w["tint_enabled"].deselect()
                w["tint_color"].set(
                    str(slot.get("tint_color", cfg.get("title", {}).get("color", "#14325C")))
                )

                size_px = int(slot.get("max_width", 290))
                w["slider_size"].set(max(80, min(600, size_px)))
                self._set_entry(w["entry_size"], str(size_px))

                def_x, def_y = default_coords[slot_key]
                self._set_entry(w["entry_x"], str(resolve_x_px(slot.get("x"), def_x)))
                self._set_entry(w["entry_y"], str(resolve_y_px(slot.get("y"), def_y)))

            # 2. Bloques de texto estándar
            defaults_y = {
                "header_institution": 265,
                "header_area": 505,
                "title": 925,
                "subtitle": 1020,
                "recipient_dni": 1295,
                "footer_date": 1650,
            }
            for key, w in self.block_widgets.items():
                block = cfg.get(key, {})
                self._set_entry(w["text"], str(block.get("text", "")))
                self._populate_common_controls(w, block, default_y=defaults_y.get(key, 600))

            # 3. Franja destacada de Curso (course_banner)
            cb = cfg.get("course_banner", {})
            if cb.get("enabled", False):
                self.course_banner_widgets["enabled"].select()
            else:
                self.course_banner_widgets["enabled"].deselect()
            if cb.get("pill_enabled", True):
                self.course_banner_widgets["pill_enabled"].select()
            else:
                self.course_banner_widgets["pill_enabled"].deselect()
            self.course_banner_widgets["pill_color"].set(cb.get("pill_color", "#76B02A"))
            self._set_entry(self.course_banner_widgets["text"], str(cb.get("text", "{CURSO}")))
            self._populate_common_controls(self.course_banner_widgets, cb, default_y=625)

            # 4. Nombre del homenajeado y visibilidad de DNI
            if cfg.get("show_dni", True):
                self.sw_show_dni.select()
            else:
                self.sw_show_dni.deselect()

            rn = cfg.get("recipient_name", {})
            if rn.get("underline", False):
                self.name_widgets["underline"].select()
            else:
                self.name_widgets["underline"].deselect()
            self.name_widgets["underline_color"].set(
                rn.get("underline_color", rn.get("color", "#14325C"))
            )
            self._populate_common_controls(self.name_widgets, rn, default_y=1200)

            # 5. Cuerpo
            body = cfg.get("body", {})
            self.body_widgets["textbox"].delete("1.0", "end")
            self.body_widgets["textbox"].insert("1.0", str(body.get("text", "")))
            self._populate_common_controls(self.body_widgets, body, default_y=1420)

            # 6. Firmas
            sigs = cfg.get("signatures", [])
            for idx, sw in enumerate(self.sig_widgets):
                sig = sigs[idx] if idx < len(sigs) else {}
                if sig.get("enabled", idx == 0):
                    sw["enabled"].select()
                else:
                    sw["enabled"].deselect()
                self._set_entry(sw["name"], str(sig.get("name", "")))
                self._set_entry(sw["role"], str(sig.get("role", "")))
                sw["align"].set(self._align_to_ui(sig.get("align", "left")))
                def_sx = 520 if idx == 0 else 1060
                self._set_entry(sw["x"], str(resolve_x_px(sig.get("x"), def_sx)))
                self._set_entry(sw["y"], str(resolve_y_px(sig.get("y"), 2075)))
                if sig.get("remove_white_bg", True):
                    sw["remove_bg"].select()
                else:
                    sw["remove_bg"].deselect()
        finally:
            self._loading_ui = False

    def _populate_common_controls(
        self, widgets: dict[str, Any], block: dict[str, Any], default_y: int
    ) -> None:
        align = str(block.get("align", "left")).lower()
        widgets["align"].set(self._align_to_ui(align))
        def_x = 320 if align == "left" else 1754
        self._set_entry(widgets["x"], str(resolve_x_px(block.get("x"), def_x)))
        self._set_entry(widgets["y"], str(resolve_y_px(block.get("y"), default_y)))

        fname = block.get("font", "NotoSans-Regular.ttf")
        disp = self._font_file_to_display.get(fname) or font_display_name(fname)
        if disp in self._font_display_to_file:
            widgets["font"].set(disp)
        self._set_entry(widgets["size"], str(block.get("size", 36)))
        widgets["color"].set(str(block.get("color", "#14325C")))

    @staticmethod
    def _set_entry(entry: ctk.CTkEntry, value: str) -> None:
        entry.delete(0, "end")
        entry.insert(0, value)

    @staticmethod
    def _parse_int(entry: ctk.CTkEntry, default: int, min_v: int, max_v: int) -> int:
        try:
            val = int(float(entry.get().strip()))
            return max(min_v, min(max_v, val))
        except ValueError:
            return default

    def _collect_common_controls(
        self,
        block: dict[str, Any],
        widgets: dict[str, Any],
        default_x: int,
        default_y: int,
        default_size: int,
    ) -> None:
        block["align"] = self._ui_to_align(widgets["align"].get())
        block["x"] = self._parse_int(widgets["x"], default_x, 80, 3420)
        block["y"] = self._parse_int(widgets["y"], default_y, 80, 2400)
        disp = widgets["font"].get()
        if disp in self._font_display_to_file:
            block["font"] = self._font_display_to_file[disp]
        block["size"] = self._parse_int(widgets["size"], default_size, 12, 260)
        block["color"] = widgets["color"].get()

    def _collect_template_state(self) -> dict[str, Any] | None:
        if not self._current_template:
            return None
        tpl = copy.deepcopy(self._current_template)
        cfg = tpl["config"]

        # 1. Logos (4 slots)
        logos_cfg = cfg.setdefault("logos", {})
        for slot_key in LOGO_SLOT_KEYS:
            slot = logos_cfg.setdefault(slot_key, {})
            w = self.logo_widgets[slot_key]
            slot["remove_white_bg"] = bool(w["remove_bg"].get())
            slot["tint_enabled"] = bool(w["tint_enabled"].get())
            slot["tint_color"] = w["tint_color"].get()
            size_px = self._parse_int(w["entry_size"], 290, 80, 600)
            slot["max_width"] = size_px
            slot["max_height"] = max(80, int(size_px * 0.85))
            slot["x"] = self._parse_int(w["entry_x"], 1660, 80, 3420)
            slot["y"] = self._parse_int(w["entry_y"], 2110, 80, 2400)

        # 2. Bloques de texto estándar
        for key, w in self.block_widgets.items():
            blk = cfg.setdefault(key, {})
            blk["text"] = w["text"].get().strip()
            self._collect_common_controls(blk, w, 320, 600, 36)

        # 3. Franja destacada de Curso
        cb = cfg.setdefault("course_banner", {})
        cb["enabled"] = bool(self.course_banner_widgets["enabled"].get())
        cb["pill_enabled"] = bool(self.course_banner_widgets["pill_enabled"].get())
        cb["pill_color"] = self.course_banner_widgets["pill_color"].get()
        cb["text"] = self.course_banner_widgets["text"].get().strip() or "{CURSO}"
        self._collect_common_controls(cb, self.course_banner_widgets, 320, 625, 62)

        # 4. Nombre del homenajeado y visibilidad de DNI
        cfg["show_dni"] = bool(self.sw_show_dni.get())
        rn = cfg.setdefault("recipient_name", {})
        rn["underline"] = bool(self.name_widgets["underline"].get())
        rn["underline_color"] = self.name_widgets["underline_color"].get()
        self._collect_common_controls(rn, self.name_widgets, 320, 1200, 84)

        # 5. Cuerpo
        body = cfg.setdefault("body", {})
        body["text"] = self.body_widgets["textbox"].get("1.0", "end").strip()
        self._collect_common_controls(body, self.body_widgets, 320, 1420, 44)

        # 6. Firmas
        sigs = cfg.setdefault("signatures", [{}, {}])
        while len(sigs) < 2:
            sigs.append({"x": 520, "y": 2075, "max_width": 360, "max_height": 130})
        for idx, sw in enumerate(self.sig_widgets):
            sigs[idx]["enabled"] = bool(sw["enabled"].get())
            sigs[idx]["name"] = sw["name"].get().strip()
            sigs[idx]["role"] = sw["role"].get().strip()
            sigs[idx]["align"] = self._ui_to_align(sw["align"].get())
            sigs[idx]["x"] = self._parse_int(sw["x"], 520 if idx == 0 else 1060, 80, 3420)
            sigs[idx]["y"] = self._parse_int(sw["y"], 2075, 100, 2400)
            sigs[idx]["remove_white_bg"] = bool(sw["remove_bg"].get())

        return tpl

    def _apply_logos_preset(self, mode: str) -> None:
        if mode == "bottom_right_row":
            coords = [(1660, 2110), (2140, 2110), (2620, 2110), (3080, 2110)]
            size = 290
        elif mode == "top_center":
            coords = [(1270, 260), (1590, 260), (1910, 260), (2230, 260)]
            size = 220
        else:  # top_left
            coords = [(360, 260), (680, 260), (1000, 260), (1320, 260)]
            size = 220

        for idx, slot_key in enumerate(LOGO_SLOT_KEYS):
            w = self.logo_widgets[slot_key]
            lx, ly = coords[idx]
            w["slider_size"].set(size)
            self._set_entry(w["entry_size"], str(size))
            self._set_entry(w["entry_x"], str(lx))
            self._set_entry(w["entry_y"], str(ly))

        self._trigger_preview_render()
        self.notify("Ubicación rápida aplicada a los 4 logos.", "info")

    def _apply_global_alignment(self, mode: str) -> None:
        ui_label = "Izquierda" if mode == "left" else "Centro"
        target_x = "320" if mode == "left" else "1754"

        for w in (
            *self.block_widgets.values(),
            self.course_banner_widgets,
            self.name_widgets,
            self.body_widgets,
        ):
            w["align"].set(ui_label)
            self._set_entry(w["x"], target_x)

        for idx, sw in enumerate(self.sig_widgets):
            sw["align"].set(ui_label)
            sig_x = ("520" if idx == 0 else "1060") if mode == "left" else ("1050" if idx == 0 else "2455")
            self._set_entry(sw["x"], sig_x)

        self._trigger_preview_render()
        self.notify(f"Alineación global cambiada a: {ui_label}.", "info")

    def _pick_background(self) -> None:
        if not self._current_template:
            return
        file_path = filedialog.askopenfilename(
            title="Seleccionar Plantilla Base", filetypes=FILEDIALOG_ASSET_TYPES
        )
        if not file_path:
            return
        try:
            stored = import_asset_to_local_store(file_path, category="fondos")
            self._current_template["bg_path"] = str(stored)
            self._trigger_preview_render()
            self.notify("Fondo actualizado en la vista previa.", "info")
        except Exception as exc:
            self.notify(f"Error al cargar fondo: {exc}", "error")

    def _on_pick_institutional_logo(self, slot_key: str, label: str) -> None:
        if not self._current_template:
            return
        logo_path = self._inst_logo_label_to_path.get(label)
        if not logo_path:
            return
        logos_cfg = self._current_template["config"].setdefault("logos", {})
        logos_cfg.setdefault(slot_key, {})["image_path"] = logo_path
        if slot_key == "main":
            self._current_template["logo_main_path"] = logo_path
        elif slot_key == "secondary":
            self._current_template["logo_sec_path"] = logo_path

        self.logo_widgets[slot_key]["lbl_file"].configure(text=Path(logo_path).name[:22])
        self._trigger_preview_render()
        self.notify(f"Logo institucional asignado: {label}", "info")

    def _pick_logo(self, slot_key: str) -> None:
        if not self._current_template:
            return
        file_path = filedialog.askopenfilename(
            title=f"Seleccionar {LOGO_DESCRIPTIONS[slot_key]}",
            filetypes=FILEDIALOG_ASSET_TYPES,
        )
        if not file_path:
            return
        try:
            stored = import_asset_to_local_store(file_path, category="logos")
            stored_str = str(stored)
            logos_cfg = self._current_template["config"].setdefault("logos", {})
            logos_cfg.setdefault(slot_key, {})["image_path"] = stored_str
            if slot_key == "main":
                self._current_template["logo_main_path"] = stored_str
            elif slot_key == "secondary":
                self._current_template["logo_sec_path"] = stored_str

            self.logo_widgets[slot_key]["lbl_file"].configure(text=stored.name[:22])
            self._trigger_preview_render()
            self.notify(f"{LOGO_DESCRIPTIONS[slot_key]} cargado.", "info")
        except Exception as exc:
            self.notify(f"Error al cargar logo: {exc}", "error")

    def _clear_logo(self, slot_key: str) -> None:
        if not self._current_template:
            return
        logos_cfg = self._current_template["config"].setdefault("logos", {})
        logos_cfg.setdefault(slot_key, {})["image_path"] = ""
        if slot_key == "main":
            self._current_template["logo_main_path"] = ""
        elif slot_key == "secondary":
            self._current_template["logo_sec_path"] = ""
        self.logo_widgets[slot_key]["lbl_file"].configure(text="(Sin archivo)")
        self._trigger_preview_render()

    def _pick_signature_img(self, idx: int) -> None:
        if not self._current_template:
            return
        file_path = filedialog.askopenfilename(
            title=f"Seleccionar Firma {idx + 1}", filetypes=FILEDIALOG_ASSET_TYPES
        )
        if not file_path:
            return
        try:
            stored = import_asset_to_local_store(file_path, category="firmas")
            sigs = self._current_template["config"].setdefault("signatures", [{}, {}])
            while len(sigs) <= idx:
                sigs.append({"x": 1060, "y": 2075, "max_width": 360, "max_height": 130})
            sigs[idx]["image_path"] = str(stored)
            self._trigger_preview_render()
            self.notify(f"Imagen de Firma {idx + 1} cargada.", "info")
        except Exception as exc:
            self.notify(f"Error al cargar firma: {exc}", "error")

    def _clear_signature_img(self, idx: int) -> None:
        if not self._current_template:
            return
        sigs = self._current_template["config"].get("signatures", [])
        if idx < len(sigs):
            sigs[idx]["image_path"] = ""
        self._trigger_preview_render()

    def _save_current_template(self) -> None:
        tpl = self._collect_template_state()
        if not tpl:
            return
        self.template_repo.update(
            int(tpl["id"]),
            bg_path=tpl["bg_path"],
            logo_main_path=tpl.get("logo_main_path", ""),
            logo_sec_path=tpl.get("logo_sec_path", ""),
            config=tpl["config"],
        )
        self._current_template = tpl
        self._templates_by_name[tpl["name"]] = tpl
        self.notify(f"Plantilla guardada: {tpl['name']}", "success")

    def _save_as_new_template(self) -> None:
        tpl = self._collect_template_state()
        if not tpl:
            return
        new_name = simpledialog.askstring(
            "Nueva Plantilla", "Ingresá el nombre para la nueva plantilla:"
        )
        if not new_name or not new_name.strip():
            return
        new_id = self.template_repo.create(
            name=new_name.strip(),
            bg_path=tpl["bg_path"],
            logo_main_path=tpl.get("logo_main_path", ""),
            logo_sec_path=tpl.get("logo_sec_path", ""),
            config=tpl["config"],
            is_preset=False,
        )
        self.on_show()
        created = self.template_repo.get_by_id(new_id)
        if created:
            self.opt_template.set(created["name"])
            self._on_template_selected(created["name"])
        self.notify(f"Nueva plantilla creada: {new_name.strip()}", "success")

    def _schedule_preview(self) -> None:
        if self._loading_ui:
            return
        if self._debounce_job is not None:
            self.after_cancel(self._debounce_job)
        self._debounce_job = self.after(180, self._trigger_preview_render)

    def _trigger_preview_render(self) -> None:
        self._debounce_job = None
        tpl = self._collect_template_state()
        if not tpl:
            return

        course_data = {
            "title": "Cultivos Hidropónicos",
            "event_type": "Capacitación",
            "event_date": "26 de noviembre 2026",
            "hours": "12 horas reloj",
            "location": "San Roque, Corrientes",
        }
        active_cid = self.get_active_course_id()
        if active_cid is not None:
            c = self.course_repo.get_by_id(active_cid)
            if c:
                course_data = c

        sample_name = self.entry_sample_name.get().strip() or "María José Fernández"
        person_data = {"full_name": sample_name, "dni": "35123456"}

        self._render_seq += 1
        seq = self._render_seq

        def _worker() -> None:
            try:
                pil_img = render_preview_image(tpl, course_data, person_data, max_width=860)
                self.after(0, lambda: self._apply_preview_image(seq, pil_img))
            except Exception as exc:
                self.after(0, lambda err=str(exc): self.notify(f"Error vista previa: {err}", "error"))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_preview_image(self, seq: int, pil_img) -> None:
        if seq != self._render_seq:
            return
        display_w = max(560, min(860, self.preview_container.winfo_width() - 24))
        display_h = max(1, int(pil_img.height * (display_w / pil_img.width)))
        self.preview_ctk_image = ctk.CTkImage(
            light_image=pil_img, dark_image=pil_img, size=(display_w, display_h)
        )
        self.preview_label.configure(image=self.preview_ctk_image, text="")
