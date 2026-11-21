"""OCR with the tesseract program (ocr.py): the words of a scan, read in other processes, with their place
and confidence; written as invisible text; pages lying sideways turned; the languages, those installed and
those downloaded (here, and by py-pdftools)."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import ClassVar

import pymupdf
import pytest
from conftest import needs_osd, needs_tesseract, scan

from py_pdfocr import interface, ocr


@needs_tesseract
def test_a_scan_read_and_written(tmp_path):
    path = scan(tmp_path / "scan.pdf", pages=2)
    seen = []
    results = ocr.run(path, "", [0, 1], "eng", progress=lambda done, of: seen.append((done, of)) or True)
    assert [r.number for r in results] == [0, 1] and seen[-1] == (2, 2)
    words = [w.text.strip(".,") for w in results[0].words]
    assert {"quick", "brown", "zebras", "quartz"} <= set(words)
    fox = next(w for w in results[0].words if w.text == "fox")
    assert 0 < fox.rect[0] < fox.rect[2] < 612 and 60 < fox.rect[1] < 120 and fox.confidence > ocr.DOUBTFUL
    doc = pymupdf.open(path)
    assert ocr.scanned(doc[0])
    assert ocr.write_words(doc[0], results[0], corrections={0: ""}) == len(results[0].words) - 1
    text = doc[0].get_text()
    assert not ocr.scanned(doc[0]) and "zebras" in text and "Sphinx" in text
    # (where the picture shows it: the word found is under the fox)
    found = doc[0].search_for("fox")[0]
    assert abs(found.x0 - fox.rect[0]) < 6 and abs(found.y1 - fox.rect[3]) < 6


@needs_tesseract
def test_doubtful_words_come_with_their_picture(tmp_path):
    """(read in this process: everything is doubtful below 101)"""
    path = scan(tmp_path / "scan.pdf")
    with tempfile.TemporaryDirectory() as folder:
        tessdata = str(ocr.tessdata_for(["eng"], Path(folder)))
        result = ocr.read_page(str(path), "", 0, "eng", tessdata, doubtful=101)
    assert result.doubtful(101) == list(result.words)
    shot = pymupdf.Pixmap(result.words[0].crop)
    assert shot.width > 10 and shot.height > 10


@needs_tesseract
def test_stopped_and_a_lower_resolution(tmp_path):
    path = scan(tmp_path / "scan.pdf", pages=3)
    with pytest.raises(ocr.OcrError, match="Stopped"):
        ocr.run(path, "", [0, 1, 2], "eng", progress=lambda done, of: False)
    (result,) = ocr.run(path, "", [1], "eng", dpi=150, workers=1)
    assert result.number == 1 and "zebras" in [w.text for w in result.words]


@needs_tesseract
def test_errors_of_the_processes_speak_the_interface(tmp_path, own):
    """(a model that tesseract can't load: the message, in Spanish, comes from the process that read the page)"""
    path = scan(tmp_path / "scan.pdf")
    own.mkdir(parents=True)
    (own / "xyz.traineddata").write_bytes(b"not a model")
    interface.use("es")
    with pytest.raises(ocr.OcrError, match="^tesseract falló"):
        ocr.run(path, "", [0], "xyz")


@needs_tesseract
@needs_osd
@pytest.mark.parametrize("rotation", [90, 180, 270])
def test_a_page_lying_sideways_is_turned(tmp_path, osd, rotation):
    path = scan(tmp_path / "turned.pdf", rotation=rotation)
    (result,) = ocr.run(path, "", [0], "eng", rotate=True)
    assert result.rotate == (360 - rotation) % 360 and "quick" in [w.text for w in result.words]
    doc = pymupdf.open(path)
    ocr.write_words(doc[0], result)
    assert doc[0].rotation == 0 and "zebras" in doc[0].get_text()


def test_languages_installed_and_downloaded(tmp_path, own):
    own.mkdir(parents=True)
    (own / "xyz.traineddata").write_bytes(b"model")
    assert "xyz" in ocr.languages() and ocr.better("xyz") and not ocr.better("nothing")
    assert ocr.better_model("xyz") == own / "xyz.traineddata"
    assert ocr.parse_languages("xyz") == ["xyz"]
    for wrong in ("", "osd", "x y", "nothing"):
        with pytest.raises(ocr.OcrError):
            ocr.parse_languages(wrong)
    folder = ocr.tessdata_for(["xyz"], tmp_path / "run")
    assert (folder / "xyz.traineddata").read_bytes() == b"model"
    if ocr.system_tessdata() is not None and "eng" in ocr.languages():
        # (a downloaded model goes before the installed one of the same language)
        (own / "eng.traineddata").write_bytes(b"better")
        assert ocr.models()["eng"] == own / "eng.traineddata"


def test_the_models_of_py_pdftools(own):
    """Those py-pdftools downloaded are used, under py-pdfocr's own; only py-pdftools removes them."""
    theirs = ocr.pdftools_tessdata()
    theirs.mkdir(parents=True)
    (theirs / "abc.traineddata").write_bytes(b"theirs")
    assert "abc" in ocr.languages() and ocr.better("abc") and ocr.better_model("abc") == theirs / "abc.traineddata"
    with pytest.raises(ocr.OcrError, match="py-pdftools"):
        ocr.remove("abc")
    own.mkdir(parents=True)
    (own / "abc.traineddata").write_bytes(b"ours")
    assert ocr.models()["abc"] == own / "abc.traineddata"
    ocr.remove("abc")
    assert not (own / "abc.traineddata").exists() and (theirs / "abc.traineddata").exists()
    with pytest.raises(ocr.OcrError, match="not downloaded"):
        ocr.remove("nothing")
    with pytest.raises(ocr.OcrError):
        ocr.remove("../abc")


def test_download(own, monkeypatch):
    class Answer(io.BytesIO):
        headers: ClassVar = {"Content-Length": "11"}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    asked = []

    def urlopen(request, timeout=0):
        asked.append((request.full_url, request.get_header("User-agent")))
        if "nope" in request.full_url:
            raise OSError("HTTP Error 404: Not Found")
        return Answer(b"model bytes")

    monkeypatch.setattr(ocr.urllib.request, "urlopen", urlopen)
    sizes = []
    (made,) = ocr.download(["lat"], progress=lambda done, total: sizes.append((done, total)) or True)
    assert made == own / "lat.traineddata" and made.read_bytes() == b"model bytes" and sizes[-1] == (11, 11)
    # (a plain request: nothing about the user goes with it)
    assert asked == [(ocr.BEST_URL.format(name="lat"), "py-pdfocr")] and ocr.better("lat")
    with pytest.raises(ocr.OcrError, match="no such language"):
        ocr.download(["nope"])
    assert not (own / "nope.part").exists() and not (own / "nope.traineddata").exists()
    with pytest.raises(ocr.OcrError, match="Stopped"):
        ocr.download(["spa"], progress=lambda done, total: False)
    assert not (own / "spa.part").exists() and not (own / "spa.traineddata").exists()
    with pytest.raises(ocr.OcrError):
        ocr.download(["../x"])


def test_scanned(tmp_path):
    assert ocr.scanned(pymupdf.open(scan(tmp_path / "scan.pdf"))[0])
    doc = pymupdf.open()
    doc.new_page()
    doc.new_page().insert_text((72, 72), "Some text")
    assert not ocr.scanned(doc[0]) and not ocr.scanned(doc[1])
