# Skill: CustomTkinter Desktop UI & UX Institucional

## Propósito
Garantizar que la interfaz gráfica de escritorio construida con `CustomTkinter` tenga una estética profesional, moderna, responsiva y libre de congelamientos en sistemas operativos Windows 10/11 y Linux.

## 1. Sistema de Diseño e Identidad Visual
- **Paleta Institucional (Dark Mode por defecto):**
  - Fondo principal de ventana: `#0B1120` (Azul noche profundo)
  - Paneles, tarjetas y sidebar: `#111827` y `#1E293B` (Gris pizarra oscuro)
  - Bordes sutiles de tarjetas: `#334155` (`border_width=1`)
  - Acento primario (Acciones principales): `#2563EB` (Azul institucional vibrante, hover `#1D4ED8`)
  - Acento secundario / Institucional destacado: `#D4AF37` (Dorado sutil para títulos o badges de certificación)
  - Estados semánticos: Éxito/Presente `#10B981`, Advertencia `#F59E0B`, Peligro/Eliminar `#EF4444`
  - Texto primario: `#F8FAFC` | Texto secundario/etiquetas: `#94A3B8`
- **Geometría y Espaciado:**
  - Usar `corner_radius=8` en contenedores/tarjetas y `corner_radius=6` en botones y campos de entrada (`CTkEntry`).
  - Mantener consistencia estricta en márgenes (`padx=12`, `pady=8`) y alturas de inputs (`height=36`).

## 2. Responsividad y Pantallas Compactas
- Toda vista con formularios extensos (especialmente el Estudio de Diseño de Diplomas) o listados largos debe usar `CTkScrollableFrame` para garantizar accesibilidad completa en resoluciones de laptop (`1366x768`) sin ocultar botones inferiores.
- Usar `grid_columnconfigure` y `grid_rowconfigure` con `weight=1` apropiado para que la vista previa del certificado y las tablas se expandan fluidamente al maximizar la ventana.

## 3. Concurrencia y Rendimiento (Cero "No Responde")
- **Prohibido bloquear el hilo principal de Tkinter (`mainloop`):**
  - La generación masiva de PDFs, la importación de archivos Excel grandes y el renderizado de vistas previas pesadas deben ejecutarse en hilos secundarios (`threading.Thread(..., daemon=True)`).
  - Toda actualización visual desde un hilo secundario (barras de progreso `CTkProgressBar`, etiquetas de estado, recarga de listas o actualización del `CTkLabel` de vista previa) debe encolarse obligatoriamente mediante `self.after(0, callback)`.
- **Debouncing en Vista Previa:** Al mover sliders o escribir en campos de texto dentro del diseñador, aplicar un retardo breve (`self.after(180, ...)`) cancelando el timer anterior para evitar renderizados redundantes por cada tecla pulsada.

## 4. Ergonomía Operativa
- Implementar navegación por teclado (`<Return>`) en el formulario de carga rápida de asistentes para permitir carga continua sin tocar el mouse.
- Mostrar siempre retroalimentación visual clara (toasts/banners de estado o diálogos modales limpios) tras guardar, importar o emitir certificados.
