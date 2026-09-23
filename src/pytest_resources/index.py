"""pytest_resources.index: recursive directory indexing without reading contents."""

from __future__ import annotations

import asyncio
import re
from operator import attrgetter
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_resources.errors import ResourceError
from pytest_resources.loaders import default_loaders
from pytest_resources.nodes import ResourceNode, Resources, _Context

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from pytest_resources.formats import FileType
    from pytest_resources.loaders import Loader

##### PRIVATE #####


def _key(name: str) -> str:
    """Identifier-safe attribute name from a file stem or a directory name."""
    return re.sub(r"\W|^(?=\d)", "_", Path(name).stem)


def _visible(name: str) -> bool:
    return not name.startswith(".") and name != "__pycache__"


def _children(path: Path, context: _Context) -> dict[str, object]:
    entries = sorted(path.iterdir(), key=attrgetter("name"))
    return {
        _key(entry.name): (_node(entry, context) if entry.is_dir() else entry)
        for entry in entries
        if _visible(entry.name)
    }


def _node(path: Path, context: _Context) -> ResourceNode:
    return ResourceNode(path, _children(path, context), context)


def _context(registry: Mapping[FileType, Loader] | None) -> _Context:
    ### A None registry means the best default table; a mapping is copied, never shared.
    return _Context(default_loaders() if registry is None else dict(registry))


def _roots(root: Path | Iterable[Path]) -> tuple[Path, ...]:
    ### One root or many: a lone Path and a sequence of them share the same code path.
    match root:
        case Path() as single:
            return (single,)
        case _:
            return tuple(root)


def _merge(paths: tuple[Path, ...], context: _Context) -> dict[str, object]:
    ### Flat top-level merge across roots; a later root overrides an earlier key.
    merged: dict[str, object] = {}
    for path in paths:
        merged |= _children(path, context)
    return merged


def _ensure_dir(root: Path) -> Path:
    if not root.is_dir():
        msg = f"resources root is not a directory: {root}"
        raise ResourceError(msg)
    return root


############################################################

##### PUBLIC #####


def build_resources(root: Path | Iterable[Path], registry: Mapping[FileType, Loader] | None = None) -> Resources:
    """Index ``root`` (one path or several) recursively — read on access, later roots win."""
    paths = tuple(map(_ensure_dir, _roots(root)))
    context = _context(registry)
    return Resources(paths[0], _merge(paths, context), context)


async def abuild_resources(root: Path | Iterable[Path], registry: Mapping[FileType, Loader] | None = None) -> Resources:
    """Same index, walked off the event loop for large trees."""
    paths = tuple(map(_ensure_dir, _roots(root)))
    context = _context(registry)
    children = await asyncio.to_thread(_merge, paths, context)
    return Resources(paths[0], children, context)
