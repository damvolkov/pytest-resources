"""tests/unit: the pluggable loader table and its e-serde / stdlib backends."""

import json
import sys

import pytest

from pytest_resources import FileType
from pytest_resources.loaders import _lines, _raw, _text, default_loaders


def test_default_loaders_covers_every_kind() -> None:
    assert set(default_loaders()) == set(FileType)


def test_json_kind_decodes_to_native_dict() -> None:
    assert default_loaders()[FileType.JSON](b'{"a": 1, "b": [1, 2]}') == {"a": 1, "b": [1, 2]}


def test_text_and_markdown_decode_to_str() -> None:
    table = default_loaders()
    assert table[FileType.TEXT](b"hi") == "hi"
    assert isinstance(table[FileType.MARKDOWN](b"# t\n"), str)


def test_unbound_kind_hands_back_raw_bytes() -> None:
    assert default_loaders()[FileType.CSV](b"a,b") == b"a,b"
    assert _raw(b"x") == b"x"


def test_lines_splits_and_decodes_per_line() -> None:
    assert _lines(json.loads, b'{"i": 1}\n\n{"i": 2}\n') == [{"i": 1}, {"i": 2}]


def test_text_helper_decodes_utf8() -> None:
    assert _text("café".encode()) == "café"


def test_stdlib_fallback_when_eserde_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "eserde", None)  # forces ImportError inside default_loaders
    table = default_loaders()
    assert table[FileType.JSON](b'{"a": 1}') == {"a": 1}
    assert table[FileType.TOML](b"a = 1\n") == {"a": 1}
    assert table[FileType.NDJSON](b'{"i": 1}\n{"i": 2}') == [{"i": 1}, {"i": 2}]
    assert table[FileType.INI](b"[s]\nk=v") == b"[s]\nk=v"  # not a stdlib codec -> bytes


@pytest.mark.parametrize(
    ("fmt", "blob", "want"),
    [
        (FileType.JSONC, b'{"a": 1 /* c */}', {"a": 1}),
        (FileType.INI, b"[s]\nk = v\n", {"s": {"k": "v"}}),
        (FileType.TOML, b"a = 1\n", {"a": 1}),
        (FileType.YAML, b"a: 1\n", {"a": 1}),
    ],
)
def test_eserde_native_config_kinds(fmt: FileType, blob: bytes, want: dict) -> None:
    pytest.importorskip("eserde")
    assert default_loaders()[fmt](blob) == want
