"""The configuration file.

It is a small TOML file, ``config.toml``, in the user's configuration folder:

* Linux: ``$XDG_CONFIG_HOME/py-pdfocr`` (usually ``~/.config/py-pdfocr``);
* macOS: ``~/Library/Application Support/py-pdfocr``;
* Windows: ``%APPDATA%\\py-pdfocr``.

``$PY_PDFOCR_CONFIG`` names another folder. It holds the language of the
interface and the languages of the text read by default:

    [parameters]
    interface = "es"
    languages = "lat+spa"
"""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

ENV = "PY_PDFOCR_CONFIG"
SETTINGS = {"interface": "en", "languages": "eng"}  # name: default


class ConfigError(Exception):
    """A configuration file that cannot be read."""


def config_dir() -> Path:
    # La variable de entorno manda: así los tests, o quien quiera una configuración aparte, no tocan la del usuario.
    if os.environ.get(ENV):
        return Path(os.environ[ENV])
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "py-pdfocr"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "py-pdfocr"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "py-pdfocr"


def config_path() -> Path:
    return config_dir() / "config.toml"


def read() -> dict[str, dict]:
    """The configuration ({} if there is no file; raises ConfigError if it is wrong)."""
    path = config_path()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as e:
        raise ConfigError(f"{path}: {e}") from None
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: {e}") from None
    return data if isinstance(data, dict) else {}


def get(name: str):
    """The setting NAME (its default if the file does not have it, or cannot be read)."""
    try:
        value = read().get("parameters", {}).get(name)
    except ConfigError:
        value = None
    return SETTINGS[name] if value is None else value


def set(name: str, value) -> Path:
    """Change one setting, keeping the others (None removes it). Returns the file's path."""
    return set_many({name: value})


def set_many(values: dict) -> Path:
    """Change several settings at once, keeping the others (a value None removes its setting). Returns the
    file's path."""
    from .interface import tr

    # Un archivo dañado se escribe de nuevo, desde cero, con los valores nuevos.
    try:
        data = read()
    except ConfigError:
        data = {}
    params = dict(data.get("parameters", {}))
    for name, value in values.items():
        if value is None:
            params.pop(name, None)
        else:
            params[name] = value
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# " + tr("The settings of py-pdfocr. Delete this file to use the usual values."), "",
             "[parameters]"]
    # Only strings are kept here (the language of the interface, those of the text).
    for key, val in params.items():
        lines.append(f'{key} = "' + str(val).replace("\\", "\\\\").replace('"', '\\"') + '"')
    # Un archivo temporal renombrado al final: un fallo nunca deja media configuración.
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path
