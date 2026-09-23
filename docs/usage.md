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

## Filtering a folder

A folder is a list of files — `select()` filters it and returns the decoded values. A
string argument is a **glob over the file name**; a compiled `re.Pattern` is
**regex-searched**; `kind=` narrows by `FileType`:

```python
import re

from pytest_resources import FileType


def test_filtering(resources: pr.Resources):
    jsons = resources.data.select("*.json")  # glob (whole-file-name match)
    users = resources.data.select("user_*")  # glob with a prefix
    logs = resources.data.select(re.compile(r"^log"))  # regex: matched with .search
    texts = resources.unstructured.select(kind=FileType.TEXT)  # by canonical kind

    assert jsons and all(isinstance(v, dict) for v in jsons)
```

`select()` with no arguments is `values()` — every file value in the folder.

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

## Errors and "did you mean"

Attribute misses raise `EntryNotFoundError` (a subclass of both `ResourceError` and
`AttributeError`); item misses raise `KeyError`. Both suggest the nearest existing name:

```python
resources.structured.sample2  # EntryNotFoundError: ... did you mean 'sample'?
resources.structured["sample2"]  # KeyError with the same hint
resources.structured.zzzzzzzz  # no hint when nothing is close
```

## Name collisions

Navigation methods (`keys`, `values`, `items`, `path`, `select`, `choice`) win over a
resource of the same name on **attribute** access. Reach such a resource with **item**
access, which always resolves to the entry:

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
