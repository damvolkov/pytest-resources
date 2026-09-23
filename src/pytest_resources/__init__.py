"""pytest-resources — lazy, typed, attribute-navigable resource fixtures for pytest.

One façade over the package. The pytest plugin (`resources` fixture, options and
hooks) lives in :mod:`pytest_resources.plugin` and auto-loads via the ``pytest11``
entry point; this module is the import-time surface for programmatic use.

    import pytest_resources as pr
    resources = pr.build_resources(Path("tests/resources"))
    sample = resources.structured.sample          # decoded per its FileType, cached
"""

from importlib.metadata import PackageNotFoundError, version

from pytest_resources.errors import EntryNotFoundError, ResourceError
from pytest_resources.formats import FileType
from pytest_resources.index import abuild_resources, build_resources
from pytest_resources.loaders import Loader, default_loaders
from pytest_resources.nodes import ResourceNode, Resources

try:
    __version__: str = version("pytest-resources")
except PackageNotFoundError:  # source tree, not installed
    __version__ = "0.0.0+dev"

__all__ = [
    "EntryNotFoundError",
    "FileType",
    "Loader",
    "ResourceError",
    "ResourceNode",
    "Resources",
    "__version__",
    "abuild_resources",
    "build_resources",
    "default_loaders",
]
