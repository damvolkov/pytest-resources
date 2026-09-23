# Usage

The `resources` fixture auto-loads via the `pytest11` entry point — no import in your
`conftest.py` is required. It is a session-scoped, lazily decoded view over your resources
directory.

## Navigation

Every folder is a node with three equivalent views that always agree:

```python
import pytest_resources as pr


def test_reads_tree(resources: pr.Resources):
    # attribute access mirrors the directory layout
    assert resources.structured.sample["id"] == "sample1"

    # item access is equivalent (and always hits the entry, see "Name collisions")
    assert resources["structured"]["sample"]["id"] == "sample1"

    # nested folders are first-class nodes
    assert resources.structured.nested.deep["id"] == "deep"

    # iterating a folder yields its decoded FILE values; directories are skipped
    values = list(resources.structured)

    # mapping helpers
    assert resources.structured.keys()  # every entry name, files and folders
    assert resources.config.items()  # (name, resolved) pairs; folders as nodes
    assert len(resources.structured) and "sample" in resources.structured
```

Files are read and decoded on first access and **memoized for the session**, so the same
resource is parsed exactly once no matter how many tests touch it.

## Extracting from a folder

A folder is a list of files. Every query below shares the same filters: a **string is a
glob over the file name**, a **compiled `re.Pattern` is regex-searched** (`.search`), and
`kind=` narrows by canonical `FileType` (pass none of them to mean *everything*).

| Call | Returns |
|---|---|
| `folder.select(*globs, kind=…)` | decoded **values** of matching files in this folder |
| `folder.first(*globs, kind=…)` | the **first** matching value in name order (deterministic) |
| `folder.paths(*globs, kind=…)` | the **`Path`s** themselves — for raw bytes, `open()`, or handing a file to another library |
| `folder.walk(*globs, kind=…)` | matching **`Path`s recursively** across the whole subtree, lazily |
| `folder.awalk(*globs, kind=…)` | the **async-generator twin** of `walk`, for streaming with `async for` |
| `folder.similar(term, kind=…)` | decoded values whose file **stem is lexically close** to `term` (difflib, best first) |
| `folder.choice(*globs, kind=…, rng=…)` | one **random** matching value (see next section) |
| `folder.as_dict()` | the whole subtree as a **plain nested `dict`** — folders recurse, files are values |

```python
import re

from pytest_resources import FileType


def test_extraction(resources: pr.Resources):
    jsons = resources.data.select("*.json")  # glob (whole-file-name match)
    users = resources.data.select(re.compile(r"^user"))  # regex: matched with .search
    texts = resources.unstructured.select(kind=FileType.TEXT)  # by canonical kind

    # reach the files themselves (raw bytes, or a path to hand to another lib)
    raw = resources.data.paths("blob.*")[0].read_bytes()

    # every .json anywhere below the root, without loading what you skip
    for path in resources.walk("*.json", kind=FileType.JSON):
        assert path.suffix == ".json"

    # fuzzy name lookup: 'usr' still finds user.json
    near = resources.data.similar("usr")
```

`select()` with no arguments is `values()` — every file value in the folder. All queries
run against the already-walked tree, so filtering never re-reads the disk; only the values
you actually touch are decoded (and cached).

## Randomising the choice

`choice()` returns one random file value. With no `rng` it uses the global `random`, which
`pytest-randomly` already seeds — so a run is reproducible and the pick varies per test.
Pass your own `random.Random(seed)` for explicit determinism:

```python
import random


def test_random_fixture(resources: pr.Resources):
    one = resources.videos.choice("*.mp4")  # seeded by pytest-randomly
    stable = resources.videos.choice("*.mp4", rng=random.Random(0))  # yours, pinned

    # a random *subset* is a one-liner, with no extra reserved name:
    two = random.Random(0).sample(resources.videos.select("*.mp4"), 2)
```

## Streaming a large tree (async)

For big resource trees, build off the event loop and walk it lazily with the async
generator, so nothing is held as a list and only the values you touch are decoded:

```python
from pathlib import Path

import pytest_resources as pr


async def test_stream():
    tree = await pr.abuild_resources(Path("fixtures"))  # walked off the loop
    async for path in tree.awalk("*.json"):  # streamed, one Path at a time
        assert path.suffix == ".json"
```

`awalk` is the async twin of `walk`; both are lazy generators and share the same
glob / regex / `kind` filters.

## Errors and "did you mean"

Attribute misses raise `EntryNotFoundError` (a subclass of both `ResourceError` and
`AttributeError`); item misses raise `KeyError`. Both suggest the nearest existing name:

```python
resources.structured.sample2  # EntryNotFoundError: ... did you mean 'sample'?
resources.structured["sample2"]  # KeyError with the same hint
resources.structured.zzzzzzzz  # no hint when nothing is close
```

## Name collisions

Navigation and query methods (`keys`, `values`, `items`, `as_dict`, `path`, `select`,
`first`, `paths`, `walk`, `awalk`, `similar`, `choice`) win over a resource of the same name
on **attribute** access. Reach such a resource with **item** access, which always resolves
to the entry:

```python
resources.data.select  # the method
resources.data["select"]  # the file named select.* (if present)
```

## Programmatic use

Outside the fixture, index a tree yourself — one path or several, sync or off the loop:

```python
from pathlib import Path

import pytest_resources as pr

tree = pr.build_resources(Path("fixtures"))  # sync
tree = pr.build_resources([Path("fixtures"), Path("fixtures/shared")])  # merged
tree = await pr.abuild_resources(Path("fixtures"))  # walked off the event loop
tree = pr.build_resources(Path("fixtures"), {FileType.JSON: my_loader})  # custom registry
```

`build_resources` is strict: a path that is not a directory raises `ResourceError`.
