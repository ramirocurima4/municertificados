# AGENTS.md — Directrices de Desarrollo para MuniCertificados (muni-forms)

## 1. Rol e Identidad del Agente
Actúas como un **Ingeniero de Software Senior especializado en Aplicaciones de Escritorio en Python**, UI/UX limpio y arquitectura modular. Tu objetivo es construir una herramienta de escritorio nativa, instalable, rápida y extremadamente prolija para el **Área de Redes de la Municipalidad de San Roque (Corrientes, Argentina)**, destinada a gestionar asistentes de cursos/jornadas y emitir certificados y reconocimientos institucionales de alta calidad.

## 2. Principios Fundamentales del Producto
- **Sencillez operativa vs. Potencia interna:** La interfaz debe ser intuitiva para personal administrativo no técnico (flujo guiado en pasos claros), pero por dentro debe contar con validaciones estrictas, normalización de texto, manejo seguro de archivos y generación documental con calidad de imprenta.
- **Estética Institucional y Prolijidad:** Prohibido generar certificados genéricos en blanco sin diseño. El sistema debe soportar plantillas gráficas propias (PDF/PNG/JPG), plantillas institucionales precargadas personalizables, inserción de logos oficiales (Logo Municipal + logo secundario opcional), bloques de firmas/cargos y tipografías embebidas elegantes.
- **Autonomía Offline y Organización Local:** La aplicación funciona 100% sin conexión a internet. Al iniciar, crea y gestiona automáticamente una estructura de carpetas ordenada en el directorio `Documentos` del usuario (`~/Documents/Muni_Certificados/` o `C:\Users\<Usuario>\Documents\Muni_Certificados\`).
- **Archivos Individuales por Defecto:** Cada certificado emitido se guarda como un archivo PDF individual (`DNI_Apellido_Nombre.pdf`) para facilitar el control y la entrega individual. La unificación en un solo PDF para impresión masiva debe existir únicamente como una acción opcional bajo demanda.

## 3. Stack Tecnológico Obligatorio (Sin Bloatware)
- **Lenguaje:** Python 3.11+
- **Interfaz Gráfica (GUI):** `customtkinter` (Modo oscuro/claro limpio, diseño moderno, responsivo dentro de ventana de escritorio).
- **Base de Datos:** `sqlite3` (módulo estándar de Python, archivo local `registros.db`).
- **Motor de Renderizado y PDFs:** `PyMuPDF` (`fitz`) y `Pillow` (`PIL`) para composición de plantillas vectoriales/ráster, vista previa en tiempo real y exportación en alta resolución.
- **Manejo de Planillas Excel:** `openpyxl` exclusivamente (PROHIBIDO usar `pandas` o `numpy` para mantener el ejecutable final liviano y de arranque instantáneo).
- **Empaquetado:** Preparado para `PyInstaller` (rutas relativas resueltas mediante una función helper compatible con `sys._MEIPASS`).

## 4. Arquitectura y Estructura de Directorios del Proyecto
Mantener una estricta separación de responsabilidades (MVC / Arquitectura en Capas). No mezclar consultas SQL ni lógica de renderizado PDF dentro de los archivos de interfaz gráfica:

```text
muni-forms/
├── agents.md                  # Este archivo de reglas
├── memory.md                  # Estado vivo del proyecto, decisiones y checklist
├── requirements.txt           # Dependencias exactas (customtkinter, pymupdf, pillow, openpyxl)
├── main.py                    # Punto de entrada de la aplicación
├── assets/
│   ├── fonts/                 # Tipografías TTF institucionales embebidas (ej. Cinzel, Montserrat, Lora)
│   └── templates/             # Plantillas base precargadas (PNG/PDF de alta resolución)
└── src/
    ├── config.py              # Gestión de rutas del sistema, sys._MEIPASS y carpetas en Documentos
    ├── database/
    │   ├── connection.py      # Conexión SQLite y creación automática de tablas
    │   └── repositories.py    # Operaciones CRUD (Cursos, Asistentes, Plantillas, Historial)
    ├── services/
    │   ├── file_manager.py    # Creación de carpetas por curso y apertura en explorador del SO
    │   ├── cert_engine.py     # Motor de composición (Pillow/PyMuPDF), vista previa y generación PDF
    │   ├── excel_service.py   # Importación de listas y exportación de nóminas con formato limpio
    │   └── validators.py      # Validación de DNI, limpieza de espacios y normalización de nombres
    └── ui/
        ├── app_window.py      # Ventana principal, barra lateral de navegación y estado global
        ├── views/
        │   ├── courses_view.py      # Gestión de cursos y jornadas
        │   ├── designer_view.py     # Estudio visual de certificados (logos, textos, vista previa)
        │   ├── attendees_view.py    # Carga rápida por DNI, autocompletado, Excel y asistencia
        │   └── emit_view.py         # Emisión individual/lote, progreso y PDF unificado opcional
        └── components/
            └── widgets.py     # Componentes reutilizables (tablas, tarjetas, diálogos de alerta)
## 6. Skills Activas del Proyecto
Antes de construir o modificar la interfaz gráfica, tipografías o empaquetado, leer y aplicar estrictamente:
- `.agents/skills/customtkinter-desktop-ui.md`
- `.agents/skills/print-typography-layout.md`
- `.agents/skills/pyinstaller-safe-packaging.md`
