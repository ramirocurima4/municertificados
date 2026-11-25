# Skill: Empaquetado Seguro y Portabilidad Multiplataforma (PyInstaller)

## Propósito
Garantizar que la aplicación funcione idénticamente ejecutada desde el código fuente en Linux/Windows y compilada como ejecutable independiente (`.exe`) con `PyInstaller` en las computadoras del Área de Redes.

## 1. Separación Estricta entre Assets y Datos de Usuario
- **Recursos Empaquetados (Solo Lectura):** Todo archivo dentro de `assets/` (plantillas base, tipografías `.ttf`, íconos) debe resolverse exclusivamente mediante `get_resource_path(relative_path)` en `src/config.py`, que verifica `hasattr(sys, '_MEIPASS')`.
- **Archivos Mutables y Generados (Lectura/Escritura):** Nunca escribir bases de datos, logs, plantillas importadas por el usuario ni PDFs dentro del directorio del ejecutable. Usar siempre la ruta en `Documents/Muni_Certificados/` resuelta por `src/config.py`.

## 2. Manejo de Imágenes en Tkinter / CustomTkinter
- Al mostrar vistas previas o íconos en la UI usando `CTkImage`, almacenar siempre una referencia persistente en el atributo de la instancia (`self.preview_ctk_image = ...`) para evitar que el recolector de basura de Python libere la imagen y deje el lienzo en blanco.
- Liberar o reutilizar objetos `PIL.Image` grandes durante el renderizado en tiempo real para mantener el consumo de RAM por debajo de `250 MB` en equipos de oficina con 4 GB de RAM.

## 3. Dependencias Limpias y Hooks de Compilación
- Mantener `requirements.txt` libre de librerías pesadas innecesarias (`pandas`, `scipy`, `matplotlib`).
- Al invocar `PyInstaller`, asegurar la inclusión explícita de carpetas de datos (`--add-data "assets:assets"` en Linux o `--add-data "assets;assets"` en Windows) y los metadatos de `customtkinter`.
