"""pytest_resources.formats: canonical file kinds and suffix resolution."""

from __future__ import annotations

from enum import StrEnum, auto
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path
    from typing import Final


class FileType(StrEnum):
    """The kinds the loader system recognises; any other suffix resolves to ``BINARY``."""

    JSON = auto()
    JSONC = auto()
    NDJSON = auto()
    YAML = auto()
    TOML = auto()
    INI = auto()
    CSV = auto()
    TSV = auto()
    MARKDOWN = auto()
    TEXT = auto()
    HTML = auto()
    XML = auto()
    PYTHON = auto()
    BINARY = auto()

    @classmethod
    def of(cls, suffix: str) -> FileType:
        """Kind resolved from a file suffix through the frozen table; unknown is ``BINARY``."""
        return _SUFFIXES.get(suffix.casefold(), FileType.BINARY)

    @classmethod
    def of_path(cls, path: Path) -> FileType:
        """Kind resolved from a path's extension."""
        return cls.of(path.suffix)


_SUFFIXES: Final[Mapping[str, FileType]] = MappingProxyType(
    {
        ".json": FileType.JSON,
        ".jsonc": FileType.JSONC,
        ".jsonl": FileType.NDJSON,
        ".ndjson": FileType.NDJSON,
        ".yaml": FileType.YAML,
        ".yml": FileType.YAML,
        ".toml": FileType.TOML,
        ".ini": FileType.INI,
        ".cfg": FileType.INI,
        ".conf": FileType.INI,
        ".csv": FileType.CSV,
        ".tsv": FileType.TSV,
        ".md": FileType.MARKDOWN,
        ".markdown": FileType.MARKDOWN,
        ".txt": FileType.TEXT,
        ".rst": FileType.TEXT,
        ".html": FileType.HTML,
        ".htm": FileType.HTML,
        ".xml": FileType.XML,
        ".py": FileType.PYTHON,
    }
)
