"""tests/unit: the auto-loaded `resources` fixture and root resolution."""

from pathlib import Path

import pytest_resources as pr
from pytest_resources import Resources, hooks, plugin
from pytest_resources.plugin import _resolve_roots


class _Cfg:
    rootpath = Path("/repo")

    def __init__(self, option: list[str] | None, ini: list[str] | None) -> None:
        self._option = option
        self._ini = ini

    def getoption(self, name: str) -> list[str] | None:
        return self._option

    def getini(self, name: str) -> list[str] | None:
        return self._ini


def test_resolve_roots_cli_wins() -> None:
    assert _resolve_roots(_Cfg(["/cli"], ["/ini"])) == [Path("/cli")]


def test_resolve_roots_ini_then_default() -> None:
    assert _resolve_roots(_Cfg(None, ["/ini"])) == [Path("/ini")]
    assert _resolve_roots(_Cfg(None, None)) == [Path("/repo/tests/resources")]
    assert _resolve_roots(_Cfg([], [])) == [Path("/repo/tests/resources")]


def test_resources_fixture_is_indexed_tree(resources: Resources) -> None:
    assert isinstance(resources, pr.Resources)
    assert resources.structured.sample["id"] == "sample1"
    assert resources.config.settings["owner"]["name"] == "damien"
    assert isinstance(resources.config.manifest, bytes)  # JSONC has no stdlib codec -> bytes by default
    assert isinstance(resources.unstructured.sample, str)


def test_resources_fixture_bytes_for_unregistered_kind(resources: Resources) -> None:
    assert isinstance(resources.data.movies, bytes)


def test_resources_fixture_synthesizes_on_the_fly(resources: Resources) -> None:
    assert isinstance(resources.make(int), int)
    assert len(resources.batch(str, 3)) == 3
    path = resources.file("txt", name="synth_smoke")
    assert path.exists()
    assert isinstance(resources.synth_smoke, str)


##### PLUGIN HOOKS (driven directly so they are measured, not only at startup) #####


class _Group:
    def __init__(self) -> None:
        self.options: list[tuple[tuple, dict]] = []

    def addoption(self, *args, **kwargs) -> None:
        self.options.append((args, kwargs))


class _Parser:
    def __init__(self) -> None:
        self.groups: dict[str, _Group] = {}
        self.inis: list[tuple[tuple, dict]] = []

    def getgroup(self, name: str, *args) -> _Group:
        return self.groups.setdefault(name, _Group())

    def addini(self, *args, **kwargs) -> None:
        self.inis.append((args, kwargs))


def test_addoption_registers_cli_and_ini() -> None:
    parser = _Parser()
    plugin.pytest_addoption(parser)
    cli = parser.groups["resources"].options
    assert any(k.get("dest") == "resources_roots" and k.get("action") == "append" for _a, k in cli)
    inis = {args[0]: kwargs for args, kwargs in parser.inis}
    assert inis["resources_root"].get("type") == "linelist"


class _PM:
    def __init__(self) -> None:
        self.spec = None

    def add_hookspecs(self, module) -> None:
        self.spec = module


class _Config:
    def __init__(self) -> None:
        self.pluginmanager = _PM()


def test_configure_publishes_hookspec_module() -> None:
    config = _Config()
    plugin.pytest_configure(config)
    assert config.pluginmanager.spec is hooks


def test_hookspec_is_callable_and_harmonizes() -> None:
    assert hooks.pytest_resource_loaders(lambda mapping: None) is None
