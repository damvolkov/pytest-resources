"""tests/unit: FileType suffix resolution."""

from pathlib import Path

import pytest

from pytest_resources import FileType


@pytest.mark.parametrize(
    ("suffix", "expected"),
    [
        (".json", FileType.JSON),
        (".JSONC", FileType.JSONC),
        (".yml", FileType.YAML),
        (".cfg", FileType.INI),
        (".jsonl", FileType.NDJSON),
        (".md", FileType.MARKDOWN),
        (".pdf", FileType.PDF),
        (".docx", FileType.DOCX),
        (".xlsx", FileType.XLSX),
        (".jpg", FileType.JPEG),
        (".jpeg", FileType.JPEG),
        (".tif", FileType.TIFF),
        (".tiff", FileType.TIFF),
        (".webp", FileType.WEBP),
        (".eml", FileType.EML),
        (".zip", FileType.ZIP),
    ],
)
def test_filetype_of_known_suffix(suffix: str, expected: FileType) -> None:
    assert FileType.of(suffix) is expected


def test_filetype_of_unknown_suffix_is_binary() -> None:
    assert FileType.of(".xyz") is FileType.BINARY
    assert FileType.of("") is FileType.BINARY


def test_filetype_of_path_reads_extension() -> None:
    assert FileType.of_path(Path("a/b/c.toml")) is FileType.TOML
