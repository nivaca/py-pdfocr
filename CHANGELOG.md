# Changelog

All notable changes to py-pdfocr. The releases, with their wheels, ZIPs
and AppImages, are on
[Codeberg](https://codeberg.org/nivaca/py-pdfocr/releases) and
[GitHub](https://github.com/nivaca/py-pdfocr/releases).

## 1.0.4 — 2026-11-21

- The open-source software py-pdfocr uses, with the licence of each, is
  listed in `docs/THIRD-PARTY.md` (in Spanish, `docs/TERCEROS_es.md`), and
  the READMEs link to it.

## 1.0.3 — 2026-11-21

The first release.

- `py-pdfocr read` (or just `py-pdfocr FILE.pdf`): the text of the scanned
  pages, read by tesseract and written under their pictures, invisible;
  into a copy, the file itself (`-i`) or a folder (`--output-dir`); the
  pages chosen (`--pages`), turned first if they lie sideways (`--rotate`),
  read at a resolution (`--dpi`), several at once (`-j`), and the doubtful
  words listed (`--report`, `--doubtful`). It shows how far it has got on
  the terminal, and asks for the password of a protected PDF when it is
  not given.
- `py-pdfocr images`: a PDF made of pictures, then read.
- `py-pdfocr scanned`: which pages are scans without text.
- `py-pdfocr languages`, `download`, `remove`: tesseract's languages, and
  its more accurate models (tessdata_best) downloaded, updated or removed.
- `py-pdfocr settings`: the languages read by default, and the language of
  the interface (English, Spanish).
- A protected PDF (AES-256) keeps its text and its pictures when it is
  saved again: the key is no longer spoilt by asking whether the file needs
  a password after it has been opened with it.
- Tesseract is found where its installers for Windows and macOS put it,
  also when it is not on the PATH.
- Installers for Linux, macOS and Windows (`install/`), tested on the three
  systems, and an AppImage for Linux; both with PyMuPDF alone, without the
  libraries it brings for its analysis of layouts, which py-pdfocr does not
  use.
