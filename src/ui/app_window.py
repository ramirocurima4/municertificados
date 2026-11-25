"""Ventana principal de MuniCertificados con navegación lateral y Curso Activo global."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from src.config import APP_DATA_DIR, APP_ICON_PATH, APP_NAME, APP_SUBTITLE
from src.database.repositories import CourseRepository
from src.services.file_manager import backup_database, open_folder_in_explorer
from src.ui.components.widgets import (
    ACCENT_GOLD,
    ACCENT_PRIMARY,
    BG_CARD,
    BG_PANEL,
    BG_WINDOW,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    StatusBanner,
    make_secondary_button,
)
from src.ui.views.attendees_view import AttendeesView
from src.ui.views.courses_view import CoursesView
from src.ui.views.designer_view import DesignerView
from src.ui.views.emit_view import EmitView


class AppWindow(ctk.CTk):
    """Contenedor principal de la aplicación de escritorio."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(f"{APP_NAME} — {APP_SUBTITLE}")
        self.geometry("1280x780")
        self.minsize(1080, 680)
        self.configure(fg_color=BG_WINDOW)
        if os.name == "nt" and APP_ICON_PATH.is_file():
            try:
                self.iconbitmap(str(APP_ICON_PATH))
            except Exception:
                pass

        self.course_repo = CourseRepository()
        self._active_course_id: int | None = None
        self._course_label_to_id: dict[str, int] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._views: dict[str, ctk.CTkFrame] = {}
        self._current_view_key: str = "courses"

        self.grid_columnconfigure(0, weight=0, minsize=255)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()
        self._refresh_active_course_selector()
        self.show_view("courses")

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self, fg_color=BG_PANEL, corner_radius=0, width=255
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(5, weight=1)

        # Identidad institucional
        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 12))

        ctk.CTkLabel(
            brand,
            text=APP_NAME,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            brand,
            text="Municipalidad de San Roque\nÁrea de Redes",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ACCENT_GOLD,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Selector global de Curso Activo
        course_box = ctk.CTkFrame(sidebar, fg_color=BG_CARD, corner_radius=8)
        course_box.grid(row=1, column=0, sticky="ew", padx=14, pady=(4, 14))
        course_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            course_box,
            text="CURSO ACTIVO",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))

        self.opt_active_course = ctk.CTkOptionMenu(
            course_box,
            values=["(Sin cursos)"],
            command=self._on_global_course_changed,
            height=34,
            corner_radius=6,
            fg_color=BG_PANEL,
        )
        self.opt_active_course.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Botones de navegación (4 vistas)
        nav_items = [
            ("courses", "1. Cursos y Jornadas"),
            ("designer", "2. Diseño de Diplomas"),
            ("attendees", "3. Asistentes y Lista"),
            ("emit", "4. Emitir Certificados"),
        ]
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="ew", padx=12)
        nav_frame.grid_columnconfigure(0, weight=1)

        for idx, (key, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                height=40,
                corner_radius=6,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="transparent",
                hover_color="#1E293B",
                text_color=TEXT_PRIMARY,
                command=lambda k=key: self.show_view(k),
            )
            btn.grid(row=idx, column=0, sticky="ew", pady=3)
            self._nav_buttons[key] = btn

        # Utilidades inferiores
        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.grid(row=6, column=0, sticky="ew", padx=14, pady=16)
        bottom.grid_columnconfigure(0, weight=1)

        make_secondary_button(
            bottom,
            "Abrir Carpeta Local",
            command=self._open_local_folder,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        make_secondary_button(
            bottom,
            "Copia de Seguridad BD",
            command=self._backup_db,
        ).grid(row=1, column=0, sticky="ew")

    def _build_main_area(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=16, pady=14)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self.status_banner = StatusBanner(main)
        self.status_banner.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.status_banner.clear()

        self.view_container = ctk.CTkFrame(main, fg_color="transparent")
        self.view_container.grid(row=1, column=0, sticky="nsew")
        self.view_container.grid_columnconfigure(0, weight=1)
        self.view_container.grid_rowconfigure(0, weight=1)

        self._views["courses"] = CoursesView(
            self.view_container,
            on_course_selected=self.set_active_course,
            notify=self.notify,
        )
        self._views["designer"] = DesignerView(
            self.view_container,
            get_active_course_id=self.get_active_course_id,
            notify=self.notify,
        )
        self._views["attendees"] = AttendeesView(
            self.view_container,
            get_active_course_id=self.get_active_course_id,
            notify=self.notify,
        )
        self._views["emit"] = EmitView(
            self.view_container,
            get_active_course_id=self.get_active_course_id,
            notify=self.notify,
        )

    def notify(self, message: str, level: str = "info") -> None:
        self.status_banner.show(message, level=level)

    def get_active_course_id(self) -> int | None:
        return self._active_course_id

    def set_active_course(self, course_id: int | None) -> None:
        self._active_course_id = course_id
        self._refresh_active_course_selector()
        current = self._views.get(self._current_view_key)
        if current and hasattr(current, "on_show"):
            current.on_show()

    def _refresh_active_course_selector(self) -> None:
        courses = self.course_repo.list_all()
        self._course_label_to_id.clear()
        if not courses:
            self._active_course_id = None
            self.opt_active_course.configure(values=["(Sin cursos)"])
            self.opt_active_course.set("(Sin cursos)")
            return

        labels: list[str] = []
        selected_label: str | None = None
        for c in courses:
            label = f"#{c['id']} — {c['title'][:26]}"
            labels.append(label)
            self._course_label_to_id[label] = int(c["id"])
            if self._active_course_id is not None and int(c["id"]) == self._active_course_id:
                selected_label = label

        self.opt_active_course.configure(values=labels)
        if selected_label is None:
            selected_label = labels[0]
            self._active_course_id = self._course_label_to_id[selected_label]
        self.opt_active_course.set(selected_label)

    def _on_global_course_changed(self, label: str) -> None:
        cid = self._course_label_to_id.get(label)
        if cid is None:
            return
        self._active_course_id = cid
        current = self._views.get(self._current_view_key)
        if current and hasattr(current, "on_show"):
            current.on_show()
        self.notify(f"Curso activo cambiado: {label}", "info")

    def show_view(self, key: str) -> None:
        if key not in self._views:
            return
        self._current_view_key = key

        for k, btn in self._nav_buttons.items():
            btn.configure(fg_color=ACCENT_PRIMARY if k == key else "transparent")

        for k, view in self._views.items():
            if k == key:
                view.grid(row=0, column=0, sticky="nsew")
                if hasattr(view, "on_show"):
                    view.on_show()
            else:
                view.grid_forget()

    def _open_local_folder(self) -> None:
        if self._active_course_id is not None:
            course = self.course_repo.get_by_id(self._active_course_id)
            if course and course.get("folder_path"):
                open_folder_in_explorer(Path(course["folder_path"]))
                return
        open_folder_in_explorer(APP_DATA_DIR)

    def _backup_db(self) -> None:
        default_name = f"muni_certificados_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
        dest = filedialog.asksaveasfilename(
            title="Guardar Copia de Seguridad de Base de Datos",
            defaultextension=".db",
            initialfile=default_name,
            filetypes=[("Base de Datos SQLite", "*.db")],
        )
        if not dest:
            return
        try:
            saved = backup_database(dest)
            self.notify(f"Copia de seguridad guardada en: {saved.name}", "success")
        except Exception as exc:
            self.notify(f"Error al respaldar BD: {exc}", "error")
