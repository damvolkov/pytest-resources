"""pytest_resources.loaders: pluggable decoders, e-serde preferred, stdlib fallback.

The system accepts any canonical ``bytes -> object`` loader. ``default_loaders``
returns the best table available: e-serde's unified native codecs when installed,
otherwise the standard library (json + tomllib). Kinds with no parser hand back raw
bytes for the caller to decode.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from functools import partial
from tomllib import loads as _toml_loads
from typing import Any

from pytest_resources.formats import FileType

Loader = Callable[[bytes], Any]


def _raw(data: bytes) -> bytes:
    """Passthrough for kinds with no parser bound."""
    return data


def _text(data: bytes) -> str:
    """UTF-8 decode for textual kinds."""
    return data.decode()


def _toml(data: bytes) -> dict[str, Any]:
    """TOML decode through the standard-library reader."""
    return _toml_loads(data.decode())


def _lines(loader: Loader, data: bytes) -> list[Any]:
    """Split into non-empty lines and decode each with `loader`."""
    return [loader(line) for line in data.splitlines() if line.strip()]


def _eserde_loaders() -> dict[FileType, Loader]:
    """Config-codec table backed by e-serde (native Rust/C decoders, native dicts out)."""
    from eserde import Format, loads  # noqa: PLC0415 -- optional fast path, not a core dep

    json_row = partial(loads, format=Format.JSON)
    return {
        FileType.JSON: json_row,
        FileType.JSONC: partial(loads, format=Format.JSONC),
        FileType.YAML: partial(loads, format=Format.YAML),
        FileType.TOML: partial(loads, format=Format.TOML),
        FileType.INI: partial(loads, format=Format.INI),
        FileType.NDJSON: partial(_lines, json_row),
        FileType.MARKDOWN: _text,
        FileType.TEXT: _text,
    }


def _stdlib_loaders() -> dict[FileType, Loader]:
    """Config-codec table from the standard library alone (json + tomllib)."""
    return {
        FileType.JSON: json.loads,
        FileType.TOML: _toml,
        FileType.NDJSON: partial(_lines, json.loads),
        FileType.MARKDOWN: _text,
        FileType.TEXT: _text,
    }


def default_loaders() -> dict[FileType, Loader]:
    """A fresh codec table: e-serde when importable, else the stdlib; other kinds stay bytes."""
    table: dict[FileType, Loader] = dict.fromkeys(FileType, _raw)
    try:
        table |= _eserde_loaders()
    except ImportError:
        table |= _stdlib_loaders()
    return table
