# Skill: Composición Editorial, Tipografía y Calidad de Imprenta

## Propósito
Asegurar que cada certificado y reconocimiento generado por `cert_engine.py` posea equilibrio visual, jerarquía tipográfica editorial y márgenes seguros para impresión en hoja A4 apaisada (300 DPI: `3508 x 2480 px`).

## 1. Gestión y Variedad de Tipografías (`assets/fonts/`)
- El sistema debe contar con un catálogo amplio de tipografías embebidas en formato `.ttf` clasificadas mentalmente en 3 estilos institucionales:
  1. **Clásicas / Solemnes (Serif):** ej. `Cinzel`, `PlayfairDisplay`, `Lora`, `Merriweather`, `NotoSerif`.
  2. **Modernas / Técnicas (Sans-Serif):** ej. `Montserrat`, `Poppins`, `Raleway`, `Roboto`, `NotoSans`.
  3. **Caligráficas / Destacados y Firmas (Script/Display):** ej. `GreatVibes`, `AlexBrush`, `CormorantGaramond` (ideales para nombres destacados o títulos honoríficos).
- El selector de fuentes en la interfaz debe listar dinámicamente todos los archivos `.ttf` disponibles en `assets/fonts/` con nombres limpios y legibles (sin rutas ni extensiones `.ttf`).

## 2. Jerarquía Visual y Reglas de Composición
- **Márgenes de Seguridad de Impresión:** Ningún bloque de texto ni logo puede ubicarse a menos de `210 px` (~18 mm) de los bordes exteriores del lienzo A4 (`3508 x 2480 px`) para evitar cortes en impresoras de oficina.
- **Centrado Matemático Real:** Al activar alineación centrada, calcular el ancho exacto del texto con `ImageDraw.textbbox()` o `font.getlength()` y posicionar en `x = (canvas_width - text_width) / 2`.
- **Ajuste Dinámico y Salto de Línea Inteligente (Word-Wrapping):**
  - **Nombre del Homenajeado:** Si el nombre completo excede el ancho máximo seguro (`2600 px`), reducir progresivamente el tamaño de fuente en pasos de `2 pt` hasta que entre en una sola línea limpia sin desbordar los marcos.
  - **Cuerpo del Certificado:** Dividir automáticamente el texto por palabras respetando un ancho máximo configurable (por defecto `2500 px`), dibujando cada línea centrada con un interlineado (`line_spacing`) equivalente a `1.35x` el tamaño de fuente.
- **Bloque de Firmas Institucionales:**
  - Soportar 1, 2 o 3 firmas distribuidas simétricamente en el tercio inferior (`y ≈ 1950 - 2150 px`).
  - Dibujar una línea horizontal sobria (`width=480 px`, `2-3 px` de grosor) encima del Nombre de la Autoridad y su Cargo en fuente ligeramente menor debajo. Si existe imagen de firma (`PNG` o fondo blanco removido), centrarla inmediatamente sobre la línea.
