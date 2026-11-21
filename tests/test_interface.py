"""The interface in Spanish (locale/es.xml): every text of the code has its translation there, and the file
has no other (but argparse's own texts)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from py_pdfocr import interface

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from texts import texts


def _argparse_texts() -> set[str]:
    source = Path(argparse.__file__).read_text(encoding="utf-8")
    found = re.findall(r"""_\(\s*['"](.+?)['"]\s*\)""", source, flags=re.DOTALL)
    found += [t for pair in re.findall(r"""ngettext\(\s*['"](.+?)['"],\s*['"](.+?)['"]""", source, flags=re.DOTALL)
              for t in pair]
    return {" ".join(t.split()) for t in found}


def test_every_text_is_translated():
    translated = interface.read(interface.FOLDER / "es.xml")
    missing = texts() - set(translated)
    assert not missing, f"not in locale/es.xml: {sorted(missing)}"
    unused = set(translated) - texts() - _argparse_texts()
    assert not unused, f"in locale/es.xml, but not used: {sorted(unused)}"


def test_languages_of_the_interface():
    assert interface.names() == {"en": "English", "es": "Español"}
    assert interface.use("es") and interface.tr("Wrote {path}", path="x.pdf") == "Se escribió x.pdf"
    assert interface.ntr("{count} page read", "{count} pages read", 2).startswith("2 ")
    assert not interface.use("xx") and interface.code() == "en" and "xx" in interface.error()
    assert interface.option(["--interface", "es", "x"]) == "es" and interface.option(["--interface=es"]) == "es"
