"""Vista de carga rápida de asistentes, autocompletado por DNI e importación Excel."""

from __future__ import annotations

import threading
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from src.database.repositories import (
    AttendeeRepository,
    CourseRepository,
    PersonRepository,
)
from src.services.excel_service import import_attendees_from_excel
from src.services.validators import (
    clean_dni,
    format_dni_display,
    is_valid_dni,
    is_valid_email,
    normalize_name,
    parse_whatsapp_list,
)
from src.ui.components.widgets import (
    ACCENT_GOLD,
    BG_CARD,
    BG_PANEL,
    BG_WINDOW,
    COLOR_DANGER,
    COLOR_SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    SectionCard,
    make_entry,
    make_primary_button,
    make_secondary_button,
)


class AttendeesView(ctk.CTkFrame):
    """Gestión de asistentes del Curso Activo con padrón histórico local."""

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

        self.course_repo = CourseRepository()
        self.person_repo = PersonRepository()
        self.attendee_repo = AttendeeRepository()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_quick_form()
        self._build_toolbar()
        self._build_table()

    def _build_quick_form(self) -> None:
        card = SectionCard(self)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            card,
            text="Carga Rápida de Asistentes (Enter para avanzar y guardar)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, sticky="ew", padx=14, pady=(10, 6))

        ctk.CTkLabel(card, text="DNI *", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=1, column=0, sticky="ew", padx=(14, 6)
        )
        ctk.CTkLabel(card, text="Apellido y Nombre *", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=1, column=1, sticky="ew", padx=6
        )
        ctk.CTkLabel(card, text="Institución / Cargo", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=1, column=2, sticky="ew", padx=6
        )
        ctk.CTkLabel(card, text="Email (Opcional)", text_color=TEXT_SECONDARY, anchor="w").grid(
            row=1, column=3, sticky="ew", padx=(6, 14)
        )

        self.entry_dni = make_entry(card, "Ej. 35123456")
        self.entry_dni.grid(row=2, column=0, sticky="ew", padx=(14, 6), pady=(2, 10))
        self.entry_dni.bind("<Return>", self._on_dni_enter)
        self.entry_dni.bind("<FocusOut>", lambda _e: self._autocomplete_by_dni())

        self.entry_name = make_entry(card, "Ej. Pérez Juan Carlos")
        self.entry_name.grid(row=2, column=1, sticky="ew", padx=6, pady=(2, 10))
        self.entry_name.bind("<Return>", lambda _e: self.entry_inst.focus_set())

        self.entry_inst = make_entry(card, "Municipalidad / Área")
        self.entry_inst.grid(row=2, column=2, sticky="ew", padx=6, pady=(2, 10))
        self.entry_inst.bind("<Return>", lambda _e: self.entry_email.focus_set())

        self.entry_email = make_entry(card, "correo@ejemplo.com")
        self.entry_email.grid(row=2, column=3, sticky="ew", padx=(6, 14), pady=(2, 10))
        self.entry_email.bind("<Return>", lambda _e: self._save_attendee())

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=3, column=0, columnspan=4, sticky="ew", padx=14, pady=(0, 12))

        self.entry_phone = make_entry(btn_row, "Teléfono (Opcional)", width=200)
        self.entry_phone.pack(side="left", padx=(0, 10))
        self.entry_phone.bind("<Return>", lambda _e: self._save_attendee())

        make_primary_button(
            btn_row, "Guardar Asistente", width=170, command=self._save_attendee
        ).pack(side="left", padx=(0, 8))

        make_secondary_button(
            btn_row, "Limpiar", width=90, command=self._clear_inputs
        ).pack(side="left")

        self.lbl_stats = ctk.CTkLabel(
            btn_row,
            text="Inscriptos: 0  |  Presentes: 0",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.lbl_stats.pack(side="right")

    def _build_toolbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        bar.grid_columnconfigure(0, weight=1)

        self.entry_search = make_entry(bar, "Buscar por DNI o Nombre...")
        self.entry_search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_search.bind("<KeyRelease>", lambda _e: self._refresh_list())

        self.btn_whatsapp = make_secondary_button(
            bar,
            "📋 Pegar desde WhatsApp",
            fg_color="#0D9488",
            hover_color="#0F766E",
            command=self._open_whatsapp_dialog,
        )
        self.btn_whatsapp.grid(row=0, column=1, padx=(0, 8))

        self.btn_import = make_secondary_button(
            bar,
            "📥 Importar desde Excel (.xlsx)",
            fg_color=COLOR_SUCCESS,
            hover_color="#059669",
            command=self._import_excel,
        )
        self.btn_import.grid(row=0, column=2)

    def _build_table(self) -> None:
        card = SectionCard(self)
        card.grid(row=2, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)

        self.list_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.list_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.list_scroll.grid_columnconfigure(0, weight=1)

    def on_show(self) -> None:
        self._refresh_list()

    def _on_dni_enter(self, _event=None) -> None:
        self._autocomplete_by_dni()
        self.entry_name.focus_set()

    def _autocomplete_by_dni(self) -> None:
        dni = clean_dni(self.entry_dni.get())
        if not dni:
            return
        person = self.person_repo.get_by_dni(dni)
        if person:
            self._set_if_empty(self.entry_name, person.get("full_name", ""))
            self._set_if_empty(self.entry_inst, person.get("institution_or_role", ""))
            self._set_if_empty(self.entry_email, person.get("email", ""))
            self._set_if_empty(self.entry_phone, person.get("phone", ""))
            self.notify(f"Datos autocompletados desde padrón histórico (DNI {format_dni_display(dni)}).", "info")

    @staticmethod
    def _set_if_empty(entry: ctk.CTkEntry, value: str) -> None:
        if value and not entry.get().strip():
            entry.delete(0, "end")
            entry.insert(0, value)

    def _save_attendee(self) -> None:
        course_id = self.get_active_course_id()
        if course_id is None:
            self.notify("Primero seleccioná o creá un Curso Activo.", "warning")
            return

        raw_dni = self.entry_dni.get()
        if not is_valid_dni(raw_dni):
            self.notify("Ingresá un DNI válido (6 a 9 dígitos).", "warning")
            self.entry_dni.focus_set()
            return

        full_name = normalize_name(self.entry_name.get())
        if not full_name:
            self.notify("El Apellido y Nombre es obligatorio.", "warning")
            self.entry_name.focus_set()
            return

        email = self.entry_email.get().strip()
        if not is_valid_email(email):
            self.notify("El formato del correo electrónico no es válido.", "warning")
            self.entry_email.focus_set()
            return

        dni = self.person_repo.upsert(
            dni=raw_dni,
            full_name=full_name,
            email=email,
            phone=self.entry_phone.get().strip(),
            institution_or_role=self.entry_inst.get().strip(),
        )
        self.attendee_repo.enroll(course_id, dni, attended=True)

        self._clear_inputs()
        self._refresh_list()
        self.entry_dni.focus_set()
        self.notify(f"Asistente guardado: {full_name} (DNI {format_dni_display(dni)})", "success")

    def _clear_inputs(self) -> None:
        for entry in (
            self.entry_dni,
            self.entry_name,
            self.entry_inst,
            self.entry_email,
            self.entry_phone,
        ):
            entry.delete(0, "end")

    def _refresh_list(self) -> None:
        for child in self.list_scroll.winfo_children():
            child.destroy()

        course_id = self.get_active_course_id()
        if course_id is None:
            self.lbl_stats.configure(text="Sin Curso Activo seleccionado")
            ctk.CTkLabel(
                self.list_scroll,
                text="Seleccioná un Curso Activo en la barra lateral o en 'Cursos y Jornadas'.",
                text_color=TEXT_SECONDARY,
            ).grid(row=0, column=0, pady=40)
            return

        query = self.entry_search.get().strip()
        rows = self.attendee_repo.list_by_course(course_id, search_query=query)
        all_rows = rows if not query else self.attendee_repo.list_by_course(course_id)
        present_count = sum(1 for r in all_rows if r.get("attended", 1))
        self.lbl_stats.configure(
            text=f"Inscriptos: {len(all_rows)}  |  Presentes: {present_count}"
        )

        if not rows:
            ctk.CTkLabel(
                self.list_scroll,
                text="No hay asistentes registrados para mostrar.",
                text_color=TEXT_SECONDARY,
            ).grid(row=0, column=0, pady=30)
            return

        for idx, row in enumerate(rows):
            item = ctk.CTkFrame(
                self.list_scroll, fg_color=BG_PANEL, corner_radius=6, border_width=1, border_color="#334155"
            )
            item.grid(row=idx, column=0, sticky="ew", pady=(0, 6))
            item.grid_columnconfigure(1, weight=1)

            att_id = int(row["id"])
            var_att = ctk.BooleanVar(value=bool(row.get("attended", 1)))
            chk = ctk.CTkCheckBox(
                item,
                text="Presente",
                variable=var_att,
                width=95,
                command=lambda a_id=att_id, v=var_att: self._toggle_attended(a_id, v.get()),
            )
            chk.grid(row=0, column=0, padx=12, pady=8)

            info_text = f"{row['full_name']}  •  DNI {format_dni_display(row['dni'])}"
            if row.get("institution_or_role"):
                info_text += f"  •  {row['institution_or_role']}"
            ctk.CTkLabel(
                item,
                text=info_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=TEXT_PRIMARY,
                anchor="w",
            ).grid(row=0, column=1, sticky="ew", padx=8)

            badge_text = "Emitido" if row.get("cert_generated") else "Pendiente"
            badge_color = COLOR_SUCCESS if row.get("cert_generated") else TEXT_SECONDARY
            ctk.CTkLabel(
                item,
                text=badge_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=badge_color,
                width=80,
            ).grid(row=0, column=2, padx=8)

            make_secondary_button(
                item,
                "Quitar",
                width=70,
                height=28,
                fg_color=COLOR_DANGER,
                hover_color="#DC2626",
                command=lambda a_id=att_id, n=row["full_name"]: self._remove_attendee(a_id, n),
            ).grid(row=0, column=3, padx=(4, 12), pady=8)

    def _toggle_attended(self, attendee_id: int, attended: bool) -> None:
        self.attendee_repo.set_attended(attendee_id, attended)
        self._refresh_list()

    def _remove_attendee(self, attendee_id: int, name: str) -> None:
        if not messagebox.askyesno("Quitar asistente", f"¿Quitar a {name} de este curso?"):
            return
        self.attendee_repo.remove(attendee_id)
        self._refresh_list()
        self.notify(f"Asistente quitado: {name}", "info")

    def _import_excel(self) -> None:
        course_id = self.get_active_course_id()
        if course_id is None:
            self.notify("Primero seleccioná o creá un Curso Activo.", "warning")
            return

        file_path = filedialog.askopenfilename(
            title="Importar Nómina desde Excel",
            filetypes=[("Planillas Excel", "*.xlsx *.xlsm")],
        )
        if not file_path:
            return

        self.btn_import.configure(state="disabled", text="Importando...")
        self.notify("Leyendo planilla Excel...", "info")

        def _worker() -> None:
            try:
                records, warnings = import_attendees_from_excel(file_path)
                for rec in records:
                    dni = self.person_repo.upsert(
                        dni=rec["dni"],
                        full_name=rec["full_name"],
                        email=rec.get("email", ""),
                        phone=rec.get("phone", ""),
                        institution_or_role=rec.get("institution_or_role", ""),
                    )
                    self.attendee_repo.enroll(course_id, dni, attended=True)
                self.after(0, lambda: self._on_import_done(len(records), len(warnings)))
            except Exception as exc:
                self.after(0, lambda err=str(exc): self._on_import_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_import_done(self, imported: int, skipped: int) -> None:
        self.btn_import.configure(state="normal", text="📥 Importar desde Excel (.xlsx)")
        self._refresh_list()
        msg = f"Importación completada: {imported} asistentes cargados."
        if skipped:
            msg += f" ({skipped} filas omitidas por datos inválidos)"
        self.notify(msg, "success")

    def _on_import_error(self, error_msg: str) -> None:
        self.btn_import.configure(state="normal", text="📥 Importar desde Excel (.xlsx)")
        self.notify(f"Error al importar Excel: {error_msg}", "error")

    def _open_whatsapp_dialog(self) -> None:
        course_id = self.get_active_course_id()
        if course_id is None:
            self.notify("Primero seleccioná o creá un Curso Activo.", "warning")
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("📋 Pegar Lista de Asistentes desde WhatsApp")
        dlg.geometry("660x520")
        dlg.minsize(560, 440)
        dlg.configure(fg_color=BG_WINDOW)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        dlg.grid_columnconfigure(0, weight=1)
        dlg.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            dlg,
            text="Pegá el mensaje o tabla copiada de WhatsApp",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 2))

        ctk.CTkLabel(
            dlg,
            text=(
                "Formatos soportados automáticamente:\n"
                "• | 1 | Montenegro Ricardo | 36.303.823 |   • 1. Montenegro Ricardo - 36303823   • Montenegro Ricardo 36.303.823"
            ),
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        txt = ctk.CTkTextbox(
            dlg,
            corner_radius=6,
            fg_color=BG_PANEL,
            border_color="#334155",
            border_width=1,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=12),
        )
        txt.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))

        preview_card = ctk.CTkFrame(dlg, fg_color=BG_CARD, corner_radius=6)
        preview_card.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 10))
        preview_card.grid_columnconfigure(0, weight=1)

        lbl_count = ctk.CTkLabel(
            preview_card,
            text="Personas detectadas: 0",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_SUCCESS,
            anchor="w",
        )
        lbl_count.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 2))

        lbl_sample = ctk.CTkLabel(
            preview_card,
            text="Pegá el texto arriba para previsualizar los asistentes detectados.",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
            justify="left",
            anchor="w",
        )
        lbl_sample.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        def _update_preview(_event=None) -> list[dict[str, str]]:
            raw = txt.get("1.0", "end")
            parsed = parse_whatsapp_list(raw)
            lbl_count.configure(text=f"Personas detectadas: {len(parsed)}")
            if not parsed:
                lbl_sample.configure(
                    text="No se detectaron pares válidos de Nombre y DNI todavía."
                )
            else:
                sample_items = [
                    f"• {p['full_name']} (DNI {format_dni_display(p['dni'])})"
                    for p in parsed[:4]
                ]
                if len(parsed) > 4:
                    sample_items.append(f"  ... y {len(parsed) - 4} más.")
                lbl_sample.configure(text="\n".join(sample_items))
            return parsed

        txt.bind("<KeyRelease>", _update_preview)

        def _paste_clipboard() -> None:
            try:
                clip = dlg.clipboard_get()
                if clip:
                    txt.insert("insert", clip)
                    _update_preview()
            except Exception:
                pass

        def _confirm_import() -> None:
            parsed = _update_preview()
            if not parsed:
                self.notify("No se detectaron asistentes válidos en el texto pegado.", "warning")
                return

            existing_dnis = {
                r["dni"] for r in self.attendee_repo.list_by_course(course_id)
            }
            seen_in_batch: set[str] = set()
            new_count = 0
            dup_count = 0

            for item in parsed:
                dni = item["dni"]
                existing_person = self.person_repo.get_by_dni(dni)
                self.person_repo.upsert(
                    dni=dni,
                    full_name=item["full_name"],
                    email=existing_person.get("email", "") if existing_person else "",
                    phone=existing_person.get("phone", "") if existing_person else "",
                    institution_or_role=(
                        existing_person.get("institution_or_role", "")
                        if existing_person
                        else ""
                    ),
                )
                self.attendee_repo.enroll(course_id, dni, attended=True)
                if dni in existing_dnis or dni in seen_in_batch:
                    dup_count += 1
                else:
                    new_count += 1
                seen_in_batch.add(dni)

            dlg.destroy()
            self._refresh_list()
            msg = f"WhatsApp: {new_count} nuevos asistentes cargados"
            if dup_count:
                msg += f" ({dup_count} duplicados/actualizados)."
            else:
                msg += "."
            self.notify(msg, "success")

        btn_bar = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_bar.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 14))

        make_secondary_button(
            btn_bar, "Pegar del Portapapeles", command=_paste_clipboard
        ).pack(side="left")

        make_secondary_button(
            btn_bar, "Cancelar", width=90, command=dlg.destroy
        ).pack(side="right", padx=(8, 0))

        make_primary_button(
            btn_bar,
            "Confirmar y Guardar",
            fg_color=COLOR_SUCCESS,
            hover_color="#059669",
            command=_confirm_import,
        ).pack(side="right")

        txt.focus_set()
