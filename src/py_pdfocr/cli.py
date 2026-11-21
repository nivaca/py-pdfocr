"""The command line of py-pdfocr.

    py-pdfocr read PDF...          the text of the scanned pages, read and written under them
    py-pdfocr PDF...               (the same: read is the command when none is given)
    py-pdfocr images PICTURE...    a PDF made of pictures, and its text read
    py-pdfocr scanned PDF...       which pages are scans without text
    py-pdfocr languages            tesseract's languages here (and, with --all, those it can download)
    py-pdfocr download NAME...     the more accurate models of languages, downloaded or updated
    py-pdfocr remove NAME...       a model downloaded, removed
    py-pdfocr settings             the languages read by default, and those of the interface

The doubtful words can be listed (--report), but not corrected before they
are written.
"""

from __future__ import annotations

import argparse
import datetime
import getpass
import sys
from pathlib import Path

from . import config, document, interface, ocr, pagesel
from .interface import ntr, tr

PROG = "py-pdfocr"
COMMANDS = ("read", "images", "scanned", "languages", "download", "remove", "settings")


class CliError(Exception):
    """A command that cannot be done (its message is shown, and the program ends with 1)."""


# ----------------------------------------------------------------- progress, on the terminal

class Progress:
    """A line on standard error, written over as the work goes on (only on a terminal, and unless QUIET)."""

    def __init__(self, quiet: bool = False):
        self.on = not quiet and sys.stderr.isatty()
        self.shown = False

    def say(self, text: str) -> bool:
        if self.on:
            sys.stderr.write("\r\033[K" + text)
            sys.stderr.flush()
            self.shown = True
        return True  # (go on: ocr.run and ocr.download stop when told False)

    def pages(self, done: int, of: int) -> bool:
        return self.say(tr("Reading the scanned pages: {done} of {of}…", done=done, of=of))

    def end(self):
        if self.shown:
            sys.stderr.write("\r\033[K")
            sys.stderr.flush()
            self.shown = False


# ----------------------------------------------------------------- the parser

def _ocr_options(p: argparse.ArgumentParser) -> None:
    """The options of reading, the same in read and images."""
    p.add_argument("-l", "--lang", metavar=tr("LANGUAGES"),
                   help=tr("the languages of the text, as tesseract names them, several with +, the main one "
                           "first: lat+spa (by default, those of the settings: {languages})",
                           languages=_default_languages()))
    p.add_argument("--rotate", action="store_true",
                   help=tr("turn the pages lying sideways or upside down before reading them (needs "
                           "tesseract's osd model: py-pdfocr download osd)"))
    p.add_argument("--report", action="store_true",
                   help=tr("list the doubtful words (page, confidence, word), to be checked"))
    p.add_argument("--doubtful", type=float, default=ocr.DOUBTFUL, metavar=tr("CONFIDENCE"),
                   help=tr("words read with a confidence below this (0 to 100) are doubtful (default: %(default)s)"))
    p.add_argument("--dpi", type=int, default=ocr.DPI, metavar="DPI",
                   help=tr("the resolution at which the pages are read, 72 to 1200 (default: %(default)s)"))
    p.add_argument("-j", "--jobs", type=int, metavar="N",
                   help=tr("how many pages are read at once (by default, half the processors)"))
    p.add_argument("-q", "--quiet", action="store_true", help=tr("do not show how far the reading has got"))


def build_parser() -> argparse.ArgumentParser:
    from . import __version__

    parser = argparse.ArgumentParser(
        prog=PROG,
        description=tr("Read the text of the scanned pages of PDFs with tesseract, and write it under their "
                       "pictures, invisible, so that it can be found, copied and marked. 'py-pdfocr FILE.pdf' "
                       "reads a PDF (the command read)."),
        epilog=tr("Run '%(prog)s COMMAND -h' for help on a command."))
    parser.add_argument("--interface", choices=sorted(interface.names()), default=argparse.SUPPRESS,
                        help=tr("the language of the interface, for this run only (to keep a choice, use "
                                "'settings --interface')"))
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", metavar=tr("COMMAND"))

    p = sub.add_parser(
        "read", help=tr("read the text of the scanned pages of PDFs, and write it under them"),
        description=tr("Read the text of the scanned pages of PDFs with tesseract, and write it under their "
                       "pictures, invisible, so that it can be found, copied and marked. Pages that have text "
                       "already are left as they are. Each PDF is written as NAME-ocr.pdf beside it, unless "
                       "-o, -i or --output-dir say otherwise."))
    p.add_argument("inputs", nargs="+", type=Path, metavar=tr("PDF"), help=tr("the PDFs to read"))
    p.add_argument("--pages", metavar=tr("PAGES"),
                   help=tr("the pages to read: 1-5,9, LAST ... (by default, all the scanned pages)"))
    where = p.add_mutually_exclusive_group()
    where.add_argument("-o", "--output", type=Path, metavar=tr("FILE"), help=tr("the PDF to write (one input only)"))
    where.add_argument("-i", "--in-place", action="store_true", help=tr("write each PDF over itself"))
    where.add_argument("--output-dir", type=Path, metavar=tr("FOLDER"),
                       help=tr("write the PDFs into FOLDER, with the same names"))
    p.add_argument("--password", default=None,
                   help=tr("the password of the PDFs, if they have one (asked for, if not given, on a terminal)"))
    _ocr_options(p)

    p = sub.add_parser(
        "images", help=tr("make a PDF of pictures (photographs, scans), and read its text"),
        description=tr("Make a PDF of pictures (photographs, scans): a page for each, in the order given, as "
                       "big as the picture or on paper of a size; then read its text with tesseract and write "
                       "it under the pictures (unless --no-ocr)."))
    p.add_argument("inputs", nargs="+", type=Path, metavar=tr("PICTURE"), help=tr("a picture (PNG, JPEG, TIFF…)"))
    p.add_argument("-o", "--output", required=True, type=Path, metavar=tr("FILE"), help=tr("the PDF made"))
    from .images import PAPERS

    p.add_argument("--paper", choices=list(PAPERS), help=tr("put each picture on paper of this size"))
    g = p.add_mutually_exclusive_group()
    g.add_argument("--portrait", dest="landscape", action="store_false", default=None,
                   help=tr("the paper standing (else as each picture is)"))
    g.add_argument("--landscape", dest="landscape", action="store_true", help=tr("the paper lying"))
    p.add_argument("--margin", type=float, default=0, metavar="MM", help=tr("a margin, in millimetres"))
    p.add_argument("--no-ocr", action="store_true", help=tr("only make the PDF; do not read its text"))
    _ocr_options(p)

    p = sub.add_parser(
        "scanned", help=tr("show which pages of PDFs are scans without text"),
        description=tr("Show which pages of PDFs are scans without text: those that 'read' reads. A page with "
                       "pictures and no text is a scan."))
    p.add_argument("inputs", nargs="+", type=Path, metavar=tr("PDF"), help=tr("the PDFs to look at"))
    p.add_argument("--password", default=None, help=tr("the password of the PDFs, if they have one"))

    p = sub.add_parser(
        "languages", help=tr("show tesseract's version and its languages here"),
        description=tr("Show tesseract's version and the languages it can read here: those installed with it, "
                       "and the more accurate models downloaded (★). With --all, also those that can be "
                       "downloaded."))
    p.add_argument("filter", nargs="?", metavar=tr("TEXT"), help=tr("only the languages whose code or name has TEXT"))
    p.add_argument("-a", "--all", action="store_true", help=tr("also the languages that can be downloaded"))

    p = sub.add_parser(
        "download", help=tr("download or update tesseract's most accurate models of languages"),
        description=tr("Download tesseract's most accurate models (tessdata_best) of these languages, or "
                       "download them again to update them, into py-pdfocr's own folder; osd is the model that "
                       "finds how pages lie (--rotate). Needs the internet."))
    p.add_argument("names", nargs="+", metavar=tr("NAME"), help=tr("a language, as tesseract names it (lat, spa, osd…)"))

    p = sub.add_parser(
        "remove", help=tr("remove downloaded models of languages"),
        description=tr("Remove the more accurate models of these languages downloaded with py-pdfocr; the one "
                       "installed with tesseract, if any, is used again. The languages installed with "
                       "tesseract are installed and removed with the system's packages (tesseract-langpack-… "
                       "on Fedora, tesseract-ocr-… on Debian and Ubuntu)."))
    p.add_argument("names", nargs="+", metavar=tr("NAME"), help=tr("a language, as tesseract names it (lat, spa, osd…)"))

    p = sub.add_parser(
        "settings", help=tr("show or change the settings"),
        description=tr("Show the settings, or change them: the languages of the text read by default, and "
                       "the language of the interface."))
    p.add_argument("--languages", metavar=tr("LANGUAGES"),
                   help=tr("the languages of the text read by default, several with +: lat+spa"))
    p.add_argument("--interface", dest="set_interface", metavar=tr("CODE"),
                   choices=sorted(interface.names()),
                   help=tr("the language of the interface ({codes})", codes=", ".join(sorted(interface.names()))))
    return parser


# ----------------------------------------------------------------- reading

def _default_languages() -> str:
    value = config.get("languages")
    return value if isinstance(value, str) and value else "eng"


def _target(a, source: Path) -> Path:
    if a.output is not None:
        return a.output
    if a.in_place:
        return source
    folder = a.output_dir if a.output_dir is not None else source.parent
    return folder / (source.name if a.output_dir is not None else f"{source.stem}-ocr.pdf")


def _open(path: Path, a):
    """The PDF at PATH, with the password given; on a terminal, asked for if it was not given (and then kept
    in A, for the PDFs that follow)."""
    try:
        return document.open_pdf(path, a.password or "")
    except document.PasswordError:
        if a.password is not None or not sys.stdin.isatty():
            raise
    a.password = getpass.getpass(tr("Password of {path}: ", path=path))
    return document.open_pdf(path, a.password)


def _check_reading(a, language: str) -> None:
    """Tesseract, the languages and the options of reading, checked once, before any file is read."""
    if not ocr.available():
        raise CliError(tr("tesseract is not installed: there is no OCR"))
    if not 0 <= a.doubtful <= 100:
        raise CliError(tr("--doubtful must be between 0 and 100"))
    if not 72 <= a.dpi <= 1200:
        raise CliError(tr("--dpi must be between 72 and 1200"))
    if a.jobs is not None and a.jobs < 1:
        raise CliError(tr("--jobs must be 1 or more"))
    try:
        ocr.parse_languages(language)
        if a.rotate and not ocr.has_osd():
            raise ocr.OcrError(tr("the orientation of the pages can't be found: tesseract's osd model is not "
                                  "there (it can be downloaded with: py-pdfocr download osd)"))
    except ocr.OcrError as e:
        raise CliError(str(e)) from None


def read_into(a, source: Path, target: Path, pages_spec: str | None, label: str | None = None) -> bool:
    """Read the scanned pages of SOURCE chosen by PAGES_SPEC, and write the PDF as TARGET. LABEL: the name
    put before the lines of the report (with several PDFs). Whether there was anything to read. Raises
    OcrError or DocumentError."""
    language = a.lang or _default_languages()
    progress = Progress(a.quiet)
    doc = _open(source, a)
    try:
        try:
            chosen = pagesel.parse_pages(pages_spec, doc.page_count)
        except pagesel.PageError as e:
            raise ocr.OcrError(str(e)) from None
        # (a page with text already would have its text twice)
        pages = [n for n in chosen if ocr.scanned(doc[n])]
        if not pages:
            print(tr("{path}: no page of those chosen is a scan without text", path=source))
            return False
        try:
            results = ocr.run(source, a.password or "", pages, language, rotate=a.rotate, doubtful=a.doubtful,
                              workers=a.jobs, dpi=a.dpi, progress=progress.pages)
        finally:
            progress.end()
        words = sum(ocr.write_words(doc[r.number], r) for r in results)
        if a.report:
            for r in results:
                for w in r.doubtful(a.doubtful):
                    print((f"{label}\t" if label else "") + f"{r.number + 1}\t{w.confidence:.0f}\t{w.text}")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            document.save(doc, target)
        except (OSError, RuntimeError, ValueError) as e:
            raise document.DocumentError(tr("{path} cannot be written: {error}", path=target, error=e)) from None
        doubtful = sum(len(r.doubtful(a.doubtful)) for r in results)
        turned = sum(1 for r in results if r.rotate)
        print(tr("Wrote {path}", path=target) + ": " + ", ".join(
            [ntr("{count} page read", "{count} pages read", len(results)),
             ntr("{count} word", "{count} words", words),
             ntr("{count} doubtful word", "{count} doubtful words", doubtful),
             *([ntr("{count} page turned", "{count} pages turned", turned)] if turned else [])]))
        return True
    finally:
        if not doc.is_closed:
            doc.close()


def cmd_read(a) -> int:
    if a.output is not None and len(a.inputs) > 1:
        raise CliError(tr("-o names one file: with several PDFs, use --output-dir or -i"))
    _check_reading(a, a.lang or _default_languages())
    failed = False
    for source in a.inputs:
        try:
            read_into(a, source, _target(a, source), a.pages, str(source) if len(a.inputs) > 1 else None)
        except (ocr.OcrError, document.DocumentError) as e:
            print(f"{PROG}: {source}: {e}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


def cmd_images(a) -> int:
    from .images import ImagesError, from_images

    if not a.no_ocr:
        _check_reading(a, a.lang or _default_languages())
    try:
        count = from_images(a.inputs, a.output, a.paper or "", a.landscape, a.margin)
    except ImagesError as e:
        raise CliError(str(e)) from None
    print(tr("Wrote {path} ({count} pages)", path=a.output, count=count))
    if a.no_ocr:
        return 0
    a.password = ""
    try:
        read_into(a, a.output, a.output, None)
    except (ocr.OcrError, document.DocumentError) as e:
        raise CliError(f"{a.output}: {e}") from None
    return 0


def cmd_scanned(a) -> int:
    failed = False
    for source in a.inputs:
        try:
            doc = _open(source, a)
        except document.DocumentError as e:
            print(f"{PROG}: {e}", file=sys.stderr)
            failed = True
            continue
        with doc:
            pages = [page.number + 1 for page in doc if ocr.scanned(page)]
            count = doc.page_count
        listed = _ranges(pages)
        print(f"{source}: " + ntr("{count} page is a scan without text", "{count} pages are scans without text",
                                  len(pages)) + " " + tr("(of {total})", total=count) + (f": {listed}" if pages else ""))
    return 1 if failed else 0


def _ranges(numbers: list[int]) -> str:
    """[1, 2, 3, 7, 9, 10] as '1-3, 7, 9-10'."""
    out, start = [], None
    for i, n in enumerate(numbers):
        if start is None:
            start = n
        if i + 1 == len(numbers) or numbers[i + 1] != n + 1:
            out.append(f"{start}-{n}" if n != start else str(n))
            start = None
    return ", ".join(out)


# ----------------------------------------------------------------- languages and models

def cmd_languages(a) -> int:
    version = ocr.version()
    there = set(ocr.models())
    print((tr("Tesseract {version}.", version=version) if version
           else tr("Tesseract is not installed: there is no OCR.")) + " "
          + ntr("{count} language can be read here.", "{count} languages can be read here.",
                len([n for n in there if n != "osd"])))
    print(tr("Orientation of pages (osd): {state}", state=tr("yes") if ocr.has_osd() else tr("no")))
    print(tr("Better models: {path}", path=ocr.own_tessdata()))
    if ocr.pdftools_tessdata().is_dir():
        print(tr("Better models of py-pdftools: {path}", path=ocr.pdftools_tessdata()))
    names = sorted(set(ocr.NAMES) | there if a.all else there,
                   key=lambda n: (n not in there, tr(ocr.NAMES.get(n, n)).casefold()))
    wanted = (a.filter or "").strip().casefold()
    rows = []
    for name in names:
        title = tr(ocr.NAMES[name]) if name in ocr.NAMES else name
        if wanted and wanted not in f"{name} {title}".casefold():
            continue
        better = ""
        model = ocr.better_model(name)
        if model is not None:
            st = model.stat()
            better = f"★ {st.st_size / 1e6:.0f} MB, {datetime.date.fromtimestamp(st.st_mtime).isoformat()}"
            if model.parent == ocr.pdftools_tessdata():
                better += " (py-pdftools)"
        rows.append((name, title, tr("yes") if ocr.installed(name) else "", better))
    if not rows:
        print(tr("No language has {text}.", text=a.filter) if wanted else tr("No language is there."))
        return 0
    head = (tr("Code"), tr("Language"), tr("With tesseract"), tr("Better model"))
    widths = [max(len(r[c]) for r in [head, *rows]) for c in range(3)]
    print()
    for row in [head, *rows]:
        print(("  ".join(cell.ljust(w) for cell, w in zip(row[:3], widths)) + "  " + row[3]).rstrip())
    if not a.all:
        print()
        print(tr("'py-pdfocr languages --all' shows those that can be downloaded too."))
    return 0


def cmd_download(a) -> int:
    progress = Progress()
    failed = False
    for name in a.names:
        def step(done: int, total: int, name=name) -> bool:
            size = f"{done / 1e6:.1f}" + (f" / {total / 1e6:.1f}" if total else "") + " MB"
            return progress.say(tr("Downloading {name}…", name=name) + " " + size)

        try:
            (path,) = ocr.download([name], step)
        except ocr.OcrError as e:
            progress.end()
            print(f"{PROG}: {e}", file=sys.stderr)
            failed = True
            continue
        progress.end()
        print(tr("Downloaded {path}", path=path))
    return 1 if failed else 0


def cmd_remove(a) -> int:
    failed = False
    for name in a.names:
        try:
            ocr.remove(name)
        except ocr.OcrError as e:
            print(f"{PROG}: {e}", file=sys.stderr)
            failed = True
            continue
        print(tr("Removed the better model of {name}", name=name)
              + (" " + tr("(the one installed with tesseract is used again)") if ocr.installed(name) else ""))
    return 1 if failed else 0


def cmd_settings(a) -> int:
    changes = {}
    if a.languages is not None:
        spec = "+".join(a.languages.replace(",", "+").split()).strip("+")
        try:
            if ocr.available():
                ocr.parse_languages(spec)
            elif not spec or not all(ocr.LANGUAGE.fullmatch(n) for n in spec.split("+")):
                raise ocr.OcrError(tr("{name} is not a language of tesseract", name=a.languages))
        except ocr.OcrError as e:
            raise CliError(str(e)) from None
        changes["languages"] = spec
    if a.set_interface is not None:
        if not interface.use(a.set_interface):
            raise CliError(tr("the language {code} cannot be used: {error}", code=a.set_interface,
                              error=interface.error()))
        changes["interface"] = a.set_interface
    if changes:
        try:
            config.set_many(changes)
        except OSError as e:
            raise CliError(tr("Could not keep the setting: {error}", error=e)) from None
    names = interface.names()
    current = config.get("interface")
    print(tr("Languages of the text: {languages}", languages=_default_languages()))
    print(tr("Interface: {name}", name=names.get(current, current))
          + " (" + ", ".join(f"{c}: {n}" for c, n in names.items()) + ")")
    print(tr("Configuration file: {path}", path=config.config_path()))
    return 0


# ----------------------------------------------------------------- main

def _command_at(argv: list[str]) -> int | None:
    """Where the command is, or should be, in ARGV: after the options of the program itself (--interface);
    None if ARGV only asks for the help or the version."""
    i = 0
    while i < len(argv):
        if argv[i] == "--interface":
            i += 2
        elif argv[i].startswith("--interface="):
            i += 1
        elif argv[i] in ("-h", "--help", "--version"):
            return None
        else:
            return i
    return None


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # La lengua se fija antes de construir el analizador: su ayuda y los mensajes de argparse salen traducidos.
    interface.use_configured(interface.option(argv))
    interface.translate_argparse()
    # 'py-pdfocr FILE.pdf' (or 'py-pdfocr -l lat FILE.pdf'): the command read, when none is given.
    at = _command_at(argv)
    if at is not None and argv[at] not in COMMANDS:
        argv.insert(at, "read")
    parser = build_parser()
    a = parser.parse_args(argv)
    if a.command is None:
        parser.print_help()
        return 1
    run = {"read": cmd_read, "images": cmd_images, "scanned": cmd_scanned, "languages": cmd_languages,
           "download": cmd_download, "remove": cmd_remove, "settings": cmd_settings}[a.command]
    try:
        return run(a)
    except CliError as e:
        print(f"{PROG}: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(f"\n{PROG}: " + tr("Stopped"), file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
