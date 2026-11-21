"""Every test runs with its own configuration and its own folders of models (empty), in a folder of its own,
so that the user's are never read or changed."""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from py_pdfocr import interface, ocr

LINES = ["The quick brown fox jumps over the lazy dog.", "Pack my box with five dozen liquor jugs.",
         "How vexingly quick daft zebras jump.", "Sphinx of black quartz, judge my vow."]

needs_tesseract = pytest.mark.skipif(not ocr.available() or "eng" not in ocr.languages(),
                                     reason="needs tesseract, with English")
# tesseract's osd model, wherever the user has it (found before the tests change the folders of models)
OSD = ocr.models().get("osd")
needs_osd = pytest.mark.skipif(OSD is None, reason="needs tesseract's osd model (py-pdfocr download osd)")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("PY_PDFOCR_CONFIG", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "data"))
    interface.use(None)
    yield
    interface.use(None)


@pytest.fixture
def osd(own):
    """The user's osd model, linked into the folder of the test."""
    own.mkdir(parents=True, exist_ok=True)
    if not ocr.has_osd():
        (own / "osd.traineddata").symlink_to(OSD)


@pytest.fixture
def own():
    """py-pdfocr's own folder of models (empty, in the folder of the test)."""
    return ocr.own_tessdata()


def picture(dpi: int = 200) -> pymupdf.Pixmap:
    """A picture of a page of text, as scanned."""
    text = pymupdf.open()
    page = text.new_page()
    for i, line in enumerate(LINES * 3):
        page.insert_text((60, 90 + i * 34), line, fontsize=15)
    return page.get_pixmap(dpi=dpi)


def scan(path: Path, rotation: int = 0, pages: int = 1, password: str = "") -> Path:
    """A PDF whose pages are pictures of text (as scanned), shown turned ROTATION degrees."""
    shot = picture()
    doc = pymupdf.open()
    for _ in range(pages):
        p = doc.new_page()
        p.insert_image(p.rect, pixmap=shot)
        p.set_rotation(rotation)
    if password:
        doc.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password + "!")
    else:
        doc.save(path)
    return path
