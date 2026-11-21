py-pdfocr
=========

*(Español: [README_es.md](README_es.md))*

py-pdfocr reads the text of scanned PDF pages with
[tesseract](https://github.com/tesseract-ocr/tesseract) and writes it into
the PDF, invisible, under the pictures of the pages, so that it can be
found, copied and marked. It works from the command line: it reads the
pages of PDFs, makes a PDF of pictures and reads it, says which pages are
scans, and manages tesseract's languages, with the download of its more
accurate models.

Its code was later adapted and included in
[py-pdftools](https://github.com/nivaca/py-pdftools), my editor of PDF
documents, where it has a window of its own (see "py-pdfocr and
py-pdftools").

The command line is in English and in Spanish. It runs on Linux, macOS and
Windows. This is version 1.0.4.

I am Nicolas Vaughan (<nicolasvaughan@proton.me>), and I wrote it in 2026.
It is free software, under the GNU General Public License, version 3 or
later (see "Licensing").

Installing
----------

py-pdfocr needs the tesseract program, with the languages of the
documents:

* Fedora: `sudo dnf install tesseract tesseract-langpack-spa …`
* Debian and Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-spa …`
* macOS: `brew install tesseract tesseract-lang`
* Windows: `winget install UB-Mannheim.TesseractOCR` (its installer asks
  for the languages; py-pdfocr finds it in `Program Files` even when it is
  not on the PATH)

**The AppImage** (Linux) has everything else in it, Python included. Download
`py-pdfocr-1.0.4-x86_64.AppImage` from the
[releases](https://github.com/nivaca/py-pdfocr/releases), make it
executable, and run it as the command:

    $ chmod +x py-pdfocr-1.0.4-x86_64.AppImage
    $ ./py-pdfocr-1.0.4-x86_64.AppImage scan.pdf

**The installers** need Python 3.14 or later. From the source (cloned, or
the ZIP of a release unpacked):

    $ install/install.sh                Linux and macOS: install, or update
    $ install/install.sh --uninstall
    > install\install.bat               Windows: install, or update
    > install\install.bat -Uninstall

Each makes a Python environment of its own for py-pdfocr and installs it
there with PyMuPDF (downloaded from PyPI, so it needs the internet the
first time). On Linux and macOS the command `py-pdfocr` is linked in
`~/bin` or `~/.local/bin`; on Windows it goes into
`%LOCALAPPDATA%\py-pdfocr\bin`, which is added to the user's PATH. Nothing
needs administrator rights, and uninstalling keeps the settings and the
models downloaded. The installers are tested on the three systems at each
change (`.github/workflows/installers.yml`).

**With [uv](https://docs.astral.sh/uv/)**, from the source:

    $ git clone https://github.com/nivaca/py-pdfocr.git
    $ cd py-pdfocr
    $ uv run py-pdfocr --help
    $ uv tool install .                 or as a command of its own

Reading scanned pages
---------------------

    $ py-pdfocr scan.pdf                     writes scan-ocr.pdf beside it
    $ py-pdfocr scan.pdf -l lat+spa          in Latin and Spanish, Latin first
    $ py-pdfocr scan.pdf -i                  over the file itself
    $ py-pdfocr *.pdf --output-dir read/     several, into a folder
    $ py-pdfocr scan.pdf --pages 3-10,LAST -o out.pdf

`read` is the command when none is given (`py-pdfocr read scan.pdf` is the
same). Only the pages that are scans are read: a page that has pictures and
no text. A page that has text already is left as it is, so that its text is
not there twice, and a file can be read again without harm.

The words are written where the picture shows them, as wide as they are
there, in invisible text (render mode 3). Several pages are read at once,
each in a process of its own (`-j` says how many; by default, half the
processors). Each page is drawn at 300 dpi (`--dpi`) for tesseract.

`--rotate` turns first the pages scanned sideways or upside down, and the
pages of the PDF are turned with them. It needs tesseract's model `osd`,
which finds how a page lies: `py-pdfocr download osd`.

Tesseract says how sure it is of each word, from 0 to 100. The words below
60 (`--doubtful`) are doubtful; `--report` lists them, one to a line, as
page, confidence and word, separated by tabs (with several PDFs, the file
first), so that they can be checked in the PDF afterwards.

A PDF with a password is opened with `--password`, or else the password is
asked for on the terminal. The copy keeps the protection of the original.

A PDF made of pictures
----------------------

    $ py-pdfocr images p1.jpg p2.jpg p3.tif -o book.pdf -l spa
    $ py-pdfocr images *.png -o book.pdf --paper A4 --margin 10 --no-ocr

Each picture is a page (each frame, in a TIFF of several); the page is as
big as the picture, or of the paper of `--paper` (A3, A4, A5, Letter,
Legal), standing or lying as the picture is (or `--portrait`,
`--landscape`). Then its text is read, as above, unless `--no-ocr`.

Which pages are scans
---------------------

    $ py-pdfocr scanned *.pdf
    scan.pdf: 12 pages are scans without text (of 14): 1-10, 13-14

Languages
---------

    $ py-pdfocr languages              those tesseract can read here
    $ py-pdfocr languages --all welsh  also those that can be downloaded
    $ py-pdfocr download lat osd       their more accurate models
    $ py-pdfocr remove lat             the one installed is used again

The languages installed with tesseract come from the packages of the
system. Tesseract also has more accurate models of each language
([tessdata_best](https://github.com/tesseract-ocr/tessdata_best)), slower
but better on difficult pages: `download` puts them in py-pdfocr's own
folder (`~/.local/share/py-pdfocr/tessdata`; `%LOCALAPPDATA%` on Windows),
and they are used instead of the installed ones, marked with ★ in the list.
Downloading again updates them. This is the only thing py-pdfocr does on
the internet, and the request carries nothing about the user.

Settings
--------

    $ py-pdfocr settings --languages lat+spa    read in these by default
    $ py-pdfocr settings --interface es         the command line in Spanish
    $ py-pdfocr --interface en languages        in English, this time only

They are kept in `~/.config/py-pdfocr/config.toml` (on macOS, in
`~/Library/Application Support/py-pdfocr`; on Windows, in
`%APPDATA%\py-pdfocr`; `PY_PDFOCR_CONFIG` names another folder).

py-pdfocr and py-pdftools
-------------------------

py-pdfocr came first. Its code (the reading of the pages, the languages
and the models, the PDF made of pictures) was later adapted and included in
py-pdftools, which edits PDF documents in a window. There it has a mode of
its own, and something py-pdfocr leaves out on purpose: the doubtful words
are shown beside their pictures, to be corrected before the text is
written. Here they are only listed (`--report`).

py-pdftools keeps the models it downloads in its own folder
(`~/.local/share/py-pdftools/tessdata`). py-pdfocr uses them too, so that
the same model is not downloaded twice; `languages` shows where each one
is, and only py-pdftools removes its own.

Testing
-------

There are 27 tests (`uv run pytest`): the reading of pages, with the place
and confidence of the words; the doubtful words; pages turned; the
languages and models, and their download; each command of the command
line; PDFs with a password; the Spanish interface, with every text
translated; and the version, the same everywhere. The tests that read need
tesseract with English, and those that turn pages need the model `osd`
(they are skipped without it).

Licensing
---------

py-pdfocr is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version (see [LICENSE](LICENSE)). It uses PyMuPDF (GNU AGPL 3),
and runs tesseract (Apache License 2.0), whose models are under the same
license. The AppImage includes a Python of the python-appimage project
(Python Software Foundation License). The open-source software py-pdfocr
uses, and the licences of each, are listed in
[docs/THIRD-PARTY.md](docs/THIRD-PARTY.md).
