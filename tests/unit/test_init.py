"""tests/unit: the package façade and its not-installed version fallback."""

from __future__ import annotations

import importlib
import importlib.metadata
from typing import TYPE_CHECKING, Never

import pytest_resources as pr

if TYPE_CHECKING:
    import pytest


def test_version_falls_back_when_package_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> Never:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    importlib.reload(pr)
    assert pr.__version__ == "0.0.0+dev"

    monkeypatch.undo()
    importlib.reload(pr)
    assert pr.__version__ != "0.0.0+dev"
