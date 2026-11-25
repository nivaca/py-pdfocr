Open-source software used by py-pdfocr
======================================

*(Español: [TERCEROS_es.md](TERCEROS_es.md))*

py-pdfocr is free software, under the GNU General Public License, version 3
or later (GPL-3.0-or-later). It is built on the open-source software listed
here: the library it imports, the program it runs and its models, and the
tools that build, test and package it. The versions are those of py-pdfocr
1.0.5 (as `uv.lock` resolves them); `uv tree` shows those of any later
version. Licences are given as SPDX identifiers, as each project declares
them.

All of these licences allow their use in a program under the GPL 3. PyMuPDF
is under the GNU Affero GPL 3, which section 13 of the GPL 3 allows to be
combined with it; tesseract, under the Apache License 2.0, is not combined
with py-pdfocr at all, but runs as a program of its own.


The library py-pdfocr needs
---------------------------

| Software | Version | Licence | What py-pdfocr does with it |
|---|---|---|---|
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) (with MuPDF) | 2.1 | AGPL-3.0 (or a commercial licence from Artifex) | Reads the PDFs, draws their pages for tesseract, writes the invisible text, makes PDFs of images |

The rest is Python's own standard library.

What PyMuPDF 2.1 brings with it when installed from PyPI (with `pip
install py-pdfocr` or `uv`). py-pdfocr uses none of it, and the installers
and the AppImage leave it out (`--no-deps`):

| Software | Version | Licence |
|---|---|---|
| pymupdf-layout, pymupdf4llm | 2.1 | (empty packages, kept by PyMuPDF 2 for upgrading; their code is now in PyMuPDF, under its licence) |
| [NumPy](https://numpy.org) | 2.5 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| [ONNX Runtime](https://onnxruntime.ai) | 1.32 | MIT |
| [FlatBuffers](https://google.github.io/flatbuffers/) | 25.12 | Apache-2.0 |
| [Protocol Buffers](https://protobuf.dev) | 7.36 | BSD-3-Clause |
| [packaging](https://github.com/pypa/packaging) | 26.3 | Apache-2.0 OR BSD-2-Clause |
| [NetworkX](https://networkx.org/) | 3.7 | BSD-3-Clause |
| [psutil](https://github.com/giampaolo/psutil) | 7.2 | BSD-3-Clause |
| [PyYAML](https://pyyaml.org/) | 6.0 | MIT |
| [tabulate](https://github.com/astanin/python-tabulate) | 0.10 | MIT |


Programs it runs, and their data
--------------------------------

These are installed apart (the installers check for tesseract and say how
to install it); py-pdfocr runs tesseract as a program of its own.

| Software | Licence | For |
|---|---|---|
| [Python](https://www.python.org) | PSF-2.0 | Everything, 3.14 or later (the AppImage brings its own) |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) | Apache-2.0 | Reading the text of the pages |
| The models of the languages that come with tesseract ([tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) or [tessdata](https://github.com/tesseract-ocr/tessdata), as each system packages them) | Apache-2.0 | The languages, and `osd`, which finds how a page lies (`--rotate`) |
| [tessdata_best](https://github.com/tesseract-ocr/tessdata_best) | Apache-2.0 | The more accurate models, downloaded with `py-pdfocr download` when wished |
| The Windows build of tesseract of the [Mannheim University Library](https://github.com/UB-Mannheim/tesseract) | Apache-2.0 | Tesseract on Windows (`winget install UB-Mannheim.TesseractOCR`), as the installer suggests |
| [Homebrew](https://brew.sh) | BSD-2-Clause | Tesseract and Python on macOS (`brew install tesseract tesseract-lang`), as the installer suggests |


The author's program it went into
---------------------------------

The code of py-pdfocr was later adapted and included in
[py-pdftools](https://github.com/nivaca/py-pdftools), by Nicolas Vaughan,
also under GPL-3.0-or-later. py-pdfocr also uses the more accurate models
that py-pdftools has downloaded, if there are any.


Building, testing and packaging
-------------------------------

Used to make py-pdfocr, not by it when it runs.

| Software | Licence | For |
|---|---|---|
| [uv](https://github.com/astral-sh/uv) (with uv_build) | MIT OR Apache-2.0 | The environment, the wheel and the source package |
| [pytest](https://docs.pytest.org) (with iniconfig, pluggy, Pygments, colorama) | MIT (Pygments: BSD-2-Clause; colorama: BSD-3-Clause) | The tests |
| [python-appimage](https://github.com/niess/python-appimage) | GPL-3.0 | The Python inside the AppImage |
| [appimagetool](https://github.com/AppImage/appimagetool), [type2-runtime](https://github.com/AppImage/type2-runtime) | MIT | Making the AppImage |
| [GitHub Actions](https://github.com/actions) (checkout, setup-python) | MIT | Testing the installers on Linux, macOS and Windows |
| [Chocolatey](https://chocolatey.org) | Apache-2.0 | Tesseract on the Windows machines of those tests |
