"""tests/unit: the loader tables — the stdlib default and the opt-in e-serde table."""

import json
import sys

import pytest

from pytest_resources import FileType
from pytest_resources.errors import ExtraNotInstalledError
from pytest_resources.loaders import _lines, _raw, _text, default_loaders, eserde_loaders


def test_default_loaders_covers_every_kind() -> None:
    assert set(default_loaders()) == set(FileType)


def test_default_loaders_is_stdlib() -> None:
    table = default_loaders()
    assert table[FileType.JSON](b'{"a": 1, "b": [1, 2]}') == {"a": 1, "b": [1, 2]}
    assert table[FileType.TOML](b"a = 1\n") == {"a": 1}
    assert table[FileType.NDJSON](b'{"i": 1}\n\n{"i": 2}') == [{"i": 1}, {"i": 2}]
    assert table[FileType.MARKDOWN](b"# t\n") == "# t\n"


@pytest.mark.parametrize("fmt", [FileType.CSV, FileType.YAML, FileType.INI, FileType.JSONC, FileType.HTML])
def test_default_loaders_leaves_the_rest_as_bytes(fmt: FileType) -> None:
    assert default_loaders()[fmt](b"raw") == b"raw"  # no stdlib codec -> honest bytes


def test_default_loaders_does_not_pick_eserde() -> None:
    pytest.importorskip("eserde")  # e-serde is optional: the default must ignore it, even when installed
    assert default_loaders()[FileType.JSONC](b'{"a": 1}') == b'{"a": 1}'


@pytest.mark.parametrize(
    ("fmt", "blob", "want"),
    [
        (FileType.JSON, b'{"a": 1}', {"a": 1}),
        (FileType.JSONC, b'{"a": 1 /* c */}', {"a": 1}),
        (FileType.INI, b"[s]\nk = v\n", {"s": {"k": "v"}}),
        (FileType.TOML, b"a = 1\n", {"a": 1}),
        (FileType.YAML, b"a: 1\n", {"a": 1}),
    ],
)
def test_eserde_loaders_decodes_config_kinds(fmt: FileType, blob: bytes, want: dict) -> None:
    pytest.importorskip("eserde")
    assert eserde_loaders()[fmt](blob) == want


def test_eserde_loaders_requires_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "eserde", None)  # forces the ImportError path
    with pytest.raises(ExtraNotInstalledError) as exc:
        eserde_loaders()
    assert "pytest-resources[serde]" in str(exc.value)
    assert "uv add" in str(exc.value)


def test_eserde_loaders_is_importable_without_calling_it() -> None:
    assert callable(eserde_loaders)  # importing loaders must not import e-serde eagerly


def test_lines_splits_and_decodes_per_line() -> None:
    assert _lines(json.loads, b'{"i": 1}\n\n{"i": 2}\n') == [{"i": 1}, {"i": 2}]


def test_text_and_raw_helpers() -> None:
    assert _text("café".encode()) == "café"
    assert _raw(b"x") == b"x"
