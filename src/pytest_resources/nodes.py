"""pytest_resources.nodes: the lazy, attribute-navigable tree over indexed files."""

from __future__ import annotations

import difflib
import fnmatch
import random
import re
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_resources.errors import EntryNotFoundError, ResourceError
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

    def _absent(self, name: str) -> str:
        ### One message for both miss paths; difflib nudges the nearest name, if any.
        hint = difflib.get_close_matches(name, self._entries, n=1)
        return f"{self._path.name!r} has no entry {name!r}" + (f" — did you mean {hint[0]!r}?" if hint else "")

    def _select_paths(self, patterns: tuple[str | re.Pattern[str], ...], kind: FileType | None) -> list[Path]:
        ### A string pattern is a glob over the file name; a compiled one is regex-searched.
        matchers = tuple(m if isinstance(m, re.Pattern) else re.compile(fnmatch.translate(m)) for m in patterns)
        return [
            file
            for file in self._entries.values()
            if isinstance(file, Path)
            and (kind is None or FileType.of_path(file) is kind)
            and (not matchers or any(matcher.search(file.name) for matcher in matchers))
        ]

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
        return self.select()

    def items(self) -> list[tuple[str, Any]]:
        """``(name, resolved)`` pairs: files parsed, directories as nodes."""
        return [(name, self._value(entry)) for name, entry in self._entries.items()]

    def select(self, *patterns: str | re.Pattern[str], kind: FileType | None = None) -> list[Any]:
        """Decoded values of files in this folder, narrowed by glob/regex and optional kind."""
        return [self._context.load(file) for file in self._select_paths(patterns, kind)]

    def choice(
        self,
        *patterns: str | re.Pattern[str],
        kind: FileType | None = None,
        rng: random.Random | None = None,
    ) -> Any:
        """One random file value from the selection (default RNG honours the session seed)."""
        candidates = self.select(*patterns, kind=kind)
        if not candidates:
            msg = f"{self._path.name!r} has no file to choose from"
            raise ResourceError(msg)
        return (rng or random).choice(candidates)

    def __getattr__(self, name: str) -> Any:
        entry = self._entries.get(name, _MISSING)
        if entry is _MISSING:
            raise EntryNotFoundError(self._absent(name))
        return self._value(entry)

    def __getitem__(self, name: str) -> Any:
        entry = self._entries.get(name, _MISSING)
        if entry is _MISSING:
            raise KeyError(self._absent(name))
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
