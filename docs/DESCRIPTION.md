How py-pdfocr was made
======================

py-pdfocr reads the text of scanned PDF pages with the tesseract program
and writes it into the PDF, invisible, under the pictures of the pages, so
that it can be found, copied and marked. Nicolas Vaughan made it in
November 2026, as a program for the command line, for the scans of books
and manuscripts that a PDF viewer shows but cannot search. Its code was
later adapted and included in py-pdftools, his editor of PDF documents.
Here I explain how it was made, in six stages.

It is free software, under the GNU General Public License, version 3 or
later. The PDFs are read, drawn and written by PyMuPDF (GNU AGPL 3); the
text is read by tesseract (Apache License 2.0), which runs as a program of
its own, and whose models of the languages are under the same license.

Nicolas Vaughan is Associate Professor of Literature at the School of Arts
and Humanities of the Universidad de los Andes, Bogotá, Colombia.

1. A first version
------------------

Tesseract reads pictures, not PDFs, and gives back text, not a PDF. What
was needed was everything around it. Each page is drawn in grey at 300
dpi and given to tesseract through its standard input; tesseract answers
with a table (`tessedit_create_tsv`) of the words, each with its rectangle
on the picture and its confidence, from 0 to 100. The rectangle is turned
into points on the page, and the word is written there in invisible text
(render mode 3), with the height of the box and stretched to its width, so
that a search finds it under the letters the eye sees. A word read with a
confidence below 60 is doubtful, and keeps a small picture of itself.

Only the pages that are scans are read: a page with pictures and no text.
A page with text would end with its text twice, and with this rule a file
can be read again without harm. The pages are read several at once, each
in a process of its own, since tesseract on one page takes a few seconds
and the processors of a computer are many.

A page scanned sideways can be turned first: tesseract's model `osd` finds
how it lies, and both the picture read and the page of the PDF are turned.
For each run, a temporary folder of links gives tesseract the models of the
languages asked for, so that a better model, downloaded, can stand in for
the one installed with tesseract without touching the system.

The rest is the frame of my other programs: the lists of pages
(`1-5, 9, LAST-2..LAST`), the interface in English and Spanish, each text
found by its English in an XML file, and a configuration file.

2. The commands
---------------

`read` reads the scanned pages of PDFs and writes each as `NAME-ocr.pdf`
beside it, over itself (`-i`) or into a folder (`--output-dir`). It is
also the command when none is given, so that `py-pdfocr scan.pdf` reads a
PDF. `images` makes a PDF of pictures, a page for each, as big as the
picture or on paper of a size, and then reads it. `scanned` says which
pages are scans. `languages` prints a table of the languages, with
whether each came with tesseract and the size and date of its better
model; with `--all` it shows also those that can be downloaded, and a text
filters it. `download` fetches the more accurate models of tesseract
(tessdata_best) into py-pdfocr's own folder, and to download again is to
update; `remove` takes them out. `settings` keeps the languages read by
default and the language of the interface.

The doubtful words are listed with `--report`, one to a line, with their
page and confidence, to be checked in the PDF. They are not corrected
before they are written: that would be editing the text, which needs a
window, and py-pdfocr has none.

3. On the terminal
------------------

The program shows how far it has got with a line on standard error,
written over as each page is read. It is written only on a terminal and
not with `-q`, so that a script finds in the output only the result and the
report. Ctrl+C stops the reading: the pages not started are cancelled,
nothing is written, and the program ends with 130.

The processes that read are started with `spawn`, which works the same on
the three systems. A spawned process starts with the interface in English,
so a message of tesseract's failure came in English in the middle of a
Spanish interface; each process now receives the language when it starts.
Two options came from use: `--dpi`, for letters very small or very large,
and `-j`, how many pages are read at once. A PDF with a password, when none
is given, asks for it on the terminal, and the password serves for the
files that follow.

4. A key spoilt
---------------

The test of a PDF protected with AES-256 failed: the copy was written, it
opened with its password, and it had no text. MuPDF printed "aes padding
out of range" while saving. The words were on the page until the moment it
was saved, so I followed it with small trials until one line remained: the
question of whether the document needed a password, which the function of
saving asked in order to keep the protection. It asked `needs_pass`. Asked
after the password has been given, MuPDF tries the empty password again,
and on an AES-256 file this leaves a wrong key. Everything written after
that, the new text and the pictures written again, is encrypted with that
key, and nobody can read it. The metadata of the document say the same
thing (their entry `encryption`) without touching the key, also for a file
with only a password of permissions, so the function now asks them.

5. Installers and an AppImage
-----------------------------

There are installers for Linux and macOS (`install/install.sh`) and for
Windows (`install/install.bat`, which runs `install.ps1`). Each finds a
Python 3.14, makes an environment of its own and installs py-pdfocr in it.
On Linux and macOS the command is linked in `~/bin` or `~/.local/bin`. On
Windows it is a small `py-pdfocr.cmd` in a folder of its own, which is put
on the user's PATH; the folder `Scripts` of the environment would have put
its `python.exe` and `pip` there too. Uninstalling keeps the settings and
the models downloaded, which may live in the same folder as the
environment.

The installers of tesseract for Windows and macOS do not always put it on
the PATH, so the program looks for it also where they leave it
(`Program Files\Tesseract-OCR`, `/opt/homebrew/bin`).

The first AppImage weighed 135 MB. PyMuPDF 2.1 brings with it onnxruntime,
numpy, networkx and others, for its analysis of the layout of pages, which
py-pdfocr never uses. PyMuPDF works without them, and the tests pass without
them, so the AppImage and the installers install it alone (`--no-deps`):
the AppImage weighs 85 MB, and it holds its own Python (of the
python-appimage project), so that on Linux only tesseract is needed. A
workflow of GitHub runs the installers on Linux, macOS and Windows, with
tesseract installed as a user would, runs the tests against the program
installed, and uninstalls it.

6. Into py-pdftools
-------------------

py-pdftools, which edits PDF documents in a window, took this code later:
the reading of pages, the languages and their models, and the PDF made of
pictures. It was adapted there to a mode of the window, with a panel to
choose the pages and the languages, and with what py-pdfocr leaves out, the
doubtful words shown beside their pictures, to be corrected before the
text is written. py-pdftools keeps the models it downloads in its own
folder; py-pdfocr uses those too, so that a model is not downloaded twice,
but only py-pdftools removes its own.

Testing
-------

There are 27 tests, run with pytest. Eleven are of the engine: the words of
a page read in other processes, with their place and confidence, and
written where the picture shows them; the doubtful words, with their
pictures; the reading stopped; the error of tesseract in the language of
the interface; pages lying at 90, 180 and 270 degrees turned; the
languages, installed and downloaded, here and by py-pdftools; and the
download, with its failures, without the network. Thirteen are of the
command line: each command, the outputs, the report with one PDF and with
several, the protected PDF and its key, and the errors. Two are of the
interface: every text of the code is in the Spanish file, and none is
there that the code does not use. One checks that the version is the same
everywhere it is written. The tests run in folders of their own and never
touch the user's settings or models. Those that read need tesseract with
English; those that turn pages need the model `osd`, and use the user's if
there is one.

The program was also run by hand on scans made for the purpose, in both
languages, with `osd` downloaded from tesseract's repository and removed
again, and with Ctrl+C sent to the whole group of processes in the middle
of a reading. The installer for Linux was run in a home folder made for the
test, and the AppImage with an empty environment. It has 17 files of
Python, around 2,500 lines, and 281 texts of the interface in Spanish, 31
of them argparse's own.
