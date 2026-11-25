# MuniCertificados — Sistema Institucional de Gestión de Asistentes y Emisión de Diplomas

**Municipalidad de San Roque (Corrientes, Argentina)**  
*Desarrollado para el Área de Modernización y Redes*

---

## 1. Descripción General y Problema que Resuelve

En la gestión cotidiana de cursos, capacitaciones, talleres y jornadas municipales, el registro manual de inscriptos y la confección artesanal de certificados uno por uno generan demoras operativas, errores de tipeo en nombres o D.N.I., inconsistencias estéticas y cuellos de botella al momento de la entrega presencial.

**MuniCertificados** es una aplicación de escritorio nativa, liviana y **100% autónoma (Offline)** diseñada específicamente para resolver esta problemática:

- **Elimina el llenado manual:** Automatiza la composición gráfica a calidad de imprenta (**300 DPI**, formato **A4 Apaisado** de `3508 x 2480 px`) generando decenas o cientos de certificados en segundos.
- **Unifica la identidad visual municipal:** Incorpora el diseño oficial de **Mosaico Geométrico de la Municipalidad de San Roque** adaptado a cada área temática (Producción/Agro, Educación, Turismo, Tecnología/IA, Deportes, Salud, Emprendedores, Cultura, Ambiente e Institucional).
- **Construye un Padrón Histórico Local:** Cada vecino, docente o participante cargado queda registrado por su D.N.I. en la base de datos local; en futuros cursos, al ingresar su documento, el sistema autocompleta instantáneamente su nombre, institución y contacto.

---

## 2. Características Principales

### 🎨 Catálogo de 13 Plantillas Institucionales a 300 DPI
- **10 Plantillas Temáticas *"Mosaico Muni San Roque"*:** Diseñadas siguiendo el formato oficial municipal (franja vertical izquierda, mosaico geométrico superior derecho con sol naciente e iconografía vectorial propia de cada rubro, matrices de puntos decorativos y franja de curso en color):
  1. *Agro, Cultivos y Producción* (Verde oliva/lima y ocre — hojas botánicas y brote en suelo)
  2. *Docentes y Educación* (Azul institucional, celeste y oro — libro abierto y birrete)
  3. *Guías Turísticos y Turismo* (Turquesa esteros y naranja — rosa de los vientos y pin sobre río)
  4. *Inteligencia Artificial, Redes e IT* (Azul profundo y cian — red neuronal y microchip)
  5. *Deportes y Recreación* (Azul dinámico y naranja — trofeo y medalla)
  6. *Salud, RCP y Bienestar* (Verde sanitario y esmeralda — cruz de salud y pulso ECG)
  7. *Emprendedores, Oficios y Comercio* (Terracota y azul marino — lámpara de ideas y barras de crecimiento)
  8. *Cultura, Arte y Música* (Púrpura cultural y oro — corcheas musicales y estrella cultural)
  9. *Ambiente, Ecología y Reciclaje* (Verde bosque y tierra — flora y naturaleza)
  10. *Institucional General* (Azul marino municipal y oro — edificio municipal y escudo)
- **3 Plantillas Clásicas Ornamentales:** *Clásico Institucional (Azul y Oro)*, *Moderno Municipal (Verde y Pizarra)* y *Distinción Solemne (Borgoña y Dorado)* para actos protocolares.

### 🖌️ Estudio Visual de Diplomas (Modo Simple + Modo Avanzado)
- **Modo Simple Guiado:** Pensado para uso administrativo inmediato sin complejidades técnicas.
- **Logos Oficiales Precargados (Hasta 4 Logos simultáneos):** Incluye de fábrica en `assets/logos/` los emblemas transparentes `# Avanzamos Juntos`, `Escudo San Roque Municipio` y `San Roque Puente`, seleccionables con 1 clic además de permitir cargar logos externos (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`) como INTA o ISFD.
- **Teñido Inteligente y Remoción de Fondo Blanco:** Permite quitar el fondo blanco de logos o firmas en JPG y **teñir cualquier logo del color de la plantilla** conservando su transparencia alfa intacta.
- **Paleta Visual de Colores (`ColorPickerButton`):** 12 muestras rápidas (*swatches*) con los colores oficiales municipales y selector cromático completo.
- **Opciones Editoriales Flexibles:** Switch para **mostrar u ocultar el D.N.I.** debajo del nombre, franja destacada de curso con pastilla de color, configuración de 1 o 2 firmas y **Modo Avanzado desplegable** para control fino de coordenadas `X/Y`, alineación (`Izquierda` / `Centro`) y más de **15 familias tipográficas `.ttf` embebidas**.

### ⚡ Carga Ultra-Rápida de Asistentes
- **📋 Pegar desde WhatsApp:** Herramienta exclusiva que permite copiar un mensaje, lista numerada o tabla directamente desde un chat de WhatsApp y pegarlo en la aplicación. El sistema detecta y separa automáticamente los nombres y números de D.N.I., normaliza mayúsculas/minúsculas y descarta encabezados.
- **📥 Importación Masiva desde Excel (`.xlsx`):** Detección automática de columnas (`DNI`, `Apellido y Nombre`, `Perfil/Rol` como *Docente / Estudiante / Vecino*, `Institución`, `Email`, `Teléfono`), totalmente compatible con planillas descargadas de formularios web de pre-inscripción.
- **Autocompletado Histórico por D.N.I.:** Navegación rápida con tecla `<Enter>` para carga continua sin usar el mouse.

### 📄 Emisión Profesional y Contingencia
- **PDFs Individuales por Defecto:** Genera un archivo `DNI_Apellido_Nombre.pdf` por cada asistente presente, facilitando el envío digital o control individual.
- **PDF Unificado para Imprenta (Opcional):** Une en 1 clic todos los certificados del curso en un único documento multipágina `Lote_Impresion_<Curso>.pdf`.
- **Certificado en Blanco de Contingencia:** Botón `"📄 Generar Certificado en Blanco (Contingencia)"` que emite `000_CERTIFICADO_EN_BLANCO.pdf` con todos los datos, logos y firmas del evento pero dejando libre el espacio y la línea del nombre para imprevistos en el acto presencial.
- **Exportación de Nómina Oficial:** Genera `Nomina_Asistentes.xlsx` con encabezado institucional y estado de asistencia/emisión.

### 🔒 100% Offline, Seguro y Ordenado
- Funciona sin conexión a internet sobre una base de datos local **SQLite** (`muni_certificados.db`).
- Incluye botón de **Copia de Seguridad de Base de Datos** en la barra lateral.
- Organiza todos los archivos automáticamente en la carpeta `Documentos/Muni_Certificados/` del usuario:
  ```text
  Documentos/Muni_Certificados/
  ├── 01_Plantillas_y_Logos/
  ├── 02_Cursos_y_Jornadas/
  │   └── 2026-11_Nombre_Del_Curso/
  │       ├── Certificados_Individuales/
  │       │   └── 36303823_Montenegro_Ricardo.pdf
  │       ├── 000_CERTIFICADO_EN_BLANCO.pdf
  │       ├── Nomina_Asistentes.xlsx
  │       └── Lote_Impresion_Nombre_Del_Curso.pdf
  └── Base_Datos/
      └── muni_certificados.db
  ```

---

## 3. Guía Rápida de Instalación y Prueba (Paso a Paso)

### Requisitos Previos
- **Python 3.11 o superior** instalado en el equipo.
  - *En Windows:* Descargar desde [python.org](https://www.python.org/downloads/) marcando la casilla **"Add Python to PATH"** al instalar.
  - *En Linux (Ubuntu/Debian):* Asegurarse de tener los paquetes `python3-venv` y `python3-tk` (`sudo apt install -y python3-venv python3-tk`).

### Opción A: Inicio Automático en 1 Clic (Recomendado)
El repositorio incluye scripts de arranque que crean el entorno virtual `.venv`, instalan las librerías necesarias e inician la interfaz gráfica automáticamente:

- **En Windows 10 / 11:** Hacer doble clic sobre el archivo **`iniciar_windows.bat`**.
- **En Linux:** Abrir una terminal en la carpeta del proyecto y ejecutar:
  ```bash
  ./iniciar_linux.sh
  ```

### Opción B: Instalación Manual por Consola

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO> muni-forms
   cd muni-forms
   ```

2. **Crear y activar el entorno virtual:**
   - En **Windows (PowerShell / CMD):**
     ```bat
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - En **Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

---

## 4. Flujo de Uso Recomendado en 4 Pasos

1. **Paso 1 — Crear el Curso o Jornada (`1. Cursos y Jornadas`):**
   Completar el título del evento (ej. *Cultivos Hidropónicos*), tipo (*Capacitación*, *Curso*, *Jornada*), fecha, carga horaria y plantilla temática inicial. Al guardar, queda seleccionado como **Curso Activo**.
2. **Paso 2 — Personalizar el Diploma (`2. Diseño de Diplomas`):**
   Verificar en la vista previa en vivo la plantilla temática elegida, seleccionar o ajustar los **Logos Institucionales** del pie (y los de instituciones articuladoras como INTA/ISFD), definir el cargo de la firma y elegir si se desea mostrar u ocultar el D.N.I.
3. **Paso 3 — Cargar la Lista de Asistentes (`3. Asistentes y Lista`):**
   Cargar a los participantes con un clic mediante **"📋 Pegar desde WhatsApp"**, **"📥 Importar desde Excel (.xlsx)"** o mediante la carga rápida por D.N.I., y verificar los tildes de asistencia (*Presente*).
4. **Paso 4 — Emitir Certificados (`4. Emitir Certificados`):**
   Presionar **"Emitir Certificados (Presentes)"** para generar todos los PDFs individuales a 300 DPI. Opcionalmente, exportar la planilla oficial `Nomina_Asistentes.xlsx`, generar el `000_CERTIFICADO_EN_BLANCO.pdf` de contingencia o unir todo en un solo PDF para imprenta.

---

## 5. Arquitectura del Proyecto y Hoja de Ruta (Fase 4)

El sistema sigue una arquitectura modular en capas (sin dependencias pesadas como `pandas`) preparada para empaquetado nativo:

```text
muni-forms/
├── main.py                    # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias livianas (customtkinter, pillow, pymupdf, openpyxl, numpy)
├── MuniCertificados.spec      # Especificación de compilación PyInstaller (--onedir, sin consola)
├── installer.iss              # Script de instalador oficial Windows (Inno Setup 6)
├── build_installer.bat        # Compilador local en 1 clic (PyInstaller + Inno Setup)
├── iniciar_windows.bat        # Arranque automático desde código fuente en Windows 10/11
├── iniciar_linux.sh           # Arranque automático desde código fuente en Linux
├── .github/workflows/
│   └── build-windows.yml      # Compilación automática en la nube (GitHub Actions -> Windows .exe)
├── assets/
│   ├── app_icon.ico           # Ícono oficial multi-resolución con el Escudo Municipal
│   ├── fonts/                 # 25 archivos tipográficos TTF embebidos (15+ familias)
│   ├── logos/                 # Logos oficiales transparentes de la Municipalidad de San Roque
│   └── templates/             # 13 plantillas institucionales A4 Apaisado a 300 DPI
├── scripts/
│   └── generate_templates.py  # Generador vectorial/ráster de las 13 plantillas e ícono .ico
├── src/
│   ├── config.py              # Gestión de rutas multiplataforma y soporte sys._MEIPASS (PyInstaller)
│   ├── database/              # Conexión SQLite, esquema auto-inicializable y repositorios CRUD
│   ├── services/              # Motor PDF 300 DPI (cert_engine), Excel (openpyxl) y validadores/WhatsApp
│   └── ui/                    # Interfaz gráfica CustomTkinter (AppWindow, 4 vistas y widgets)
└── tests/
    └── test_phase1_phase2.py  # Suite de pruebas automatizadas (unittest)
```

---

## 6. Compilación y Descarga del Instalador Windows (`Setup_MuniCertificados_v1.0.exe`)

El proyecto cuenta con dos vías listas para obtener el instalador ejecutable para Windows 10 / 11 (sin necesidad de instalar Python en las computadoras administrativas):

### Opción 1: Compilación Automática en la Nube (GitHub Actions — Recomendado desde Linux)
1. Subir los cambios al repositorio de GitHub (`git push origin main`).
2. Ingresar a la pestaña **Actions** del repositorio en GitHub y seleccionar el workflow **"Build Windows Installer (MuniCertificados)"** (también puede ejecutarse manualmente con el botón **Run workflow**).
3. Al finalizar (aprox. 2–3 minutos), descargar desde la sección **Artifacts**:
   - **`Instalador-Windows-Setup_MuniCertificados_v1.0`**: contiene el instalador oficial **`Setup_MuniCertificados_v1.0.exe`** en español, que instala el sistema en el equipo, crea los accesos directos con el escudo municipal en el Escritorio y Menú Inicio, y preserva intacta la carpeta `Documentos\Muni_Certificados` al actualizar o desinstalar.
   - **`Portable-Windows-MuniCertificados`**: carpeta portable lista para ejecutar sin instalación.

### Opción 2: Compilación Local en una PC con Windows
1. Instalar Python 3.11+ e [Inno Setup 6](https://jrsoftware.org/isdl.php).
2. Hacer doble clic sobre **`build_installer.bat`**.
3. El script creará el entorno virtual, ejecutará `PyInstaller` (`MuniCertificados.spec`) e `ISCC.exe` (`installer.iss`), generando:
   - Ejecutable portable en: `dist\MuniCertificados\MuniCertificados.exe`
   - Instalador oficial en: `dist_installer\Setup_MuniCertificados_v1.0.exe`
