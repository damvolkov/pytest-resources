"""tests/unit: the synthesis surface on the root — lazy module load, delegation and tree adoption."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pytest_resources import build_resources

if TYPE_CHECKING:
    from pytest_resources.nodes import Resources

SAMPLE = Path("/synth")


@dataclass
class User:
    name: str
    age: int


class _StubProvider:
    """Records what Resources forwards and returns controlled paths."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def make(self, spec: object, /, *, seed: int | None = None, **fields: object) -> object:
        self.calls.append(("make", spec, seed, fields))
        return "OBJECT"

    def batch(self, spec: object, /, n: int = 10, *, seed: int | None = None, **fields: object) -> list[object]:
        self.calls.append(("batch", spec, n, seed, fields))
        return ["OBJECT"] * n

    def file(self, kind: object, /, *, name: str | None = None, seed: int | None = None) -> Path:
        self.calls.append(("file", kind, name, seed))
        return SAMPLE / f"{name or 'anon'}.pdf"


@pytest.fixture
def tree(tmp_path: Path) -> Resources:
    return build_resources(tmp_path)


def test_synth_module_stays_unloaded_until_first_use(tree: Resources) -> None:
    assert tree._synth is None


def test_make_forwards_spec_seed_and_fields(tree: Resources) -> None:
    tree._synth = stub = _StubProvider()
    assert tree.make(User, seed=5, name="ada") == "OBJECT"
    assert stub.calls == [("make", User, 5, {"name": "ada"})]


def test_batch_forwards_spec_size_seed_and_fields(tree: Resources) -> None:
    tree._synth = stub = _StubProvider()
    assert tree.batch(User, 3, seed=5, name="ada") == ["OBJECT"] * 3
    assert stub.calls == [("batch", User, 3, 5, {"name": "ada"})]


def test_file_forwards_kind_name_and_seed(tree: Resources) -> None:
    tree._synth = stub = _StubProvider()
    assert tree.file("pdf", name="doc", seed=2) == SAMPLE / "doc.pdf"
    assert stub.calls == [("file", "pdf", "doc", 2)]


def test_file_adopts_the_path_as_an_entry(tree: Resources) -> None:
    tree._synth = _StubProvider()
    path = tree.file("pdf", name="doc")
    assert tree._entries["doc"] == path
    assert path in tree.walk("*.pdf")


def test_named_file_owns_its_slot_against_a_real_file(tmp_path: Path) -> None:
    (tmp_path / "report.pdf").write_bytes(b"real")
    tree = build_resources(tmp_path)
    tree._synth = _StubProvider()
    path = tree.file("pdf", name="report")
    assert tree._entries["report"] == path
    assert "report" in tree
    assert "report_2" not in tree


def test_anonymous_file_never_overwrites_its_key(tree: Resources) -> None:
    class _Clash(_StubProvider):
        def file(self, kind: object, /, *, name: str | None = None, seed: int | None = None) -> Path:
            self.step = getattr(self, "step", 0) + 1
            return Path(f"/synth{self.step}") / "anon.pdf"

    tree._synth = _Clash()
    tree.file("pdf")
    tree.file("pdf")
    assert "anon" in tree
    assert "anon_2" in tree


def test_repeated_same_path_replaces_without_a_counter(tree: Resources) -> None:
    tree._synth = _StubProvider()
    tree.file("pdf")
    tree.file("pdf")
    assert "anon" in tree
    assert "anon_2" not in tree
