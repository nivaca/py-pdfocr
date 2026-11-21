"""A PDF made of pictures (photographs, scans), a page for each, to be read afterwards."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from . import document
from .interface import tr

PAPERS = {"A3": (297, 420), "A4": (210, 297), "A5": (148, 210), "Letter": (215.9, 279.4),
          "Legal": (215.9, 355.6)}  # (millimetres)
MM = 72 / 25.4


class ImagesError(Exception):
    """Pictures that cannot be made a PDF."""


def _frames(path: Path) -> pymupdf.Document:
    """The picture at PATH as a PDF of one page for each of its frames, each as big as the frame is (at the
    resolution the picture says; at 96 dpi if it says none)."""
    try:
        with pymupdf.open(path) as img:
            if img.is_pdf:
                raise ImagesError(tr("{path} is not a picture", path=path))
            return pymupdf.open("pdf", img.convert_to_pdf())
    except ImagesError:
        raise
    except Exception as e:  # noqa: BLE001  (MuPDF tiene errores propios para cada formato que no entiende)
        raise ImagesError(tr("{path} cannot be read as a picture: {error}", path=path, error=e)) from None


def from_images(images: list[Path], target: Path, paper: str = "", landscape: bool | None = None,
                margin: float = 0) -> int:
    """A PDF of IMAGES, a page for each (or for each frame of one), saved as TARGET. PAPER: a size of PAPERS
    on which each picture is put, as large as fits within MARGIN (millimetres), and centred; '' for pages as
    big as the pictures (and MARGIN around them). LANDSCAPE: the paper lying (True) or standing (False);
    None, as each picture is. Returns how many pages it has."""
    if not images:
        raise ImagesError(tr("There are no pictures"))
    out = pymupdf.open()
    try:
        for path in images:
            with _frames(path) as frames:
                for n in range(frames.page_count):
                    pic = frames[n].rect
                    m = margin * MM
                    if paper:
                        w, h = (v * MM for v in PAPERS[paper])
                        lying = pic.width > pic.height if landscape is None else landscape
                        if lying:
                            w, h = h, w
                    else:
                        w, h = pic.width + 2 * m, pic.height + 2 * m
                    page = out.new_page(width=w, height=h)
                    room = pymupdf.Rect(m, m, w - m, h - m)
                    if room.is_empty:
                        raise ImagesError(tr("The margin leaves no room for the pictures"))
                    # keep_proportion: la imagen tan grande como quepa, centrada en el espacio que deja el margen.
                    page.show_pdf_page(room, frames, n, keep_proportion=True)
        count = out.page_count
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            document.save(out, target)
        except (OSError, RuntimeError, ValueError) as e:
            raise ImagesError(tr("{path} cannot be written: {error}", path=target, error=e)) from None
        return count
    finally:
        if not out.is_closed:
            out.close()
