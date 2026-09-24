"""tests/integration: the library used raw, as if it were just another stack dependency.

No plugin, no fixture from pytest_resources — a caller imports the package, builds a
tree over its own sample directory and navigates it. It also pins the open-ended contract:
anything without a bound codec (a spreadsheet, an unknown binary blob) hands back bytes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pytest_resources as pr

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def project_tree(tmp_path: Path) -> Path:
    config = tmp_path / "config"
    config.mkdir()
    (config / "settings.toml").write_text('title = "stack"\n[owner]\nname = "damien"\n')
    data = tmp_path / "data"
    data.mkdir()
    (data / "users.json").write_text('[{"name": "ada"}, {"name": "grace"}]')
    (data / "rows.csv").write_text("name,age\nada,36\n")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "diagram.pdf").write_bytes(b"%PDF-1.7\n\xff\x00not really a pdf\n")
    return tmp_path


def test_public_api_decodes_bound_kinds(project_tree: Path) -> None:
    tree = pr.build_resources(project_tree)
    assert tree.config.settings["title"] == "stack"
    assert tree.config.settings["owner"]["name"] == "damien"
    assert [u["name"] for u in tree.data.users] == ["ada", "grace"]


def test_public_api_falls_back_to_bytes_for_unbound_kinds(project_tree: Path) -> None:
    tree = pr.build_resources(project_tree)
    assert isinstance(tree.data.rows, bytes)  # CSV has no default codec
    assert isinstance(tree.assets.diagram, bytes)  # PDF kind exists but has no bound codec
    assert tree.data.rows.decode().splitlines()[0] == "name,age"  # the caller decodes


def test_default_loader_table_is_open_ended() -> None:
    table = pr.default_loaders()
    assert callable(table[pr.FileType.JSON])
    assert table[pr.FileType.BINARY](b"\x00\x01") == b"\x00\x01"


def test_extraction_toolbox_over_the_fixture(resources: pr.Resources) -> None:
    # recursive: every .json under structured, including nested/deep
    assert {p.name for p in resources.structured.walk("*.json")} == {"sample.json", "sample2.json", "deep.json"}
    # values by kind within a folder
    assert resources.structured.select("*.json")  # decoded dicts
    # paths unlock the raw file for a caller that wants bytes/text, not a decoded value
    assert resources.data.paths("*.csv")[0].read_text().startswith("title,year")
    assert resources.config.paths("*.toml")[0].name == "settings.toml"
    # fuzzy stem lookup
    assert all(isinstance(v, str) for v in resources.unstructured.similar("sample"))
    # random pick is always a real member of the selection
    chosen = resources.structured.choice("*.json")
    assert chosen in resources.structured.select("*.json")


def test_first_and_as_dict_over_the_fixture(resources: pr.Resources) -> None:
    assert resources.structured.first("*.json") == resources.structured.select("*.json")[0]
    nested = resources.structured.as_dict()
    assert {"sample", "sample2", "nested"} <= set(nested)
    assert nested["nested"]["deep"]["id"] == "deep"  # folders recurse into plain dicts


async def test_awalk_streams_over_the_fixture(resources: pr.Resources) -> None:
    seen = [p.name async for p in resources.structured.awalk("*.json")]
    assert set(seen) == {"sample.json", "sample2.json", "deep.json"}
