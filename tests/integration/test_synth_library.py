"""tests/integration: the synthesis feature with its optional backends really installed.

Objects come out of polyfactory for every model family a project may use; files
come out of faker-file, land on disk, join the indexed tree and decode through the
same loader table as any authored resource.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypedDict

import attrs
import msgspec
import pydantic
import pytest

import pytest_resources as pr

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_resources import FileType, Resources


@dataclass
class User:
    name: str
    age: int


class Pet(pydantic.BaseModel):
    species: str
    legs: int


class Point(msgspec.Struct):
    x: float
    y: float


@attrs.define
class Book:
    title: str
    pages: int


class Row(TypedDict):
    k: str
    v: int


@pytest.fixture
def tree(tmp_path: Path) -> Resources:
    return pr.build_resources(tmp_path)


def test_make_builds_a_dataclass_instance(tree: Resources) -> None:
    user = tree.make(User)
    assert isinstance(user, User)
    assert isinstance(user.name, str)
    assert isinstance(user.age, int)


@pytest.mark.parametrize("model", [User, Pet, Point, Book])
def test_make_autodetects_every_model_family(tree: Resources, model: type[Any]) -> None:
    assert isinstance(tree.make(model), model)


def test_make_builds_a_typeddict_model(tree: Resources) -> None:
    row = tree.make(Row)
    assert isinstance(row, dict)
    assert set(row) == {"k", "v"}
    assert isinstance(row["k"], str)
    assert isinstance(row["v"], int)


def test_batch_defaults_to_ten(tree: Resources) -> None:
    assert len(tree.batch(User)) == 10


def test_batch_returns_n_instances(tree: Resources) -> None:
    squad = tree.batch(User, 4)
    assert [type(item) for item in squad] == [User] * 4


def test_make_pins_fields_from_overrides(tree: Resources) -> None:
    assert tree.make(User, name="ada", age=36) == User(name="ada", age=36)


@pytest.mark.parametrize("hint", [int, str, float, list[int], dict[str, int], list[tuple[str, int]]], ids=str)
def test_make_serves_bare_type_hints(tree: Resources, hint: Any) -> None:
    value = tree.make(hint)
    assert type(value) is hint or callable(getattr(hint, "__origin__", None))


def test_batch_of_hints(tree: Resources) -> None:
    rows = tree.batch(list[int], 3)
    assert len(rows) == 3
    assert all(isinstance(row, list) for row in rows)


def test_make_is_reproducible_under_a_seed(tree: Resources) -> None:
    assert tree.batch(User, 5, seed=42) == tree.batch(User, 5, seed=42)
    assert tree.make(User) != tree.make(User)


@pytest.mark.parametrize(
    "kind",
    [
        pr.FileType.BINARY,
        pr.FileType.TEXT,
        pr.FileType.CSV,
        pr.FileType.JSON,
        pr.FileType.XML,
        pr.FileType.PDF,
        pr.FileType.DOCX,
        pr.FileType.XLSX,
        pr.FileType.PPTX,
        pr.FileType.EPUB,
        pr.FileType.RTF,
        pr.FileType.ODT,
        pr.FileType.ODS,
        pr.FileType.ODP,
        pr.FileType.EML,
        pr.FileType.ZIP,
        pr.FileType.TAR,
        pr.FileType.ICO,
        pr.FileType.BMP,
        pr.FileType.GIF,
        pr.FileType.JPEG,
        pr.FileType.PNG,
        pr.FileType.TIFF,
        pr.FileType.WEBP,
    ],
    ids=lambda kind: kind.value,
)
@pytest.mark.filterwarnings("ignore:imghdr was removed in Python 3.13:DeprecationWarning")
def test_file_writes_a_real_non_empty_file(tree: Resources, kind: FileType) -> None:
    try:
        path = tree.file(kind)
    except OSError as exc:
        pytest.skip(f"faker-file cannot synthesize {kind.value} here: {exc}")  # needs a system font / no temp lock
    assert path.exists()
    assert path.stat().st_size > 0
    assert pr.FileType.of_path(path) is kind


def test_file_resolves_a_suffix_from_a_filename(tree: Resources) -> None:
    path = tree.file("invoice.xlsx", name="invoice.xlsx")
    assert path.name == "invoice.xlsx"


def test_named_file_is_adopted_and_decoded_like_an_authored_one(tree: Resources) -> None:
    path = tree.file("txt", name="note")
    assert tree.note == path.read_bytes().decode()  # the node value is exactly the loader's decode
    assert path in tree.paths("*.txt")


def test_json_synthetic_decodes_to_a_container(tree: Resources) -> None:
    tree.file("json", name="doc")
    assert isinstance(tree.doc, dict | list)


def test_csv_synthetic_stays_raw_bytes_until_a_loader_is_bound(tree: Resources) -> None:
    tree.file("csv", name="rows")
    assert isinstance(tree.rows, bytes)


def test_choice_and_walk_see_synthetic_files(tree: Resources) -> None:
    try:
        path = tree.file("png", name="logo")
    except OSError as exc:
        pytest.skip(f"faker-file cannot synthesize png here: {exc}")  # needs a system font
    assert tree.choice("*.png") == path.read_bytes()
    assert path in list(tree.walk("*.png"))


def test_file_is_reproducible_under_a_seed(tree: Resources) -> None:
    one = tree.file("txt", name="one", seed=3)
    two = tree.file("txt", name="two", seed=3)
    assert one.read_text() == two.read_text()
