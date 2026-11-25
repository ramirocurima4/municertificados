"""Vista de emisión individual, por lote, exportación Excel y PDF unificado opcional."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable

import customtkinter as ctk

from src.database.repositories import (
    AttendeeRepository,
    CourseRepository,
    TemplateRepository,
)
from src.services.cert_engine import (
    generate_blank_contingency_pdf,
    generate_certificate_pdf,
    merge_pdfs_for_print,
)
from src.services.excel_service import export_attendees_excel
from src.services.file_manager import (
    ensure_course_directories,
    open_folder_in_explorer,
)
from src.services.validators import (
    build_certificate_filename,
    format_dni_display,
    sanitize_filename,
)
from src.ui.components.widgets import (
    ACCENT_GOLD,
    BG_PANEL,
    COLOR_SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    SectionCard,
    make_primary_button,
    make_secondary_button,
)


class EmitView(ctk.CTkFrame):
    """Emisión de certificados individuales y herramientas de salida."""

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
        self.template_repo = TemplateRepository()
        self.attendee_repo = AttendeeRepository()
        self._is_emitting = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_summary_and_actions()
        self._build_progress_card()
        self._build_attendees_list()

    def _build_summary_and_actions(self) -> None:
        card = SectionCard(self)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)

        self.lbl_course_info = ctk.CTkLabel(
            card,
            text="Sin Curso Activo seleccionado",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=ACCENT_GOLD,
            anchor="w",
        )
        self.lbl_course_info.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))

        self.lbl_counts = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        self.lbl_counts.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))

        self.btn_emit_all = make_primary_button(
            actions,
            "Emitir Certificados (Presentes)",
            command=self._emit_batch,
            width=230,
        )
        self.btn_emit_all.pack(side="left", padx=(0, 8))

        self.btn_export_excel = make_secondary_button(
            actions,
            "Exportar Nómina Excel",
            fg_color=COLOR_SUCCESS,
            hover_color="#059669",
            command=self._export_excel,
        )
        self.btn_export_excel.pack(side="left", padx=(0, 8))

        self.btn_merge_pdf = make_secondary_button(
            actions,
            "Unir en 1 PDF (Imprenta)",
            command=self._merge_for_print,
        )
        self.btn_merge_pdf.pack(side="left", padx=(0, 8))

        self.btn_blank_cert = make_secondary_button(
            actions,
            "📄 Generar Certificado en Blanco (Contingencia)",
            command=self._emit_blank_contingency,
        )
        self.btn_blank_cert.pack(side="left", padx=(0, 8))

        make_secondary_button(
            actions,
            "Abrir Carpeta",
            command=self._open_certs_folder,
        ).pack(side="right")

    def _build_progress_card(self) -> None:
        card = SectionCard(self)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)

        self.lbl_progress = ctk.CTkLabel(
            card,
            text="Listo para emitir certificados individuales (DNI_Apellido_Nombre.pdf).",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        self.lbl_progress.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 4))

        self.progress_bar = ctk.CTkProgressBar(card, height=12, corner_radius=6)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

    def _build_attendees_list(self) -> None:
        card = SectionCard(self)
        card.grid(row=2, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="Control de Emisión Individual",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        self.list_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.list_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.list_scroll.grid_columnconfigure(0, weight=1)

    def on_show(self) -> None:
        self._refresh_view()

    def _get_course_and_template(self) -> tuple[dict[str, Any], dict[str, Any]] | None:
        cid = self.get_active_course_id()
        if cid is None:
            self.notify("Seleccioná primero un Curso Activo.", "warning")
            return None
        course = self.course_repo.get_by_id(cid)
        if not course:
            self.notify("No se encontró el curso seleccionado.", "error")
            return None

        tpl_id = course.get("template_id")
        tpl = self.template_repo.get_by_id(int(tpl_id)) if tpl_id else None
        if not tpl:
            all_tpls = self.template_repo.list_all()
            if not all_tpls:
                self.notify("No hay plantillas disponibles.", "error")
                return None
            tpl = all_tpls[0]
        return course, tpl

    def _refresh_view(self) -> None:
        for child in self.list_scroll.winfo_children():
            child.destroy()

        cid = self.get_active_course_id()
        if cid is None:
            self.lbl_course_info.configure(text="Sin Curso Activo seleccionado")
            self.lbl_counts.configure(text="")
            return

        course = self.course_repo.get_by_id(cid)
        if not course:
            return

        attendees = self.attendee_repo.list_by_course(cid)
        present = [a for a in attendees if a.get("attended", 1)]
        generated = [a for a in attendees if a.get("cert_generated", 0)]

        tpl_name = "Predeterminada"
        if course.get("template_id"):
            tpl = self.template_repo.get_by_id(int(course["template_id"]))
            if tpl:
                tpl_name = tpl["name"]

        self.lbl_course_info.configure(text=f"[{course['event_type']}] {course['title']}")
        self.lbl_counts.configure(
            text=f"Plantilla: {tpl_name}  •  Inscriptos: {len(attendees)}  •  "
            f"Presentes: {len(present)}  •  Certificados Emitidos: {len(generated)}"
        )

        if not attendees:
            ctk.CTkLabel(
                self.list_scroll,
                text="No hay asistentes inscriptos en este curso.",
                text_color=TEXT_SECONDARY,
            ).grid(row=0, column=0, pady=30)
            return

        for idx, att in enumerate(attendees):
            item = ctk.CTkFrame(
                self.list_scroll, fg_color=BG_PANEL, corner_radius=6, border_width=1, border_color="#334155"
            )
            item.grid(row=idx, column=0, sticky="ew", pady=(0, 6))
            item.grid_columnconfigure(0, weight=1)

            status = "Emitido" if att.get("cert_generated") else "Pendiente"
            att_flag = "Presente" if att.get("attended", 1) else "Ausente"
            txt = f"{att['full_name']}  •  DNI {format_dni_display(att['dni'])}  •  {att_flag}  •  {status}"
            ctk.CTkLabel(
                item,
                text=txt,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_PRIMARY if att.get("attended", 1) else TEXT_SECONDARY,
                anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=12, pady=8)

            make_secondary_button(
                item,
                "Emitir / Re-emitir",
                width=130,
                height=30,
                command=lambda a=att: self._emit_single(a),
            ).grid(row=0, column=1, padx=(4, 12), pady=6)

    def _emit_batch(self) -> None:
        if self._is_emitting:
            return
        pair = self._get_course_and_template()
        if not pair:
            return
        course, tpl = pair

        attendees = [
            a for a in self.attendee_repo.list_by_course(int(course["id"])) if a.get("attended", 1)
        ]
        if not attendees:
            self.notify("No hay asistentes marcados como Presentes para emitir.", "warning")
            return

        _, certs_dir = ensure_course_directories(course["event_date"], course["title"])
        self._is_emitting = True
        self.btn_emit_all.configure(state="disabled")
        self.progress_bar.set(0)

        def _worker() -> None:
            total = len(attendees)
            errors = 0
            for idx, att in enumerate(attendees, start=1):
                try:
                    filename = build_certificate_filename(att["dni"], att["full_name"])
                    out_pdf = certs_dir / filename
                    generate_certificate_pdf(tpl, course, att, out_pdf)
                    self.attendee_repo.mark_certificate_generated(int(att["id"]), str(out_pdf))
                except Exception:
                    errors += 1
                progress = idx / total
                msg = f"Generando {idx}/{total}: {att['full_name']}"
                self.after(0, lambda p=progress, m=msg: self._update_progress(p, m))

            self.after(0, lambda: self._on_batch_done(total, errors, certs_dir))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_progress(self, value: float, text: str) -> None:
        self.progress_bar.set(value)
        self.lbl_progress.configure(text=text)

    def _on_batch_done(self, total: int, errors: int, certs_dir: Path) -> None:
        self._is_emitting = False
        self.btn_emit_all.configure(state="normal")
        self._refresh_view()
        if errors:
            self.lbl_progress.configure(text=f"Completado con {errors} error(es) de {total}.")
            self.notify(f"Emisión finalizada con {errors} errores.", "warning")
        else:
            self.lbl_progress.configure(text=f"¡{total} certificados generados en {certs_dir}!")
            self.notify(f"Se emitieron {total} certificados individuales correctamente.", "success")

    def _emit_single(self, att: dict[str, Any]) -> None:
        if self._is_emitting:
            return
        pair = self._get_course_and_template()
        if not pair:
            return
        course, tpl = pair
        _, certs_dir = ensure_course_directories(course["event_date"], course["title"])

        def _worker() -> None:
            try:
                filename = build_certificate_filename(att["dni"], att["full_name"])
                out_pdf = certs_dir / filename
                generate_certificate_pdf(tpl, course, att, out_pdf)
                self.attendee_repo.mark_certificate_generated(int(att["id"]), str(out_pdf))
                self.after(0, lambda: self._on_single_done(att["full_name"]))
            except Exception as exc:
                self.after(0, lambda err=str(exc): self.notify(f"Error al emitir: {err}", "error"))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_single_done(self, full_name: str) -> None:
        self._refresh_view()
        self.notify(f"Certificado emitido: {full_name}", "success")

    def _export_excel(self) -> None:
        cid = self.get_active_course_id()
        if cid is None:
            self.notify("Seleccioná primero un Curso Activo.", "warning")
            return
        course = self.course_repo.get_by_id(cid)
        if not course:
            return
        course_dir, _ = ensure_course_directories(course["event_date"], course["title"])
        attendees = self.attendee_repo.list_by_course(cid)
        out_xlsx = course_dir / "Nomina_Asistentes.xlsx"
        export_attendees_excel(course, attendees, out_xlsx)
        self.notify(f"Nómina exportada: {out_xlsx.name}", "success")

    def _merge_for_print(self) -> None:
        cid = self.get_active_course_id()
        if cid is None:
            self.notify("Seleccioná primero un Curso Activo.", "warning")
            return
        course = self.course_repo.get_by_id(cid)
        if not course:
            return
        course_dir, _ = ensure_course_directories(course["event_date"], course["title"])
        attendees = self.attendee_repo.list_by_course(cid)
        pdf_paths = [
            a["cert_file_path"]
            for a in attendees
            if a.get("cert_generated") and a.get("cert_file_path") and Path(a["cert_file_path"]).is_file()
        ]
        if not pdf_paths:
            self.notify("Primero emití los certificados individuales antes de unificar.", "warning")
            return

        safe_course = sanitize_filename(course["title"], max_length=40)
        out_pdf = course_dir / f"Lote_Impresion_{safe_course}.pdf"
        merge_pdfs_for_print(pdf_paths, out_pdf)
        self.notify(f"PDF unificado para imprenta generado: {out_pdf.name}", "success")

    def _emit_blank_contingency(self) -> None:
        pair = self._get_course_and_template()
        if not pair:
            return
        course, tpl = pair
        course_dir, _ = ensure_course_directories(course["event_date"], course["title"])
        out_pdf = course_dir / "000_CERTIFICADO_EN_BLANCO.pdf"

        def _worker() -> None:
            try:
                generate_blank_contingency_pdf(tpl, course, out_pdf)
                self.after(
                    0,
                    lambda: self.notify(
                        f"Certificado en blanco de contingencia generado: {out_pdf.name}",
                        "success",
                    ),
                )
            except Exception as exc:
                self.after(
                    0,
                    lambda err=str(exc): self.notify(
                        f"Error al generar certificado en blanco: {err}", "error"
                    ),
                )

        threading.Thread(target=_worker, daemon=True).start()

    def _open_certs_folder(self) -> None:
        cid = self.get_active_course_id()
        if cid is None:
            self.notify("Seleccioná primero un Curso Activo.", "warning")
            return
        course = self.course_repo.get_by_id(cid)
        if not course:
            return
        course_dir, _ = ensure_course_directories(course["event_date"], course["title"])
        open_folder_in_explorer(course_dir)
