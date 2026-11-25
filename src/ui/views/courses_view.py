"""Vista de gestión de Cursos y Jornadas."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from src.database.repositories import CourseRepository, TemplateRepository
from src.services.file_manager import ensure_course_directories, open_folder_in_explorer
from src.ui.components.widgets import (
    ACCENT_GOLD,
    BG_PANEL,
    COLOR_DANGER,
    COLOR_SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    SectionCard,
    make_entry,
    make_primary_button,
    make_secondary_button,
)

EVENT_TYPES = ["Curso", "Jornada", "Taller", "Capacitación", "Reconocimiento"]


class CoursesView(ctk.CTkFrame):
    """CRUD de Cursos/Jornadas y acceso rápido a su carpeta local."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        on_course_selected: Callable[[int | None], None],
        notify: Callable[[str, str], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.course_repo = CourseRepository()
        self.template_repo = TemplateRepository()
        self.on_course_selected = on_course_selected
        self.notify = notify

        self._editing_course_id: int | None = None
        self._templates_map: dict[str, int] = {}

        self.grid_columnconfigure(0, weight=0, minsize=380)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_form()
        self._build_list()

    def _build_form(self) -> None:
        card = SectionCard(self)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=0)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(
            card,
            text="Nuevo / Editar Curso o Jornada",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))

        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(scroll, text="Título del Evento *", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=8, pady=(4, 2)
        )
        self.entry_title = make_entry(scroll, "Ej. Operación y Mantenimiento de Redes")
        self.entry_title.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Tipo de Evento", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=2, column=0, sticky="ew", padx=8, pady=(4, 2)
        )
        self.opt_event_type = ctk.CTkOptionMenu(
            scroll, values=EVENT_TYPES, height=36, corner_radius=6, fg_color=BG_PANEL
        )
        self.opt_event_type.set("Curso")
        self.opt_event_type.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Fecha del Evento *", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=4, column=0, sticky="ew", padx=8, pady=(4, 2)
        )
        self.entry_date = make_entry(scroll, "Ej. 25 de noviembre de 2026")
        self.entry_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.entry_date.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Carga Horaria", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=6, column=0, sticky="ew", padx=8, pady=(4, 2)
        )
        self.entry_hours = make_entry(scroll, "Ej. 8 horas reloj")
        self.entry_hours.grid(row=7, column=0, sticky="ew", padx=8, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Lugar", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=8, column=0, sticky="ew", padx=8, pady=(4, 2)
        )
        self.entry_location = make_entry(scroll, "San Roque, Corrientes")
        self.entry_location.insert(0, "San Roque, Corrientes")
        self.entry_location.grid(row=9, column=0, sticky="ew", padx=8, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Plantilla de Diploma", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=10, column=0, sticky="ew", padx=8, pady=(4, 2)
        )
        self.opt_template = ctk.CTkOptionMenu(
            scroll, values=["(Sin plantilla)"], height=36, corner_radius=6, fg_color=BG_PANEL
        )
        self.opt_template.grid(row=11, column=0, sticky="ew", padx=8, pady=(0, 14))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", padx=14, pady=(6, 14))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_save = make_primary_button(btn_row, "Guardar Curso", command=self._save_course)
        self.btn_save.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_clear = make_secondary_button(btn_row, "Nuevo / Limpiar", command=self._reset_form)
        self.btn_clear.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _build_list(self) -> None:
        card = SectionCard(self)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="Cursos y Jornadas Registrados",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.list_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.list_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.list_scroll.grid_columnconfigure(0, weight=1)

    def on_show(self) -> None:
        self._refresh_templates_dropdown()
        self._refresh_courses_list()

    def _refresh_templates_dropdown(self) -> None:
        templates = self.template_repo.list_all()
        self._templates_map = {t["name"]: int(t["id"]) for t in templates}
        names = list(self._templates_map.keys())
        if names:
            self.opt_template.configure(values=names)
            if self.opt_template.get() not in self._templates_map:
                self.opt_template.set(names[0])
        else:
            self.opt_template.configure(values=["(Sin plantilla)"])
            self.opt_template.set("(Sin plantilla)")

    def _refresh_courses_list(self) -> None:
        for child in self.list_scroll.winfo_children():
            child.destroy()

        courses = self.course_repo.list_all()
        if not courses:
            ctk.CTkLabel(
                self.list_scroll,
                text="Aún no hay cursos creados. Completá el formulario de la izquierda para comenzar.",
                text_color=TEXT_SECONDARY,
            ).grid(row=0, column=0, pady=40)
            return

        for idx, course in enumerate(courses):
            item = ctk.CTkFrame(
                self.list_scroll, fg_color=BG_PANEL, corner_radius=8, border_width=1, border_color="#334155"
            )
            item.grid(row=idx, column=0, sticky="ew", pady=(0, 8))
            item.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(item, fg_color="transparent")
            info.grid(row=0, column=0, sticky="ew", padx=14, pady=10)
            info.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                info,
                text=f"[{course['event_type']}] {course['title']}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=TEXT_PRIMARY,
                anchor="w",
            ).grid(row=0, column=0, sticky="w")

            meta = (
                f"Fecha: {course['event_date']}  •  "
                f"Carga: {course['hours'] or '-'}  •  "
                f"Plantilla: {course.get('template_name') or 'Sin asignar'}\n"
                f"Asistentes: {course.get('total_attendees', 0)}  •  "
                f"Emitidos: {course.get('total_generated', 0)}"
            )
            ctk.CTkLabel(
                info,
                text=meta,
                font=ctk.CTkFont(size=12),
                text_color=TEXT_SECONDARY,
                justify="left",
                anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(2, 0))

            actions = ctk.CTkFrame(item, fg_color="transparent")
            actions.grid(row=0, column=1, padx=12, pady=10)

            cid = int(course["id"])
            make_primary_button(
                actions,
                "Activar",
                width=82,
                height=32,
                fg_color=COLOR_SUCCESS,
                hover_color="#059669",
                command=lambda c=cid: self._activate_course(c),
            ).pack(side="left", padx=3)

            make_secondary_button(
                actions,
                "Editar",
                width=72,
                height=32,
                command=lambda c=course: self._load_into_form(c),
            ).pack(side="left", padx=3)

            make_secondary_button(
                actions,
                "Carpeta",
                width=78,
                height=32,
                command=lambda fp=course["folder_path"]: self._open_course_folder(fp),
            ).pack(side="left", padx=3)

            make_secondary_button(
                actions,
                "Eliminar",
                width=78,
                height=32,
                fg_color=COLOR_DANGER,
                hover_color="#DC2626",
                command=lambda c=cid, t=course["title"]: self._delete_course(c, t),
            ).pack(side="left", padx=3)

    def _activate_course(self, course_id: int) -> None:
        self.on_course_selected(course_id)
        self.notify("Curso seleccionado como Curso Activo.", "success")

    def _load_into_form(self, course: dict) -> None:
        self._editing_course_id = int(course["id"])
        self.entry_title.delete(0, "end")
        self.entry_title.insert(0, course["title"])
        self.opt_event_type.set(course["event_type"])
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, course["event_date"])
        self.entry_hours.delete(0, "end")
        self.entry_hours.insert(0, course.get("hours", ""))
        self.entry_location.delete(0, "end")
        self.entry_location.insert(0, course.get("location", "San Roque, Corrientes"))

        tpl_name = course.get("template_name")
        if tpl_name and tpl_name in self._templates_map:
            self.opt_template.set(tpl_name)
        self.btn_save.configure(text="Actualizar Curso")

    def _reset_form(self) -> None:
        self._editing_course_id = None
        self.entry_title.delete(0, "end")
        self.opt_event_type.set("Curso")
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.entry_hours.delete(0, "end")
        self.entry_location.delete(0, "end")
        self.entry_location.insert(0, "San Roque, Corrientes")
        self.btn_save.configure(text="Guardar Curso")

    def _save_course(self) -> None:
        title = self.entry_title.get().strip()
        event_date = self.entry_date.get().strip()
        if not title or not event_date:
            self.notify("El título y la fecha del evento son obligatorios.", "warning")
            return

        event_type = self.opt_event_type.get()
        hours = self.entry_hours.get().strip()
        location = self.entry_location.get().strip() or "San Roque, Corrientes"
        tpl_id = self._templates_map.get(self.opt_template.get())

        course_dir, _ = ensure_course_directories(event_date, title)

        if self._editing_course_id is None:
            new_id = self.course_repo.create(
                title=title,
                event_type=event_type,
                event_date=event_date,
                hours=hours,
                location=location,
                template_id=tpl_id,
                folder_path=str(course_dir),
            )
            self.on_course_selected(new_id)
            self.notify(f"Curso creado y activado: {title}", "success")
        else:
            self.course_repo.update(
                self._editing_course_id,
                title=title,
                event_type=event_type,
                event_date=event_date,
                hours=hours,
                location=location,
                template_id=tpl_id,
                folder_path=str(course_dir),
            )
            self.on_course_selected(self._editing_course_id)
            self.notify(f"Curso actualizado: {title}", "success")

        self._reset_form()
        self._refresh_courses_list()

    def _open_course_folder(self, folder_path: str) -> None:
        if not folder_path:
            self.notify("Este curso no tiene carpeta asignada.", "warning")
            return
        open_folder_in_explorer(Path(folder_path))

    def _delete_course(self, course_id: int, title: str) -> None:
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el curso '{title}' y su lista de inscripciones de la base de datos?\n"
            "(Los archivos PDF ya generados en Documentos no se borrarán.)",
        ):
            return
        self.course_repo.delete(course_id)
        self.on_course_selected(None)
        self._refresh_courses_list()
        self.notify(f"Curso eliminado: {title}", "info")
