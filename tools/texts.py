"""The texts of the interface in the code (those given to tr, ntr and N_), for locale/es.xml and its test."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "src" / "py_pdfocr"


def texts() -> set[str]:
    found = set()
    for path in SOURCE.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("tr", "ntr", "N_"):
                count = 2 if node.func.id == "ntr" else 1
                for arg in node.args[:count]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        found.add(" ".join(arg.value.split()))
    return found


if __name__ == "__main__":
    for text in sorted(texts()):
        print(text)
