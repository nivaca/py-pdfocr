"""Opening a PDF and saving it: with its password, if it has one; saved through a temporary file beside the
target, keeping its protection."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pymupdf

from .interface import tr


class DocumentError(Exception):
    """A PDF that cannot be opened or written."""


class PasswordError(DocumentError):
    """A PDF whose password is missing or wrong."""


def open_pdf(path: Path, password: str = "") -> pymupdf.Document:
    """The PDF at PATH, opened with PASSWORD if it needs one (raises DocumentError, or PasswordError)."""
    # PyMuPDF also opens pictures and other formats; is_pdf, below, turns them away.
    try:
        doc = pymupdf.open(path)
    except (pymupdf.FileNotFoundError, pymupdf.FileDataError, RuntimeError) as e:
        raise DocumentError(tr("{path} cannot be read as a PDF: {error}", path=path, error=e)) from None
    if not doc.is_pdf:
        doc.close()
        raise DocumentError(tr("{path} is not a PDF", path=path))
    # needs_pass es falso para un archivo con solo contraseña de permisos: esos se abren sin preguntar.
    if doc.needs_pass and not doc.authenticate(password):
        doc.close()
        raise PasswordError(tr("{path} is protected by a password", path=path))
    return doc


def kept_encryption(doc: pymupdf.Document) -> int:
    """How DOC is to be saved: protected as it is (with its passwords and permissions), if it is; else not.
    The metadata say it ('encryption'), also of a file with only a permissions password, which opens without
    asking. (Not needs_pass: asked after authenticate, MuPDF tries the empty password again, which spoils the
    key of an AES-256 file; whatever is written afterwards cannot be read.)"""
    encrypted = bool((doc.metadata or {}).get("encryption"))
    return pymupdf.PDF_ENCRYPT_KEEP if encrypted else pymupdf.PDF_ENCRYPT_NONE


def save(doc: pymupdf.Document, target: Path) -> None:
    """Save DOC as TARGET, safely (through a file of its own, put in its place at the end). If TARGET is
    the file DOC was opened from, DOC is closed first (Windows won't replace a file that is open)."""
    fd, tmp = tempfile.mkstemp(suffix=".pdf", dir=target.parent)
    os.close(fd)
    try:
        # garbage=1 quita los objetos que ya nada usa, sin renumerar los demás.
        doc.save(tmp, garbage=1, deflate=True, encryption=kept_encryption(doc))
        if doc.name and Path(doc.name).resolve() == target.resolve():
            doc.close()
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
