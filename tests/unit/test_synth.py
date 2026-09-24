"""tests/unit: the vendor seam — availability probes, the exact-missing-extra error and the file-kind tables."""

from __future__ import annotations

import random
from importlib.util import find_spec
from typing import cast

import pytest

from pytest_resources import ExtraNotInstalledError, FileType, ResourceError
from pytest_resources import synth as synth_module
from pytest_resources.synth import _FILES, SynthProvider


def _without(monkeypatch: pytest.MonkeyPatch, *absent: str) -> None:
    def probe(name: str, package: str | None = None) -> object:
        return None if name in absent else find_spec(name, package)

    monkeypatch.setattr(synth_module, "find_spec", probe)


def test_synth_make_without_objects_explains_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    _without(monkeypatch, "polyfactory")
    provider = SynthProvider()
    with pytest.raises(ExtraNotInstalledError) as excinfo:
        provider.make(int)
    msg = str(excinfo.value)
    assert "pytest-resources[objects]" in msg
    assert "uv add" in msg
    assert "polyfactory" in msg
    assert "make" in msg


def test_synth_file_without_files_explains_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    _without(monkeypatch, "faker_file")
    provider = SynthProvider()
    with pytest.raises(ExtraNotInstalledError) as excinfo:
        provider.file(FileType.PDF)
    msg = str(excinfo.value)
    assert "pytest-resources[files]" in msg
    assert "pip install" in msg
    assert "faker-file" in msg
    assert "file" in msg


def test_synth_probe_blinds_only_the_absent_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    _without(monkeypatch, "polyfactory")
    provider = SynthProvider()
    with pytest.raises(ExtraNotInstalledError):
        provider.make(int)
    path = provider.file(FileType.TEXT)
    assert path.exists()
    assert path.stat().st_size > 0


def test_synth_batch_without_objects_explains_the_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    _without(monkeypatch, "polyfactory")
    provider = SynthProvider()
    with pytest.raises(ExtraNotInstalledError) as excinfo:
        provider.batch(int, 3)
    assert "batch" in str(excinfo.value)
    assert "pytest-resources[objects]" in str(excinfo.value)


def test_synth_extra_error_stays_a_resource_failure() -> None:
    assert issubclass(ExtraNotInstalledError, ResourceError)
    assert issubclass(ExtraNotInstalledError, ImportError)


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (FileType.PDF, FileType.PDF),
        ("pdf", FileType.PDF),
        ("PDF", FileType.PDF),
        (".pdf", FileType.PDF),
        ("a.pdf", FileType.PDF),
        ("a.PDF", FileType.PDF),
        ("note.txt", FileType.TEXT),
        ("txt", FileType.TEXT),
        ("text", FileType.TEXT),
        ("report.docx", FileType.DOCX),
        ("settings.json", FileType.JSON),
        ("zip", FileType.ZIP),
    ],
    ids=repr,
)
def test_file_of_resolves_every_spelling(kind: FileType | str, expected: FileType) -> None:
    assert SynthProvider._file_of(kind) is expected


@pytest.mark.parametrize("kind", ["qqq", "a.xyz", "a.svg", "a.bin", 42, None])
def test_file_of_rejects_the_unknown(kind: object) -> None:
    with pytest.raises(ResourceError):
        SynthProvider._file_of(cast("FileType | str", kind))


def test_recipes_map_only_known_kinds() -> None:
    assert set(_FILES) <= set(FileType)
    assert _FILES[FileType.PDF].generator_kwarg == "pdf_generator_cls"
    assert {FileType.MARKDOWN, FileType.TOML, FileType.YAML}.isdisjoint(_FILES)


def test_recipe_binds_pillow_only_where_wkhtml_would_be_required() -> None:
    pil_kinds = {
        FileType.PNG,
        FileType.JPEG,
        FileType.GIF,
        FileType.BMP,
        FileType.ICO,
        FileType.TIFF,
        FileType.WEBP,
        FileType.PDF,
    }
    for kind, recipe in _FILES.items():
        assert (recipe.generator is not None) is (kind in pil_kinds)


def test_recipeless_kind_raises_with_the_supported_list() -> None:
    with pytest.raises(ResourceError) as excinfo:
        SynthProvider._file_recipe(FileType.TOML)
    assert "'toml'" in str(excinfo.value)


def test_seed_explicit_wins_and_default_follows_the_global_rng() -> None:
    provider = SynthProvider()
    assert provider._common_seed(7) == 7
    random.seed(1)
    first = provider._common_seed(None)
    random.seed(1)
    assert provider._common_seed(None) == first
    assert provider._common_seed(None) != first
