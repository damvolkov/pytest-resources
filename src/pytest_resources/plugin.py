"""pytest_resources.plugin: the pytest entry point — options, hook wiring, fixture.

Auto-loaded through the ``pytest11`` entry point. It exposes the ``resources``
fixture and the extension seams (``--resources-root``/``resources_root`` ini and the
``pytest_resource_loaders`` / ``pytest_resources_roots`` hooks).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from pytest_resources import hooks
from pytest_resources.index import build_resources
from pytest_resources.loaders import default_loaders

if TYPE_CHECKING:
    from pytest_resources.nodes import Resources


def pytest_addoption(parser: Any) -> None:
    """Register the resources roots as a repeatable CLI option and an ini list."""
    group = parser.getgroup("resources", "lazy typed resource fixtures")
    parser.addini("resources_root", "Directories indexed by the `resources` fixture.", type="linelist")
    group.addoption(
        "--resources-root",
        dest="resources_roots",
        action="append",
        default=None,
        metavar="DIR",
        help="Add a resources root directory (repeatable). CLI wins over the ini list.",
    )


def pytest_configure(config: Any) -> None:
    """Publish the loader- and root-extension hookspecs so conftests may implement them."""
    config.pluginmanager.add_hookspecs(hooks)


##### PRIVATE #####


def _resolve_roots(config: Any) -> list[Path]:
    ### CLI > ini > default; each source is a list, the first non-empty one is the base.
    chosen = config.getoption("resources_roots") or config.getini("resources_root") or []
    if chosen:
        return [Path(entry) for entry in chosen]
    return [config.rootpath / "tests" / "resources"]


############################################################

##### FIXTURES #####


@pytest.fixture(scope="session")
def resources(request: Any) -> Resources:
    """The session's indexed resources tree: default + hook roots, default + hook loaders."""
    config = request.config
    registry = default_loaders()
    config.pluginmanager.hook.pytest_resource_loaders(register=registry.update)
    roots = _resolve_roots(config)
    config.pluginmanager.hook.pytest_resources_roots(roots=roots)
    for root in roots:
        root.mkdir(parents=True, exist_ok=True)
    return build_resources(roots, registry)
