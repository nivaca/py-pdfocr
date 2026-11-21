#!/usr/bin/env python3
"""Make an AppImage of py-pdfocr, for Linux:

    uv run python tools/bundle-appimage.py [-o FOLDER] [--python APPIMAGE]
                                          [--python-version 3.14] [--appimagetool APPIMAGE]

The AppImage is dist/py-pdfocr-VERSION-x86_64.AppImage (the version of
pyproject.toml; --output gives another folder). It holds a Python of its own
(a relocatable Python of the python-appimage project,
https://github.com/niess/python-appimage) with py-pdfocr and PyMuPDF
installed into it, so it runs on any recent Linux (glibc 2.28 or later)
without installing anything but tesseract, which it runs as the system has
it:

    py-pdfocr.AppImage scan.pdf -l lat+spa
    py-pdfocr.AppImage languages

What it needs is downloaded the first time and kept in the user's cache
folder (~/.cache/py-pdfocr-build): the Python and appimagetool
(https://github.com/AppImage/appimagetool). The program's wheel is made with
"uv build", and its dependencies come from PyPI (so this needs the network).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
APP_ID = "py-pdfocr"
ARCH = "x86_64"
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
# What the program needs, from pyproject.toml, installed alone (--no-deps)
DEPENDENCIES = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]

# The Python put in the AppImage (python-appimage has one release per version,
# with an AppImage per manylinux).
PYTHON = "3.14"
PYTHON_RELEASES = "https://api.github.com/repos/niess/python-appimage/releases/tags/python{version}"
MANYLINUX = ("manylinux_2_28", "manylinux2014")
APPIMAGETOOL = f"https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-{ARCH}.AppImage"

DESKTOP = (ROOT / "packaging" / f"{APP_ID}.desktop").read_text(encoding="utf-8")

# %(python)s: the interpreter, relative to the AppDir
APPRUN = r"""#!/bin/bash
#  Starts py-pdfocr in the AppImage (made by tools/bundle-appimage.py).
ROOT="$(dirname "$(readlink -f -- "$0")")"
export APPDIR="${APPDIR:-$ROOT}"
PYTHON="$APPDIR/%(python)s"
#  (the AppImage cannot be written to)
export PYTHONDONTWRITEBYTECODE=1
#  Only what is inside the AppImage: not the user's site-packages, nor
#  another Python's settings
export PYTHONNOUSERSITE=1
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP VIRTUAL_ENV
exec "$PYTHON" -m py_pdfocr "$@"
"""


def say(text: str):
    print(text, file=sys.stderr, flush=True)


def name() -> str:
    return f"{APP_ID}-{VERSION}-{ARCH}.AppImage"


def cache_dir() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    path = base / "py-pdfocr-build"
    path.mkdir(parents=True, exist_ok=True)
    return path


def download(url: str, path: Path) -> Path:
    """Download URL into PATH (unless it is there already)."""
    if not path.is_file():
        say(f"Downloading {url} ...")
        tmp = path.with_name(path.name + ".tmp")
        with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
        os.replace(tmp, path)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def python_appimage(version: str) -> Path:
    """The Python AppImage of VERSION, for the newest manylinux there is one for."""
    url = PYTHON_RELEASES.format(version=version)
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=60) as r:
        assets = json.load(r)["assets"]
    tag = "cp" + version.replace(".", "")
    for manylinux in MANYLINUX:
        end = f"-{tag}-{tag}-{manylinux}_{ARCH}.AppImage"  # (not the free-threaded cp3XXt)
        found = [a["browser_download_url"] for a in assets if a["name"].endswith(end)]
        if found:
            return download(found[0], cache_dir() / found[0].rsplit("/", 1)[1])
    raise OSError(f"there is no Python {version} AppImage at {url}")


def wheel(folder: Path) -> Path:
    """The program's wheel, made with uv build."""
    if not shutil.which("uv"):
        raise OSError("uv is needed to make the wheel (https://docs.astral.sh/uv/)")
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(folder)], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    found = sorted(folder.glob(f"py_pdfocr-{VERSION}-*.whl"))
    if not found:
        raise OSError("uv build made no wheel")
    return found[0]


def make_appdir(appdir: Path, whl: Path):
    """Turn the AppDir of the Python into that of py-pdfocr."""
    pythons = [p for p in sorted(appdir.glob("opt/python3*/bin/python3.*")) if not p.name.endswith("-config")]
    if not pythons:
        raise OSError(f"there is no Python in {appdir}")
    python = pythons[0]
    say(f"Installing py-pdfocr and its dependencies into {python.relative_to(appdir)} ...")
    # Everything must go inside: pip must not see packages of the user's
    # site-packages (or another environment) as already installed.
    env = clean_env()
    subprocess.run([str(python), "-s", "-m", "pip", "install", "--isolated", "--no-cache-dir",
                    "--no-warn-script-location", "--disable-pip-version-check", "--quiet",
                    # (PyMuPDF without what it brings for its analysis of layouts, onnxruntime, numpy
                    # and others, some 200 MB that py-pdfocr never uses; see DEPENDENCIES)
                    "--no-deps", str(whl), *DEPENDENCIES],
                   check=True, env=env)
    # Out with what makes it the Python's AppImage
    for pattern in ("AppRun", "*.desktop", "*.png", "*.svg", ".DirIcon", "usr/share/applications",
                    "usr/share/metainfo"):
        for path in appdir.glob(pattern):
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
    apprun = appdir / "AppRun"
    apprun.write_text(APPRUN % {"python": python.relative_to(appdir)},
                      encoding="utf-8", newline="\n")
    apprun.chmod(0o755)
    (appdir / f"{APP_ID}.desktop").write_text(DESKTOP, encoding="utf-8", newline="\n")
    shutil.copy2(ROOT / "packaging" / f"{APP_ID}.png", appdir / f"{APP_ID}.png")
    os.symlink(f"{APP_ID}.png", appdir / ".DirIcon")
    for kind, folder in (("png", "256x256"), ("svg", "scalable")):
        target = appdir / "usr" / "share" / "icons" / "hicolor" / folder / "apps"
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "packaging" / f"{APP_ID}.{kind}", target / f"{APP_ID}.{kind}")


def clean_env(**extra) -> dict:
    """The environment without anything that would make a Python look outside its own folders."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("PYTHON", "PIP_", "VIRTUAL_ENV", "UV_", "CONDA"))}
    env.update(PYTHONNOUSERSITE="1", **extra)
    return env


def check_imports(appdir: Path):
    """Stop if the bundled Python can't import what the program needs, on its own."""
    python = next(p for p in sorted(appdir.glob("opt/python3*/bin/python3.*")) if not p.name.endswith("-config"))
    code = ("import pymupdf, py_pdfocr.cli, py_pdfocr.images; from py_pdfocr import ocr, interface; "
            "d = pymupdf.open(); p = d.new_page(); p.insert_text((72, 72), 'x'); "
            "assert not ocr.scanned(p); assert interface.use('es'); "
            "print(pymupdf.VersionBind)")
    r = subprocess.run([str(python), "-s", "-c", code], capture_output=True, text=True, check=False,
                       env=clean_env(APPDIR=str(appdir)))
    if r.returncode != 0:
        raise OSError(f"the bundled Python cannot run the program:\n{r.stderr.strip()}")
    say(f"Bundled PyMuPDF {r.stdout.strip()} (a page written and read, the Spanish interface loaded)")


def smoke_test(appimage: Path):
    """Run the AppImage as a user with nothing installed would: an empty home folder."""
    with tempfile.TemporaryDirectory() as home:
        env = clean_env(HOME=home, XDG_CONFIG_HOME=f"{home}/.config", XDG_CACHE_HOME=f"{home}/.cache",
                        XDG_DATA_HOME=f"{home}/.local/share", APPIMAGE_EXTRACT_AND_RUN="1")
        r = subprocess.run([str(appimage), "--version"], capture_output=True, text=True, env=env, cwd=home,
                           check=False)
        if r.returncode != 0 or VERSION not in r.stdout:
            raise OSError(f"the AppImage failed (--version):\n{(r.stderr or r.stdout).strip()}")
    say("The AppImage runs on its own (empty home folder): --version.")


def open_to_all(appdir: Path):
    """Let everyone read the AppDir: folders 0755, files 0644, or 0755 if they can be run."""
    for folder, dirs, names in os.walk(appdir):
        for d in dirs:
            p = Path(folder, d)
            if not p.is_symlink():
                p.chmod(0o755)
        for n in names:
            p = Path(folder, n)
            if not p.is_symlink():
                p.chmod(0o755 if p.stat().st_mode & stat.S_IXUSR else 0o644)
    appdir.chmod(0o755)


def bundle(output: Path, python: Path | None = None, appimagetool: Path | None = None,
           version: str = PYTHON) -> Path:
    python = python or python_appimage(version)
    appimagetool = appimagetool or download(APPIMAGETOOL, cache_dir() / Path(APPIMAGETOOL).name)
    path = output / name()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        subprocess.run([str(python.resolve()), "--appimage-extract"], cwd=tmp, check=True,
                       stdout=subprocess.DEVNULL)
        appdir = tmp / "squashfs-root"
        make_appdir(appdir, wheel(tmp / "wheel"))
        check_imports(appdir)
        open_to_all(appdir)
        # (without FUSE, as in a container, the tool runs extracted)
        env = dict(os.environ, ARCH=ARCH, APPIMAGE_EXTRACT_AND_RUN="1")
        tmp_out = path.with_name(path.name + ".tmp")
        subprocess.run([str(appimagetool.resolve()), "--no-appstream", "--comp", "zstd", str(appdir),
                        str(tmp_out)], check=True, env=env, stdout=subprocess.DEVNULL)
    os.replace(tmp_out, path)
    smoke_test(path)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tools/bundle-appimage.py",
                                     description=f"Make an AppImage of py-pdfocr: {name()}, with a Python of "
                                                 "its own.")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="the folder to write it in (default: dist/)")
    parser.add_argument("--python", type=Path, metavar="APPIMAGE",
                        help="the Python AppImage to use (default: one of python-appimage, downloaded)")
    parser.add_argument("--python-version", default=PYTHON, metavar="VERSION",
                        help=f"the version of Python to download (default: {PYTHON})")
    parser.add_argument("--appimagetool", type=Path, metavar="APPIMAGE",
                        help="the appimagetool to use (default: downloaded)")
    args = parser.parse_args(argv)
    if not sys.platform.startswith("linux"):
        sys.exit("bundle-appimage.py: AppImages are made on Linux")
    output = args.output or DIST
    output.mkdir(parents=True, exist_ok=True)
    try:
        path = bundle(output, args.python, args.appimagetool, args.python_version)
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError, StopIteration) as e:
        sys.exit(f"bundle-appimage.py: {e}")
    print(f"Wrote {path} ({path.stat().st_size / 1e6:.1f} MB).")


if __name__ == "__main__":
    main()
