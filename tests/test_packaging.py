"""The version is the same everywhere it is written: pyproject.toml, the package, the changelogs and the
Spanish description."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import py_pdfocr

ROOT = Path(__file__).resolve().parent.parent


def test_one_version():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    assert py_pdfocr.__version__ == version
    for changelog in ("CHANGELOG.md", "CHANGELOG_es.md"):
        first = re.search(r"^## (\S+)", (ROOT / changelog).read_text(encoding="utf-8"), flags=re.MULTILINE)
        assert first and first.group(1) == version, changelog
    title = (ROOT / "docs" / "DESCRIPCIÓN_es.md").read_text(encoding="utf-8").splitlines()[0]
    assert title == f"# py-pdfocr {version}: descripción"
    for readme in ("README.md", "README_es.md"):
        assert version in (ROOT / readme).read_text(encoding="utf-8"), readme
