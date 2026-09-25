"""pytest_resources.loaders: pluggable decoders, stdlib by default, e-serde opt-in.

The system accepts any canonical ``bytes -> object`` loader. ``default_loaders()``
returns the standard-library table (``json`` + ``tomllib``) — the light, dependency-free
default. [`e-serde`](https://pypi.org/project/e-serde/) is an optional ``[serde]`` extra:
call :func:`eserde_loaders` and register it to swap in the fast, multi-format backend.
Kinds with no parser hand back raw bytes for the caller to decode.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from functools import partial
from tomllib import loads as _toml_loads
from typing import Any

from pytest_resources.errors import ExtraNotInstalledError
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


def default_loaders() -> dict[FileType, Loader]:
    """The default codec table — the standard library only; kinds without one stay bytes."""
    table: dict[FileType, Loader] = dict.fromkeys(FileType, _raw)
    table |= _stdlib_loaders()
    return table


def eserde_loaders() -> dict[FileType, Loader]:
    """The recommended fast table backed by e-serde — needs the optional `[serde]` extra.

    Register it from a ``conftest.py`` to make e-serde the project's official loader::

        from pytest_resources import eserde_loaders


        def pytest_resource_loaders(register):
            register(eserde_loaders())
    """
    try:
        from eserde import Format, loads  # noqa: PLC0415 -- optional fast path, not a core dep
    except ImportError as exc:
        msg = (
            "`eserde_loaders()` requires the 'serde' extra.\n"
            'Install it with:  uv add --group test "pytest-resources[serde]"\n'
            "Underlying import failed: eserde"
        )
        raise ExtraNotInstalledError(msg) from exc
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
