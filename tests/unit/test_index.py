"""tests/unit: recursive indexing, lazy caching and the attribute/dict/iter views."""

from __future__ import annotations

import json
import random
import re
from typing import TYPE_CHECKING

import pytest

import pytest_resources as pr
from pytest_resources import (
    EntryNotFoundError,
    FileType,
    ResourceError,
    Resources,
    abuild_resources,
    build_resources,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def tree_root(tmp_path: Path) -> Path:
    structured = tmp_path / "structured"
    structured.mkdir()
    (structured / "sample.json").write_text(json.dumps({"id": "sample1", "n": 1}))
    (structured / "weird-name.json").write_text(json.dumps({"id": "weird"}))
    (structured / ".hidden.json").write_text("{}")
    (structured / "__pycache__").mkdir()
    (structured / "__pycache__" / "junk.json").write_text("{}")
    (structured / "deep").mkdir()
    (structured / "deep" / "leaf.json").write_text(json.dumps({"id": "deep"}))
    (tmp_path / "binary").mkdir()
    (tmp_path / "binary" / "raw.bin").write_bytes(b"\x00\x01")
    return tmp_path


def test_index_builds_resources_root(tree_root: Path) -> None:
    assert isinstance(build_resources(tree_root), Resources)


def test_navigation_reads_files_lazily(tree_root: Path) -> None:
    tree = build_resources(tree_root)
    assert tree.structured.sample["id"] == "sample1"
    assert tree["structured"]["weird_name"]["id"] == "weird"
    assert tree.structured.deep.leaf["id"] == "deep"


def test_hidden_and_pycache_are_skipped(tree_root: Path) -> None:
    keys = build_resources(tree_root).structured.keys()
    assert "hidden" not in keys
    assert "__pycache__" not in keys


def test_iterates_only_file_values(tree_root: Path) -> None:
    values = list(build_resources(tree_root).structured)
    assert [v["id"] for v in values] == ["sample1", "weird"]


def test_values_returns_only_file_values(tree_root: Path) -> None:
    values = build_resources(tree_root).structured.values()
    assert [v["id"] for v in values] == ["sample1", "weird"]  # the `deep` directory stays out


def test_select_by_glob_and_regex(tree_root: Path) -> None:
    structured = build_resources(tree_root).structured
    assert {v["id"] for v in structured.select("*.json")} == {"sample1", "weird"}
    assert [v["id"] for v in structured.select("weird-name*")] == ["weird"]  # glob over the file name
    assert [v["id"] for v in structured.select(re.compile(r"^sam"))] == ["sample1"]  # regex search


def test_select_by_kind_and_empty(tree_root: Path) -> None:
    tree = build_resources(tree_root)
    assert len(tree.structured.select(kind=FileType.JSON)) == 2
    assert tree.structured.select("*.toml") == []  # nothing in this folder
    assert isinstance(tree.binary.select(kind=FileType.BINARY)[0], bytes)


def test_choice_is_random_but_bounded(tree_root: Path) -> None:
    structured = build_resources(tree_root).structured
    assert structured.choice(kind=FileType.JSON, rng=random.Random(1234))["id"] in {"sample1", "weird"}
    subset = random.Random(0).sample(structured.select("*.json"), 2)  # random-k, no reserved name
    assert {v["id"] for v in subset} == {"sample1", "weird"}


def test_choice_rejects_empty_selection(tree_root: Path) -> None:
    with pytest.raises(ResourceError):
        build_resources(tree_root).structured.choice("*.toml")


def test_paths_and_walk_return_file_paths(tree_root: Path) -> None:
    tree = build_resources(tree_root)
    structured = tree.structured
    assert {p.name for p in structured.paths("*.json")} == {"sample.json", "weird-name.json"}
    assert all(p.is_file() for p in structured.paths())
    assert structured.paths("*.bin", kind=FileType.BINARY) == []  # no .bin in this folder
    assert tree.binary.paths("raw.bin")[0].read_bytes() == b"\x00\x01"  # paths unlock raw bytes


def test_walk_is_recursive_and_filtered(tree_root: Path) -> None:
    tree = build_resources(tree_root)
    assert {p.name for p in tree.walk()} == {"sample.json", "weird-name.json", "leaf.json", "raw.bin"}
    assert {p.name for p in tree.walk("*.json")} == {"sample.json", "weird-name.json", "leaf.json"}
    assert list(tree.walk(kind=FileType.BINARY)) == [tree_root / "binary" / "raw.bin"]


def test_similar_matches_lexically_close_stems(tree_root: Path) -> None:
    structured = build_resources(tree_root).structured
    assert [v["id"] for v in structured.similar("sampel")] == ["sample1"]  # fuzzy of 'sample'
    assert structured.similar("weirdname")[0]["id"] == "weird"  # hyphen-insensitive-ish
    assert structured.similar("qqqq") == []  # nothing remotely close


def test_first_is_deterministic_and_raises_when_empty(tree_root: Path) -> None:
    structured = build_resources(tree_root).structured
    assert structured.first("*.json")["id"] == "sample1"  # name order, not random
    with pytest.raises(ResourceError):
        structured.first("*.toml")


def test_as_dict_exposes_nested_plain_dict(tree_root: Path) -> None:
    nested = build_resources(tree_root).as_dict()
    assert set(nested) == {"binary", "structured"}
    assert nested["structured"]["deep"]["leaf"]["id"] == "deep"  # folders recurse
    assert isinstance(nested["binary"]["raw"], bytes)  # unbound kind -> raw bytes


async def test_awalk_matches_walk(tree_root: Path) -> None:
    tree = build_resources(tree_root)
    synced = {p.name for p in tree.walk("*.json")}
    asynced = {p.name async for p in tree.awalk("*.json")}
    assert asynced == synced == {"sample.json", "weird-name.json", "leaf.json"}
    assert [p.name async for p in tree.awalk(kind=FileType.BINARY)] == ["raw.bin"]


def test_missing_entry_suggests_close_name(tree_root: Path) -> None:
    structured = build_resources(tree_root).structured
    with pytest.raises(EntryNotFoundError, match="did you mean"):
        _ = structured.sample2  # close to the real `sample`
    with pytest.raises(EntryNotFoundError) as exc:  # nothing remotely similar: no suggestion
        _ = structured.zzzzzzzz
    assert "did you mean" not in str(exc.value)


def test_unbound_kind_stays_bytes(tree_root: Path) -> None:
    assert isinstance(build_resources(tree_root).binary.raw, bytes)


def test_caches_decoded_value_identity(tree_root: Path) -> None:
    sample = build_resources(tree_root).structured.sample
    sample["mutated"] = True
    assert build_resources(tree_root).structured.sample is not sample  # different tree, fresh cache
    tree = build_resources(tree_root)
    first = tree.structured.sample
    first["mutated"] = True
    assert tree.structured.sample["mutated"] is True  # same object across access


def test_missing_entry_raises_typed_errors(tree_root: Path) -> None:
    tree = build_resources(tree_root)
    with pytest.raises(EntryNotFoundError):
        _ = tree.structured.nope
    with pytest.raises(AttributeError):
        _ = tree.structured.nope
    with pytest.raises(KeyError):
        tree["structured"]["nope"]


def test_registry_override_replaces_default(tree_root: Path) -> None:
    tree = build_resources(tree_root / "structured", {FileType.JSON: lambda b: "SENT"})
    assert tree.sample == "SENT"


def test_container_protocol(tree_root: Path) -> None:
    tree = build_resources(tree_root)
    structured = tree.structured
    assert "sample" in structured
    assert len(structured) == len(structured.items())
    assert "structured" in repr(structured)
    assert structured.path == tree_root / "structured"


def test_missing_root_raises(tree_root: Path) -> None:
    with pytest.raises(ResourceError):
        build_resources(tree_root / "does-not-exist")


async def test_abuild_matches_sync(tree_root: Path) -> None:
    tree = await abuild_resources(tree_root)
    assert tree.structured.sample["id"] == "sample1"


def test_build_merges_multiple_roots_later_wins(tmp_path: Path) -> None:
    base, extra = tmp_path / "base", tmp_path / "extra"
    base.mkdir()
    extra.mkdir()
    (base / "a.json").write_text('{"from": "base"}')
    (base / "only_base.json").write_text('{"v": 1}')
    (extra / "a.json").write_text('{"from": "extra"}')
    (extra / "only_extra.json").write_text('{"v": 2}')
    tree = build_resources([base, extra])
    assert tree.a["from"] == "extra"  # a shared top-level key resolves to the later root
    assert (tree.only_base["v"], tree.only_extra["v"]) == (1, 2)
    assert tree.path == base  # the first root is the nominal tree root


def test_build_requires_every_root(tmp_path: Path) -> None:
    ok = tmp_path / "ok"
    ok.mkdir()
    with pytest.raises(ResourceError):
        build_resources([ok, tmp_path / "missing"])


async def test_abuild_merges_multiple_roots(tmp_path: Path) -> None:
    base, extra = tmp_path / "base", tmp_path / "extra"
    base.mkdir()
    extra.mkdir()
    (base / "a.json").write_text('{"from": "base"}')
    (extra / "a.json").write_text('{"from": "extra"}')
    tree = await abuild_resources([base, extra])
    assert tree.a["from"] == "extra"


def test_public_surface_exported() -> None:
    assert set(pr.__all__) >= {"FileType", "Resources", "build_resources", "abuild_resources", "default_loaders"}
