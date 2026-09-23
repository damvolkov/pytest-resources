"""pytest_resources.nodes: the lazy, attribute-navigable tree over indexed files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pytest_resources.errors import EntryNotFoundError
from pytest_resources.formats import FileType
from pytest_resources.loaders import _raw

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from typing import Any

    from pytest_resources.loaders import Loader

_MISSING = object()


class _Context:
    """Loader registry and decode cache shared by every node of one indexed tree."""

    __slots__ = ("_cache", "_registry")

    def __init__(self, registry: Mapping[FileType, Loader]) -> None:
        self._registry = registry
        self._cache: dict[Path, Any] = {}

    def load(self, path: Path) -> Any:
        cached = self._cache.get(path, _MISSING)
        return cached if cached is not _MISSING else self._decode(path)

    def _decode(self, path: Path) -> Any:
        ### The FileType decides the codec; an unbound kind hands back raw bytes.
        loaded = self._registry.get(FileType.of_path(path), _raw)(path.read_bytes())
        self._cache[path] = loaded
        return loaded


class ResourceNode:
    """A lazily resolved directory: attribute, item and iteration views agree."""

    __slots__ = ("_context", "_entries", "_path")

    def __init__(self, path: Path, entries: dict[str, object], context: _Context) -> None:
        self._path = path
        self._entries = entries
        self._context = context

    ##### PRIVATE #####

    def _value(self, entry: object) -> Any:
        match entry:
            case Path() as file:
                return self._context.load(file)
            case _:
                return entry

    ############################################################

    ##### PUBLIC #####

    @property
    def path(self) -> Path:
        """Absolute path this node indexes."""
        return self._path

    def keys(self) -> list[str]:
        """Every entry name, files and directories alike."""
        return list(self._entries)

    def values(self) -> list[Any]:
        """Every file entry parsed; directories stay out of the value stream."""
        return [self._context.load(entry) for entry in self._entries.values() if isinstance(entry, Path)]

    def items(self) -> list[tuple[str, Any]]:
        """``(name, resolved)`` pairs: files parsed, directories as nodes."""
        return [(name, self._value(entry)) for name, entry in self._entries.items()]

    def __getattr__(self, name: str) -> Any:
        entry = self._entries.get(name, _MISSING)
        if entry is _MISSING:
            msg = f"{self._path.name!r} has no entry {name!r}"
            raise EntryNotFoundError(msg)
        return self._value(entry)

    def __getitem__(self, name: str) -> Any:
        entry = self._entries.get(name, _MISSING)
        if entry is _MISSING:
            msg = f"{self._path.name!r} has no entry {name!r}"
            raise KeyError(msg)
        return self._value(entry)

    def __iter__(self) -> Iterator[Any]:
        return (self._context.load(entry) for entry in self._entries.values() if isinstance(entry, Path))

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, name: object) -> bool:
        return name in self._entries

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._path.name!r}, entries={len(self._entries)})"


class Resources(ResourceNode):
    """Root of an indexed resources tree — the object the ``resources`` fixture yields."""

    __slots__ = ()
