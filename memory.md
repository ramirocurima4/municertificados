#### 2. Archivo `memory.md` (Contexto, Esquema y Hoja de Ruta Viva)

```markdown
# MEMORY.md — Estado Vivo del Proyecto MuniCertificados

## 1. Contexto del Proyecto
- **Nombre del Software:** MuniCertificados (Repositorio: `muni-forms`)
- **Cliente / Usuarios Finales:** Área de Redes de la Municipalidad de San Roque, Corrientes, Argentina.
- **Problema a Resolver:** Actualmente el personal registra manualmente a los asistentes de cursos y jornadas y confecciona los diplomas uno por uno. Se requiere un software de escritorio instalable que agilice la carga, mantenga un historial de personas (autocompletado por DNI), permita personalizar diseños institucionales con logos y firmas, y genere certificados individuales en PDF organizados automáticamente en carpetas locales.
- **Requisito Clave de Calidad:** Los certificados deben lucir altamente profesionales y prolijos (marcos institucionales, escudo municipal, tipografías elegantes, alineación matemática centrada), evitando el aspecto de documentos genéricos en blanco.

## 2. Arquitectura de Carpetas Generadas en la PC del Usuario
Al ejecutarse por primera vez, el sistema crea en `Documents/Muni_Certificados/`:
- `01_Plantillas_y_Logos/`: Copia local de fondos personalizados, logos de la Municipalidad y firmas escaneadas.
- `02_Cursos_y_Jornadas/<YYYY-MM_Nombre_Curso>/`:
  - `Certificados_Individuales/`: Archivos PDF individuales nombrados `DNI_Apellido_Nombre.pdf`.
  - `Nomina_Asistentes.xlsx`: Planilla Excel institucional con todos los inscriptos, estado de asistencia y fecha de emisión.
  - `(Opcional bajo demanda) Lote_Impresion_<Nombre_Curso>.pdf`: Archivo unificado generado solo si el usuario presiona el botón de unir para imprenta.
- `Base_Datos/muni_certificados.db`: Base de datos SQLite local.

## 3. Esquema Inicial de Base de Datos (SQLite)
1. **`templates` (Plantillas de Diseño):**
   - `id`, `name`, `is_preset` (boolean), `bg_path`, `logo_main_path`, `logo_sec_path`, `config_json` (coordenadas X/Y, alineación centrada, fuentes, tamaños, colores hex, texto de cuerpo con placeholders `{nombre}`, `{dni}`, `{curso}`, `{fecha}`, `{carga_horaria}`, y configuración de firmas).
2. **`courses` (Cursos y Jornadas):**
   - `id`, `title`, `event_type` (Curso / Jornada / Taller / Reconocimiento), `event_date`, `hours`, `location`, `template_id`, `folder_path`, `created_at`.
3. **`people` (Padrón Histórico Local para Autocompletado):**
   - `dni` (PK), `full_name`, `email`, `phone`, `institution_or_role`, `updated_at`.
4. **`attendees` (Inscripciones y Asistencia por Curso):**
   - `id`, `course_id` (FK), `dni` (FK), `attended` (boolean, default 1), `cert_generated` (boolean, default 0), `cert_file_path`, `generated_at`.

## 4. Plan de Desarrollo por Fases (Checklist)
- [x] **Fase 1: Cimientos y Base de Datos**
  - Configurar estructura de carpetas del proyecto (`src/`, `assets/`), `requirements.txt` y `src/config.py` (con soporte `sys._MEIPASS` y creación automática de `Documents/Muni_Certificados`).
  - Implementar `src/database/connection.py` y `repositories.py` con las 4 tablas y consultas CRUD.
  - Crear `src/services/validators.py` (validación de DNI y normalización de nombres en Formato Título).
- [x] **Fase 2: Motor de Certificados y Plantillas Institucionales**
  - Generar/incluir 3 plantillas institucionales base de alta calidad en `assets/templates/` y fuentes TTF elegantes en `assets/fonts/`.
  - Implementar `src/services/cert_engine.py` usando `Pillow` y `PyMuPDF` con centrado matemático exacto, autoajuste de fuente para nombres largos, soporte de logos, firmas y vista previa en memoria.
  - Implementar función opcional `merge_pdfs_for_print()` para unir certificados bajo demanda.
- [x] **Fase 3: Interfaz Gráfica (CustomTkinter)**
  - Construir `app_window.py` con navegación lateral limpia e identidad visual institucional (azul oscuro/dorado/gris pizarra).
  - Implementar `courses_view.py` (crear/editar jornadas y abrir carpeta local con un clic).
  - Implementar `designer_view.py` (Estudio de Certificados: selector de plantilla precargada o propia, carga de Logo Municipal, editor de textos/variables, controles de posición/tamaño/color y vista previa en vivo).
  - Implementar `attendees_view.py` (carga rápida DNI -> autocompletado -> guardar, importación desde Excel con `openpyxl`, filtro/buscador y check de asistencia).
  - Implementar `emit_view.py` (emisión en lote de PDFs individuales con barra de progreso, re-emisión individual, exportación de `Nomina_Asistentes.xlsx` y botón opcional de PDF unificado).
- [x] **Fase 4: Pruebas y Empaquetado**
  - Verificar flujo completo en Linux y Windows.
  - Generar archivo `.spec` de PyInstaller para compilar un `.exe` limpio y autocontenido.

## 5. Registro de Decisiones Técnicas
- **2026-11-25:** Se descarta versión web para `muni-forms` y se define aplicación de escritorio nativa en Python (`CustomTkinter` + `PyMuPDF` + `Pillow` + `OpenPyXL` + `SQLite`).
- **2026-11-25:** Se descarta `pandas` para reducir en >80 MB el peso del instalador y acelerar el arranque.
- **2026-11-25:** Se establece generación de PDFs individuales por defecto y PDF unificado solo como herramienta opcional para impresión.
- **2026-11-25:** Se amplía el motor editorial (`cert_engine.py` y `designer_view.py`) para soportar hasta 4 logos con posición X/Y y tamaño libres, alineación flexible (`Izquierda` / `Centro`), franja de curso con pastilla de color destacada (`course_banner`), línea inferior opcional bajo el nombre, selector visual de colores (`ColorPickerButton` con 12 swatches institucionales + selector nativo) y 8 plantillas precargadas a 300 DPI (3 clásicas + 5 modernas editoriales temáticas).
- **2026-11-25:** Se rediseñan y amplían las plantillas institucionales (`scripts/generate_templates.py` y `src/database/connection.py`) replicando fielmente el formato oficial de **Mosaico Geométrico de la Municipalidad de San Roque** (franja vertical izquierda, mosaico superior derecho con sol naciente, cuartos de círculo e íconos vectoriales minimalistas por temática, matrices de puntos decorativos y franja de curso en color). Se precargan **13 plantillas listas para usar** (10 temáticas Muni San Roque: Agro/Cultivos, Docentes/Educación, Guías Turísticos/Turismo, IA/Redes/IT, Deportes/Recreación, Salud/RCP, Emprendedores/Oficios, Cultura/Arte, Ambiente/Ecología e Institucional General + 3 Clásicas) y se simplifica `designer_view.py` con pestañas compactas para los 4 logos y las 2 firmas y un panel colapsable `"⚙️ Mostrar Ajustes Avanzados"` oculto por defecto para mantener la interfaz limpia y simple.
- **2026-11-25:** Se integran los 3 logos institucionales transparentes en `assets/logos/` (`logo_san_roque_escudo.png`, `logo_avanzamos_juntos.png`, `logo_san_roque_puente.png`) expuestos vía `ASSETS_LOGOS_DIR` en `src/config.py`, con selector rápido `"Logos Institucionales..."` en los 4 slots de logos, función de teñido de color con preservación de canal alfa (`tint_logo_image`), pre-asignación por defecto de `#Avanzamos Juntos` y `Escudo San Roque` en las plantillas modernas, botón `"📄 Generar Certificado en Blanco (Contingencia)"` (`000_CERTIFICADO_EN_BLANCO.pdf`) en `emit_view.py` y soporte de columna `"Perfil"` / `"Rol"` (`Docente`/`Estudiante`/`Vecino`) en `excel_service.py` y `PersonRepository.upsert()`. Queda pendiente únicamente la **Fase 4 (Empaquetado `.exe` con PyInstaller)**.
- **2026-11-25:** Se optimiza la legibilidad del bloque de Texto de Reconocimiento (`body`) en las 10 plantillas "Mosaico Muni San Roque" y en `cert_engine.py`: tamaño por defecto aumentado a `44 px`, fuente estática limpia (`Poppins-Regular.ttf` / `Poppins-Bold.ttf`), color gris carbón de alto contraste (`#1E293B`), altura de editor `height=76` en `designer_view.py` y texto por defecto `"EN RECONOCIMIENTO A SU PARTICIPACIÓN EN\n**{CURSO}.**"` con prevención automática de duplicación de tipo de evento en `_format_template_string`.
- **2026-11-25:** Se agrega la opción booleana `show_dni` por plantilla en `src/database/connection.py`, `src/services/cert_engine.py` y el switch `"Mostrar D.N.I. debajo del nombre"` en la sección de textos de `src/ui/views/designer_view.py`, permitiendo mostrar u ocultar la línea `D.N.I. N° ...` en la vista previa y en los PDFs emitidos (además de ocultarla siempre en `000_CERTIFICADO_EN_BLANCO.pdf`).
- **2026-11-25:** Se incorpora la herramienta de carga rápida `"📋 Pegar desde WhatsApp"` (`parse_whatsapp_list` en `src/services/validators.py` y diálogo modal `CTkToplevel` con vista previa de detección en `src/ui/views/attendees_view.py`), capaz de extraer automáticamente pares de Nombre y DNI desde tablas o listas pegadas de mensajes de WhatsApp y registrarlos en `people` y `attendees` informando nuevos cargados y duplicados.
- **2026-11-25:** Se redacta el documento institucional `README.md` para presentación y despliegue en el Área de Modernización y Redes, junto con `requirements.txt` actualizado y los scripts de arranque rápido `iniciar_windows.bat` e `iniciar_linux.sh`.
- **2026-11-25:** Se completa la **Fase 4 (Empaquetado `.exe` e Instalador Profesional para Windows)**: generación automática de `assets/app_icon.ico` desde `logo_san_roque_escudo.png`, archivo `MuniCertificados.spec` (`--onedir`, `console=False`, recursos `assets/` y `customtkinter`), script de instalador `installer.iss` (Inno Setup 6 en español con preservación de `Documentos\Muni_Certificados`), script local `build_installer.bat` y workflow automatizado en la nube `.github/workflows/build-windows.yml` para compilar y publicar `Setup_MuniCertificados_v1.0.exe` como Artifact en GitHub Actions.
