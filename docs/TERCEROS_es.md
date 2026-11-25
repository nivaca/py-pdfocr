Software libre que usa py-pdfocr
================================

*(English: [THIRD-PARTY.md](THIRD-PARTY.md))*

py-pdfocr es software libre, con la Licencia Pública General de GNU,
versión 3 o posterior (GPL-3.0-or-later). Está construido sobre el software
libre de esta lista: la biblioteca que importa, el programa que ejecuta y
sus modelos, y las herramientas que lo hacen, lo prueban y lo empaquetan.
Las versiones son las de py-pdfocr 1.0.5 (tal como las resuelve `uv.lock`);
`uv tree` muestra las de una versión posterior. Las licencias van con sus
identificadores SPDX, tal como las declara cada proyecto.

Todas estas licencias permiten usarlos en un programa bajo la GPL 3.
PyMuPDF está bajo la GPL Affero de GNU 3, que la sección 13 de la GPL 3
permite combinar con ella; tesseract, con la Licencia Apache 2.0, no se
combina con py-pdfocr en absoluto: se ejecuta como un programa aparte.


La biblioteca que py-pdfocr necesita
------------------------------------

| Software | Versión | Licencia | Qué hace py-pdfocr con él |
|---|---|---|---|
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) (con MuPDF) | 2.1 | AGPL-3.0 (o una licencia comercial de Artifex) | Lee los PDF, dibuja sus páginas para tesseract, escribe el texto invisible, hace PDF de imágenes |

Lo demás es la biblioteca estándar de Python.

Lo que PyMuPDF 2.1 trae consigo cuando se instala desde PyPI (con `pip
install py-pdfocr` o con `uv`). py-pdfocr no usa nada de esto, y los
instaladores y la AppImage lo dejan fuera (`--no-deps`):

| Software | Versión | Licencia |
|---|---|---|
| pymupdf-layout, pymupdf4llm | 2.1 | (paquetes vacíos, que PyMuPDF 2 conserva para actualizarse; su código está ahora en PyMuPDF, bajo su licencia) |
| [NumPy](https://numpy.org) | 2.5 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| [ONNX Runtime](https://onnxruntime.ai) | 1.32 | MIT |
| [FlatBuffers](https://google.github.io/flatbuffers/) | 25.12 | Apache-2.0 |
| [Protocol Buffers](https://protobuf.dev) | 7.36 | BSD-3-Clause |
| [packaging](https://github.com/pypa/packaging) | 26.3 | Apache-2.0 OR BSD-2-Clause |
| [NetworkX](https://networkx.org/) | 3.7 | BSD-3-Clause |
| [psutil](https://github.com/giampaolo/psutil) | 7.2 | BSD-3-Clause |
| [PyYAML](https://pyyaml.org/) | 6.0 | MIT |
| [tabulate](https://github.com/astanin/python-tabulate) | 0.10 | MIT |


Programas que ejecuta, y sus datos
----------------------------------

Se instalan aparte (los instaladores comprueban si tesseract está y dicen
cómo instalarlo); py-pdfocr ejecuta tesseract como un programa propio.

| Software | Licencia | Para |
|---|---|---|
| [Python](https://www.python.org) | PSF-2.0 | Todo, 3.14 o posterior (la AppImage lleva el suyo) |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) | Apache-2.0 | Leer el texto de las páginas |
| Los modelos de los idiomas que vienen con tesseract ([tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) o [tessdata](https://github.com/tesseract-ocr/tessdata), según los empaquete cada sistema) | Apache-2.0 | Los idiomas, y `osd`, que averigua cómo está puesta una página (`--rotate`) |
| [tessdata_best](https://github.com/tesseract-ocr/tessdata_best) | Apache-2.0 | Los modelos más precisos, descargados con `py-pdfocr download` si se quiere |
| La versión de tesseract para Windows de la [Biblioteca de la Universidad de Mannheim](https://github.com/UB-Mannheim/tesseract) | Apache-2.0 | Tesseract en Windows (`winget install UB-Mannheim.TesseractOCR`), como sugiere el instalador |
| [Homebrew](https://brew.sh) | BSD-2-Clause | Tesseract y Python en macOS (`brew install tesseract tesseract-lang`), como sugiere el instalador |


El programa del autor al que pasó
---------------------------------

El código de py-pdfocr se adaptó luego e incluyó en
[py-pdftools](https://github.com/nivaca/py-pdftools), de Nicolas Vaughan,
también con GPL-3.0-or-later. py-pdfocr usa además los modelos más precisos
que py-pdftools haya descargado, si los hay.


Para hacerlo, probarlo y empaquetarlo
-------------------------------------

Sirven para hacer py-pdfocr, no los usa al ejecutarse.

| Software | Licencia | Para |
|---|---|---|
| [uv](https://github.com/astral-sh/uv) (con uv_build) | MIT OR Apache-2.0 | El entorno, la rueda y el paquete fuente |
| [pytest](https://docs.pytest.org) (con iniconfig, pluggy, Pygments, colorama) | MIT (Pygments: BSD-2-Clause; colorama: BSD-3-Clause) | Las pruebas |
| [python-appimage](https://github.com/niess/python-appimage) | GPL-3.0 | El Python de la AppImage |
| [appimagetool](https://github.com/AppImage/appimagetool), [type2-runtime](https://github.com/AppImage/type2-runtime) | MIT | Hacer la AppImage |
| [GitHub Actions](https://github.com/actions) (checkout, setup-python) | MIT | Probar los instaladores en Linux, macOS y Windows |
| [Chocolatey](https://chocolatey.org) | Apache-2.0 | Tesseract en las máquinas Windows de esas pruebas |
