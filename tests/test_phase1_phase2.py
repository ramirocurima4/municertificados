"""Pruebas unitarias e integración para Fase 1 y Fase 2 de MuniCertificados."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

from src.config import (
    A4_LANDSCAPE_HEIGHT_PT,
    A4_LANDSCAPE_HEIGHT_PX,
    A4_LANDSCAPE_WIDTH_PT,
    A4_LANDSCAPE_WIDTH_PX,
    ASSETS_LOGOS_DIR,
    FILEDIALOG_ASSET_TYPES,
    PRESET_TEMPLATES_DIR,
    SUPPORTED_ASSET_EXTENSIONS,
)
from src.database.connection import init_db
from src.database.repositories import (
    AttendeeRepository,
    CourseRepository,
    PersonRepository,
    TemplateRepository,
)
from src.services.cert_engine import (
    generate_blank_contingency_pdf,
    generate_certificate_pdf,
    list_available_fonts,
    list_institutional_logos,
    load_visual_asset,
    merge_pdfs_for_print,
    remove_white_background,
    render_preview_image,
    tint_logo_image,
)
from src.services.excel_service import (
    export_attendees_excel,
    import_attendees_from_excel,
)
from src.services.validators import (
    build_certificate_filename,
    clean_dni,
    format_dni_display,
    is_supported_asset,
    is_valid_dni,
    normalize_name,
    parse_whatsapp_list,
)


class TestValidatorsAndConfig(unittest.TestCase):
    def test_supported_extensions(self) -> None:
        for ext in (".pdf", ".png", ".jpg", ".jpeg", ".webp"):
            self.assertIn(ext, SUPPORTED_ASSET_EXTENSIONS)
            self.assertTrue(is_supported_asset(f"archivo{ext}"))
            self.assertTrue(is_supported_asset(f"ARCHIVO{ext.upper()}"))
        self.assertFalse(is_supported_asset("archivo.bmp"))
        self.assertIn("*.webp", FILEDIALOG_ASSET_TYPES[0][1])

    def test_dni_and_name_normalization(self) -> None:
        self.assertEqual(clean_dni("35.123.456 "), "35123456")
        self.assertTrue(is_valid_dni("35.123.456"))
        self.assertFalse(is_valid_dni("123"))
        self.assertEqual(format_dni_display("35123456"), "35.123.456")
        self.assertEqual(normalize_name("  juan   perez de la cruz "), "Juan Perez de la Cruz")
        self.assertEqual(
            build_certificate_filename("35.123.456", "maría josé gonzález"),
            "35123456_Maria_Jose_Gonzalez.pdf",
        )

    def test_parse_whatsapp_list(self) -> None:
        raw_whatsapp = """
        *Listado de Inscriptos - Curso Cultivos*
        | N.º | Apellido y nombre | DNI |
        |---|---|---|
        | 1 | Montenegro Ricardo | 36.303.823 |
        2. maría de los ángeles pérez - 28999111
        Gómez Juan Carlos 40.111.222
        • 35.444.555 - Fernández Lucía
        """
        parsed = parse_whatsapp_list(raw_whatsapp)
        self.assertEqual(len(parsed), 4)
        self.assertEqual(
            parsed[0], {"dni": "36303823", "full_name": "Montenegro Ricardo"}
        )
        self.assertEqual(
            parsed[1],
            {"dni": "28999111", "full_name": "María de los Ángeles Pérez"},
        )
        self.assertEqual(
            parsed[2], {"dni": "40111222", "full_name": "Gómez Juan Carlos"}
        )
        self.assertEqual(
            parsed[3], {"dni": "35444555", "full_name": "Fernández Lucía"}
        )


class TestDatabaseAndCertEngine(unittest.TestCase):
    def test_db_seed_crud_and_certificate_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            db_path = tmp_dir / "test_muni.db"
            init_db(db_path)

            tpl_repo = TemplateRepository(db_path)
            course_repo = CourseRepository(db_path)
            person_repo = PersonRepository(db_path)
            att_repo = AttendeeRepository(db_path)

            presets = tpl_repo.list_all()
            self.assertEqual(len(presets), 13)
            for tpl in presets:
                self.assertTrue(Path(tpl["bg_path"]).is_file())

            # Crear logo JPG con fondo blanco y firma WEBP + fondo PDF de prueba
            logo_jpg = tmp_dir / "logo_muni.jpg"
            img_logo = Image.new("RGB", (300, 300), "white")
            draw_logo = ImageDraw.Draw(img_logo)
            draw_logo.ellipse((40, 40, 260, 260), fill="#14325C")
            img_logo.save(logo_jpg, format="JPEG")

            sig_webp = tmp_dir / "firma.webp"
            img_sig = Image.new("RGB", (400, 140), "white")
            draw_sig = ImageDraw.Draw(img_sig)
            draw_sig.line([(40, 100), (360, 40)], fill="#111111", width=8)
            img_sig.save(sig_webp, format="WEBP")

            # Verificar carga multi-formato (.jpg, .webp, .png, .pdf) y remoción de fondo blanco
            loaded_logo = load_visual_asset(logo_jpg, transparent=True)
            transparent_logo = remove_white_background(loaded_logo, threshold=235)
            self.assertEqual(transparent_logo.getpixel((5, 5))[3], 0)
            self.assertGreater(transparent_logo.getpixel((150, 150))[3], 200)

            self.assertEqual(load_visual_asset(sig_webp).mode, "RGBA")

            sample_pdf_bg = tmp_dir / "fondo_custom.pdf"
            doc_bg = pymupdf.open()
            doc_bg.new_page(width=A4_LANDSCAPE_WIDTH_PT, height=A4_LANDSCAPE_HEIGHT_PT)
            doc_bg.save(str(sample_pdf_bg))
            doc_bg.close()
            loaded_pdf_bg = load_visual_asset(
                sample_pdf_bg,
                target_size=(A4_LANDSCAPE_WIDTH_PX, A4_LANDSCAPE_HEIGHT_PX),
                transparent=True,
            )
            self.assertEqual(
                loaded_pdf_bg.size, (A4_LANDSCAPE_WIDTH_PX, A4_LANDSCAPE_HEIGHT_PX)
            )

            # Configurar plantilla personalizada con 4 logos, alineación izquierda y pastilla de curso
            editorial_tpl = next(
                t for t in presets if "Agro" in t["name"]
            )
            cfg = editorial_tpl["config"]
            cfg["logos"]["main"]["remove_white_bg"] = True
            cfg["logos"]["logo_3"]["image_path"] = str(logo_jpg)
            cfg["logos"]["logo_3"]["remove_white_bg"] = True
            cfg["logos"]["logo_4"]["image_path"] = str(logo_jpg)
            cfg["logos"]["logo_4"]["remove_white_bg"] = True
            cfg["signatures"][0]["image_path"] = str(sig_webp)
            cfg["signatures"][0]["remove_white_bg"] = True

            custom_tpl_id = tpl_repo.create(
                name="Plantilla Prueba San Roque",
                bg_path=str(PRESET_TEMPLATES_DIR / "plantilla_agro_cultivos.png"),
                logo_main_path=str(logo_jpg),
                logo_sec_path=str(logo_jpg),
                config=cfg,
            )
            # Re-ejecutar init_db para verificar que seed_preset_templates no borra plantillas del usuario
            init_db(db_path)
            self.assertEqual(len(tpl_repo.list_all()), 14)
            custom_tpl = tpl_repo.get_by_id(custom_tpl_id)
            assert custom_tpl is not None

            course_id = course_repo.create(
                title="Operación y Mantenimiento de Redes",
                event_type="Curso",
                event_date="25 de noviembre de 2026",
                hours="12 horas reloj",
                location="San Roque, Corrientes",
                template_id=custom_tpl_id,
                folder_path=str(tmp_dir / "curso_redes"),
            )
            course = course_repo.get_by_id(course_id)
            assert course is not None

            person_repo.upsert(dni="35.123.456", full_name="juan carlos pérez")
            person_repo.upsert(
                dni="28999111",
                full_name="maría de los ángeles fernández-villarreal",
            )
            att1_id = att_repo.enroll(course_id, "35123456")
            att2_id = att_repo.enroll(course_id, "28999111")
            self.assertEqual(len(att_repo.list_by_course(course_id)), 2)

            p1 = person_repo.get_by_dni("35123456")
            p2 = person_repo.get_by_dni("28999111")
            assert p1 is not None and p2 is not None

            preview = render_preview_image(custom_tpl, course, p1, max_width=800)
            self.assertEqual(preview.width, 800)

            pdf1 = tmp_dir / build_certificate_filename(p1["dni"], p1["full_name"])
            pdf2 = tmp_dir / build_certificate_filename(p2["dni"], p2["full_name"])
            generate_certificate_pdf(custom_tpl, course, p1, pdf1)
            generate_certificate_pdf(custom_tpl, course, p2, pdf2)
            att_repo.mark_certificate_generated(att1_id, str(pdf1))
            att_repo.mark_certificate_generated(att2_id, str(pdf2))

            self.assertTrue(pdf1.is_file())
            self.assertTrue(pdf2.is_file())

            with pymupdf.open(str(pdf1)) as d1:
                self.assertEqual(len(d1), 1)
                self.assertAlmostEqual(d1[0].rect.width, A4_LANDSCAPE_WIDTH_PT, delta=1.0)
                self.assertAlmostEqual(d1[0].rect.height, A4_LANDSCAPE_HEIGHT_PT, delta=1.0)

            merged_pdf = tmp_dir / "Lote_Impresion.pdf"
            merge_pdfs_for_print([pdf1, pdf2], merged_pdf)
            with pymupdf.open(str(merged_pdf)) as dm:
                self.assertEqual(len(dm), 2)

            # Verificar catálogo de fuentes (>= 15 archivos TTF) y logos institucionales en assets/logos/
            fonts = list_available_fonts()
            self.assertGreaterEqual(len(fonts), 15)

            inst_logos = list_institutional_logos()
            self.assertGreaterEqual(len(inst_logos), 3)
            self.assertTrue((ASSETS_LOGOS_DIR / "logo_san_roque_escudo.png").is_file())
            self.assertTrue((ASSETS_LOGOS_DIR / "logo_avanzamos_juntos.png").is_file())
            self.assertTrue((ASSETS_LOGOS_DIR / "logo_san_roque_puente.png").is_file())

            # Verificar que las plantillas modernas traen por defecto logo_avanzamos_juntos y logo_san_roque_escudo
            self.assertIn("logo_avanzamos_juntos.png", editorial_tpl["logo_main_path"])
            self.assertIn("logo_san_roque_escudo.png", editorial_tpl["logo_sec_path"])
            self.assertTrue(editorial_tpl["config"].get("show_dni", True))
            self.assertEqual(editorial_tpl["config"]["body"]["size"], 44)
            self.assertEqual(editorial_tpl["config"]["body"]["color"], "#1E293B")
            self.assertIn(
                "EN RECONOCIMIENTO A SU PARTICIPACIÓN EN",
                editorial_tpl["config"]["body"]["text"],
            )

            # Verificar renderizado con show_dni=False (no debe fallar ni dibujar la línea DNI)
            custom_tpl["config"]["show_dni"] = False
            preview_no_dni = render_preview_image(custom_tpl, course, p1, max_width=400)
            self.assertEqual(preview_no_dni.width, 400)
            custom_tpl["config"]["show_dni"] = True

            # Verificar teñido de logo conservando transparencia alfa
            tinted = tint_logo_image(transparent_logo, "#0284C7")
            self.assertEqual(tinted.getpixel((5, 5))[3], 0)
            center_px = tinted.getpixel((150, 150))
            self.assertEqual(center_px[:3], (2, 132, 199))
            self.assertGreater(center_px[3], 200)

            # Verificar Certificado en Blanco de Contingencia (000_CERTIFICADO_EN_BLANCO.pdf)
            blank_pdf = tmp_dir / "000_CERTIFICADO_EN_BLANCO.pdf"
            generate_blank_contingency_pdf(custom_tpl, course, blank_pdf)
            self.assertTrue(blank_pdf.is_file())
            with pymupdf.open(str(blank_pdf)) as db_pdf:
                self.assertEqual(len(db_pdf), 1)

            # Verificar exportación e importación Excel (openpyxl) con columna Perfil/Rol del formulario web
            xlsx_path = tmp_dir / "Nomina_Asistentes.xlsx"
            rows = att_repo.list_by_course(course_id)
            export_attendees_excel(course, rows, xlsx_path)
            self.assertTrue(xlsx_path.is_file())

            import openpyxl

            in_xlsx = tmp_dir / "entrada.xlsx"
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["DNI", "Apellido y Nombre", "Perfil", "Institucion", "Email"])
            ws.append(
                [
                    "40.111.222",
                    "gómez lucía",
                    "Docente",
                    "ISFD San Roque",
                    "lucia@sanroque.gob.ar",
                ]
            )
            wb.save(str(in_xlsx))
            wb.close()

            imported, warnings = import_attendees_from_excel(in_xlsx)
            self.assertEqual(len(imported), 1)
            self.assertEqual(len(warnings), 0)
            self.assertEqual(imported[0]["dni"], "40111222")
            self.assertEqual(imported[0]["full_name"], "Gómez Lucía")
            self.assertEqual(imported[0]["profile"], "Docente")
            self.assertEqual(
                imported[0]["institution_or_role"], "Docente — ISFD San Roque"
            )


if __name__ == "__main__":
    unittest.main()
