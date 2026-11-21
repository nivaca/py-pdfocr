#!/usr/bin/env bash
# Installs py-pdfocr from this folder of its source, for this user, on Linux
# or macOS, to run with Python (3.14 or later): no binaries are built.
#
#     install/install.sh                    install, or update
#     install/install.sh --python PYTHON    with that Python
#     install/install.sh --uninstall        remove what it installed
#
# It makes a virtual environment of its own and installs py-pdfocr in it,
# with PyMuPDF from PyPI (so it needs internet the first time):
#   Linux:  ~/.local/share/py-pdfocr/venv;
#   macOS:  ~/Library/Application Support/py-pdfocr/venv.
# The command py-pdfocr is linked in ~/bin, if that folder exists, or else
# in ~/.local/bin. Nothing needs root, and nothing is put anywhere else; the
# settings and the models downloaded are never touched. Tesseract is not
# installed by this: it comes from the system's packages (or Homebrew).
#
# py-pdfocr: Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# SPDX-License-Identifier: GPL-3.0-or-later (see LICENSE)

set -euo pipefail

NAME=py-pdfocr
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
ROOT=$(dirname -- "$HERE")

usage() {
    sed -n '2,17s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"
}

die() {
    echo "install.sh: $*" >&2
    exit 1
}

say() {
    echo "==> $*"
}

case "$(uname -s)" in
    Linux) SYSTEM=linux ;;
    Darwin) SYSTEM=macos ;;
    *) die "this is for Linux and macOS; on Windows, use install\\install.bat" ;;
esac

if [[ "$SYSTEM" == macos ]]; then
    DATA="$HOME/Library/Application Support/$NAME"
else
    DATA="${XDG_DATA_HOME:-$HOME/.local/share}/$NAME"
fi
VENV="$DATA/venv"
if [[ -d "$HOME/bin" ]]; then
    BIN="$HOME/bin"
else
    BIN="$HOME/.local/bin"
fi

# ----------------------------------------------------------------- Python

# Is $1 a Python 3.14 or later, with venv and pip?
good_python() {
    "$1" -c 'import sys, venv, ensurepip; sys.exit(sys.version_info < (3, 14))' >/dev/null 2>&1
}

find_python() {
    local candidate
    for candidate in python3.16 python3.15 python3.14 python3 \
        /opt/homebrew/bin/python3 /usr/local/bin/python3 \
        /Library/Frameworks/Python.framework/Versions/3.1[4-9]/bin/python3; do
        if command -v "$candidate" >/dev/null 2>&1 && good_python "$candidate"; then
            command -v "$candidate"
            return
        fi
    done
    return 1
}

no_python() {
    echo "install.sh: py-pdfocr needs Python 3.14 or later, with venv and pip." >&2
    if [[ "$SYSTEM" == macos ]]; then
        echo "  Install it from https://www.python.org/downloads/macos/ or with Homebrew" >&2
        echo "  (brew install python@3.14), and run this again." >&2
    else
        echo "  Install it with the system's packages (Fedora: sudo dnf install python3;" >&2
        echo "  Debian and Ubuntu: sudo apt install python3.14 python3.14-venv, if the" >&2
        echo "  release has it), or with uv (uv python install 3.14), and run this again," >&2
        echo "  giving it with --python if it isn't on the PATH as python3.14." >&2
    fi
    exit 1
}

# ----------------------------------------------------------------- installing

link_command() {
    local link="$BIN/$NAME"
    mkdir -p -- "$BIN"
    if [[ -L "$link" ]]; then
        if [[ "$(readlink -- "$link")" != "$VENV/bin/$NAME" ]]; then
            echo "  (replacing $link, which pointed to $(readlink -- "$link"))"
        fi
        ln -sfn -- "$VENV/bin/$NAME" "$link"
    elif [[ -e "$link" ]]; then
        echo "  $link exists and is not a link: it was left as it is." >&2
        return
    else
        ln -s -- "$VENV/bin/$NAME" "$link"
    fi
    echo "  the command: $link"
    case ":$PATH:" in
        *":$BIN:"*) ;;
        *) echo "  ($BIN is not on your PATH: add it, or run $VENV/bin/$NAME)" ;;
    esac
}

tesseract_note() {
    if command -v tesseract >/dev/null 2>&1 || [[ -x /opt/homebrew/bin/tesseract ]]; then
        echo "  tesseract: $("$VENV/bin/$NAME" languages | head -n 1)"
        return
    fi
    echo
    echo "Tesseract is not installed, and py-pdfocr needs it to read. Install it, with"
    echo "the languages of your documents:"
    if [[ "$SYSTEM" == macos ]]; then
        echo "  brew install tesseract tesseract-lang"
    else
        echo "  Fedora:            sudo dnf install tesseract tesseract-langpack-spa ..."
        echo "  Debian and Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-spa ..."
    fi
}

install() {
    [[ -f "$ROOT/pyproject.toml" && -d "$ROOT/src/py_pdfocr" ]] \
        || die "run it from the folder of py-pdfocr's source (cloned, or the zip unpacked)"
    local python=$1
    if [[ -z "$python" ]]; then
        python=$(find_python) || no_python
    elif ! good_python "$python"; then
        no_python
    fi
    say "Python: $python ($("$python" -c 'import sys; print(sys.version.split()[0])'))"
    say "Making the environment: $VENV"
    mkdir -p -- "$DATA"
    "$python" -m venv --clear "$VENV"
    say "Installing py-pdfocr and PyMuPDF in it"
    "$VENV/bin/python" -m pip install --quiet --upgrade pip
    # (PyMuPDF alone, without what it brings for its analysis of layouts, onnxruntime, numpy and
    # others, some 200 MB that py-pdfocr never uses)
    "$VENV/bin/python" -m pip install --quiet --no-deps "pymupdf>=1.26" "$ROOT"
    say "Checking that it starts"
    "$VENV/bin/$NAME" --version
    say "Installed:"
    link_command
    tesseract_note
    echo
    echo "Run it with: $NAME file.pdf (see $NAME --help)."
    echo "To update it, run this again after updating the source; to remove it,"
    echo "$0 --uninstall."
}

uninstall() {
    say "Removing py-pdfocr"
    if [[ -L "$BIN/$NAME" && "$(readlink -- "$BIN/$NAME")" == "$VENV/bin/$NAME" ]]; then
        rm -f -- "$BIN/$NAME" && echo "  $BIN/$NAME"
    fi
    if [[ -d "$VENV" ]]; then
        rm -rf -- "$VENV" && echo "  $VENV"
    fi
    # (the models downloaded may be in the same folder: then it stays)
    rmdir -- "$DATA" 2>/dev/null || true
    echo "The settings and the models downloaded were kept; see the README, \"Settings\"."
}

PYTHON=""
ACTION=install
while [[ $# -gt 0 ]]; do
    case "$1" in
        --python) [[ $# -ge 2 ]] || die "--python needs a Python"; PYTHON=$2; shift ;;
        --python=*) PYTHON=${1#--python=} ;;
        --uninstall) ACTION=uninstall ;;
        -h | --help) usage; exit 0 ;;
        *) die "unknown option: $1 (see --help)" ;;
    esac
    shift
done

if [[ "$ACTION" == uninstall ]]; then
    uninstall
else
    install "$PYTHON"
fi
