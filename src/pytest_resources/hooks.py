"""pytest_resources.hooks: the extension seams for loaders and resource roots.

A project implements these in its own ``conftest.py`` to add or override the default
codec table, or to contribute extra resource directories, without touching the plugin.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

import pytest

from pytest_resources.formats import FileType
from pytest_resources.loaders import Loader

if TYPE_CHECKING:
    from pathlib import Path

Register = Callable[[Mapping[FileType, Loader]], None]


@pytest.hookspec
def pytest_resource_loaders(register: Register) -> None:
    """Bind or override resource loaders declaratively.

    ``register`` merges a ``{FileType: bytes -> object}`` mapping into the session's
    codec table, so an existing kind can be swapped and an unknown one introduced::

        def pytest_resource_loaders(register):
            register({FileType.CSV: my_csv_rows, FileType.YAML: ruamel_round_trip})
    """


@pytest.hookspec
def pytest_resources_roots(roots: list[Path]) -> None:
    """Contribute extra resource root directories to the indexed tree.

    ``roots`` is the resolved base list (CLI / ini / default); implementations append to
    it, and appended roots win over earlier ones on a top-level key clash::

        def pytest_resources_roots(roots):
            roots.append(Path("tests/fixtures/shared"))
    """
