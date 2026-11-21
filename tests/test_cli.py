"""The command line (cli.py): read, images, scanned, languages, download, remove and settings."""

from __future__ import annotations

import pymupdf
import pytest
from conftest import needs_osd, needs_tesseract, picture, scan

from py_pdfocr import cli, config, ocr


@needs_tesseract
def test_read(tmp_path, capsys):
    path = scan(tmp_path / "scan.pdf", pages=2)
    assert cli.main(["read", str(path), "-l", "eng", "--pages", "2", "--report", "--doubtful", "100", "-q"]) == 0
    out = capsys.readouterr().out
    written = tmp_path / "scan-ocr.pdf"
    assert f"Wrote {written}" in out and "1 page read" in out
    assert any(line.startswith("2\t") for line in out.splitlines())  # (the doubtful words of page 2)
    doc = pymupdf.open(written)
    assert doc[0].get_text().strip() == "" and "zebras" in doc[1].get_text()
    # (in place, read being the command when none is given; and a second time, nothing left to read)
    assert cli.main([str(path), "-i", "-l", "eng"]) == 0
    assert "zebras" in pymupdf.open(path)[0].get_text()
    assert cli.main(["-l", "eng", "-i", str(path)]) == 0
    assert "no page of those chosen" in capsys.readouterr().out


@needs_tesseract
def test_read_several_into_a_folder(tmp_path, capsys):
    a, b = scan(tmp_path / "a.pdf"), scan(tmp_path / "b.pdf")
    out = tmp_path / "out"
    assert cli.main(["read", str(a), str(b), "--output-dir", str(out), "-l", "eng", "--report",
                     "--doubtful", "100", "-j", "1", "--dpi", "200"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "zebras" in pymupdf.open(out / "a.pdf")[0].get_text() and (out / "b.pdf").exists()
    # (with several PDFs, each line of the report begins with its file)
    assert any(line.startswith(f"{a}\t1\t") for line in lines) and any(line.startswith(f"{b}\t1\t") for line in lines)


@needs_tesseract
def test_a_pdf_with_a_password(tmp_path, capsys):
    path = scan(tmp_path / "locked.pdf", password="secret")
    assert cli.main(["read", str(path), "-l", "eng"]) == 1
    assert "protected by a password" in capsys.readouterr().err
    assert cli.main(["read", str(path), "-l", "eng", "--password", "secret", "-o", str(tmp_path / "x.pdf")]) == 0
    doc = pymupdf.open(tmp_path / "x.pdf")
    # (it stays protected)
    assert doc.needs_pass and doc.authenticate("secret") and "zebras" in doc[0].get_text()


@needs_tesseract
@needs_osd
def test_read_turning_the_pages(tmp_path, osd, capsys):
    path = scan(tmp_path / "turned.pdf", rotation=90, pages=2)
    assert cli.main([str(path), "-l", "eng", "--rotate", "-q"]) == 0
    assert "2 pages turned" in capsys.readouterr().out
    doc = pymupdf.open(tmp_path / "turned-ocr.pdf")
    assert doc[1].rotation == 0 and "zebras" in doc[1].get_text()


def test_turning_needs_osd(tmp_path, capsys):
    if not ocr.available() or ocr.has_osd():
        pytest.skip("needs tesseract, without its osd model")
    assert cli.main([str(scan(tmp_path / "s.pdf")), "--rotate"]) == 1
    assert "py-pdfocr download osd" in capsys.readouterr().err


def test_wrong_reading(tmp_path, capsys):
    path = scan(tmp_path / "scan.pdf")
    if ocr.available():
        assert cli.main(["read", str(path), "-l", "klingon"]) == 1 and "klingon" in capsys.readouterr().err
        assert cli.main(["read", str(path), "-l", "eng", "--doubtful", "120"]) == 1
        assert cli.main(["read", str(path), "-l", "eng", "--dpi", "20"]) == 1
        assert cli.main(["read", str(path), "-l", "eng", "--jobs", "0"]) == 1
        assert cli.main(["read", str(path), "-l", "eng", "--pages", "7"]) == 1
        assert "out of range" in capsys.readouterr().err
        assert cli.main(["read", str(tmp_path / "missing.pdf"), "-l", "eng"]) == 1
    assert cli.main(["read", str(path), str(path), "-o", str(tmp_path / "x.pdf")]) == 1
    assert "-o names one file" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        cli.main(["read"])
    assert cli.main([]) == 1


@needs_tesseract
def test_images(tmp_path, capsys):
    shot = tmp_path / "page.png"
    picture(150).save(shot)
    target = tmp_path / "made" / "pics.pdf"
    assert cli.main(["images", str(shot), str(shot), "-o", str(target), "--paper", "A4", "--margin", "10",
                     "-l", "eng", "-q"]) == 0
    out = capsys.readouterr().out
    assert "Wrote" in out and "2 pages read" in out
    doc = pymupdf.open(target)
    assert doc.page_count == 2 and round(doc[0].rect.width) == 595 and "zebras" in doc[1].get_text()
    assert cli.main(["images", str(shot), "-o", str(tmp_path / "plain.pdf"), "--no-ocr"]) == 0
    assert ocr.scanned(pymupdf.open(tmp_path / "plain.pdf")[0])
    assert cli.main(["images", str(tmp_path / "plain.pdf"), "-o", str(tmp_path / "x.pdf"), "--no-ocr"]) == 1
    assert "is not a picture" in capsys.readouterr().err


def test_scanned_pages(tmp_path, capsys):
    path = scan(tmp_path / "scan.pdf", pages=4)
    doc = pymupdf.open(path)
    doc[2].insert_text((72, 72), "Some text")
    doc.save(tmp_path / "mixed.pdf")
    assert cli.main(["scanned", str(path), str(tmp_path / "mixed.pdf")]) == 0
    out = capsys.readouterr().out
    assert "4 pages are scans without text (of 4): 1-4" in out
    assert "3 pages are scans without text (of 4): 1-2, 4" in out
    assert cli.main(["scanned", str(tmp_path / "nothing.pdf")]) == 1


def test_ranges():
    assert cli._ranges([1, 2, 3, 7, 9, 10]) == "1-3, 7, 9-10" and cli._ranges([]) == ""


def test_languages(own, capsys):
    own.mkdir(parents=True)
    (own / "lat.traineddata").write_bytes(b"x" * 2_000_000)
    assert cli.main(["languages"]) == 0
    out = capsys.readouterr().out
    assert "Tesseract" in out and "Latin" in out and "★ 2 MB" in out and "Welsh" not in out
    assert cli.main(["languages", "--all", "wel"]) == 0
    out = capsys.readouterr().out
    assert "cym" in out and "Welsh" in out and "Latin" not in out
    assert cli.main(["languages", "klingon"]) == 0 and "No language has klingon" in capsys.readouterr().out


def test_download_and_remove(own, capsys, monkeypatch):
    def download(names, progress=None):
        if names == ["nope"]:
            raise ocr.OcrError("nope could not be downloaded: there is no such language")
        progress(5, 10)
        own.mkdir(parents=True, exist_ok=True)
        made = own / f"{names[0]}.traineddata"
        made.write_bytes(b"model")
        return [made]

    monkeypatch.setattr(ocr, "download", download)
    assert cli.main(["download", "lat", "osd"]) == 0
    assert "osd.traineddata" in capsys.readouterr().out and ocr.better("osd")
    assert cli.main(["download", "nope", "spa"]) == 1
    captured = capsys.readouterr()
    assert "no such language" in captured.err and "spa.traineddata" in captured.out
    assert cli.main(["remove", "osd", "lat"]) == 0
    # (the one downloaded is gone; tesseract may have its own osd, which is used again)
    assert "Removed the better model of osd" in capsys.readouterr().out and not ocr.better("osd")
    assert cli.main(["remove", "osd"]) == 1 and "was not downloaded" in capsys.readouterr().err


def test_settings(capsys):
    assert cli.main(["settings"]) == 0
    assert "Languages of the text: eng" in capsys.readouterr().out
    if ocr.available() and "eng" in ocr.languages():
        assert cli.main(["settings", "--languages", "eng"]) == 0
        assert config.get("languages") == "eng"
        assert cli.main(["settings", "--languages", "klingon"]) == 1
    assert cli.main(["settings", "--interface", "es"]) == 0
    assert "Idiomas del texto" in capsys.readouterr().out and config.get("interface") == "es"
    # (kept: the next run speaks Spanish, unless --interface says otherwise)
    assert cli.main(["scanned", "missing.pdf"]) == 1 and "no se puede leer" in capsys.readouterr().err
    assert cli.main(["--interface", "en", "scanned", "missing.pdf"]) == 1
    assert "cannot be read" in capsys.readouterr().err
    assert "interface = \"es\"" in config.config_path().read_text()


def test_a_protected_pdf_kept_readable(tmp_path):
    """(the key of an AES-256 file is not spoilt before it is saved: what is written stays readable, and so do
    its pictures)"""
    from py_pdfocr import document

    path = scan(tmp_path / "locked.pdf", password="secret")
    doc = document.open_pdf(path, "secret")
    doc[0].insert_text((72, 72), "hello", render_mode=3)
    document.save(doc, tmp_path / "out.pdf")
    out = pymupdf.open(tmp_path / "out.pdf")
    assert out.needs_pass and out.authenticate("secret") and out[0].get_text().strip() == "hello"
    assert min(out[0].get_pixmap(dpi=30).samples) < 128  # (the picture is drawn: some dark letters)
    plain = document.open_pdf(scan(tmp_path / "plain.pdf"))
    assert document.kept_encryption(plain) == pymupdf.PDF_ENCRYPT_NONE
