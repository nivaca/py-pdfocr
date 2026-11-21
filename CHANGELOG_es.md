# Cambios

Los cambios de py-pdfocr que importan. Las versiones, con sus wheels, ZIP y
AppImages, están en
[Codeberg](https://codeberg.org/nivaca/py-pdfocr/releases) y
[GitHub](https://github.com/nivaca/py-pdfocr/releases).

## 1.0.3 — 2026-11-21

La primera versión publicada.

- `py-pdfocr read` (o solo `py-pdfocr ARCHIVO.pdf`): el texto de las páginas
  escaneadas, leído por tesseract y escrito bajo sus imágenes, invisible; en
  una copia, en el mismo archivo (`-i`) o en una carpeta (`--output-dir`);
  las páginas elegidas (`--pages`), giradas antes si están de lado
  (`--rotate`), leídas a una resolución (`--dpi`), varias a la vez (`-j`), y
  las palabras dudosas listadas (`--report`, `--doubtful`). Muestra en la
  terminal cuánto ha leído y pide la contraseña de un PDF protegido si no
  se da.
- `py-pdfocr images`: un PDF hecho de imágenes, y luego leído.
- `py-pdfocr scanned`: qué páginas son escaneos sin texto.
- `py-pdfocr languages`, `download`, `remove`: los idiomas de tesseract y
  sus modelos más precisos (tessdata_best), descargados, actualizados o
  quitados.
- `py-pdfocr settings`: los idiomas que se leen por omisión y el idioma de
  la interfaz (inglés, español).
- Un PDF protegido (AES-256) conserva su texto y sus imágenes al guardarse
  de nuevo: la clave ya no se estropea al preguntar, después de abrirlo con
  ella, si el archivo necesita contraseña.
- Tesseract se encuentra donde lo ponen sus instaladores para Windows y
  macOS, aunque no esté en el PATH.
- Instaladores para Linux, macOS y Windows (`install/`), probados en los
  tres sistemas, y una AppImage para Linux; ambos con PyMuPDF solo, sin las
  bibliotecas que trae para analizar la disposición de las páginas, que
  py-pdfocr no usa.
