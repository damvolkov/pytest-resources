# Usage

The `resources` fixture auto-loads via the `pytest11` entry point — no import in your
`conftest.py` is required.

```python
import pytest_resources as pr

def test_reads_tree(resources: pr.Resources):
    # attribute navigation mirrors the directory layout
    assert resources.structured.sample["id"] == "sample1"

    # item access is equivalent
    assert resources["structured"]["sample"]["id"] == "sample1"

    # iterating a directory yields its decoded file values (directories are skipped)
    values = list(resources.structured)

    # nested directories are first-class nodes
    assert resources.structured.nested.deep["id"] == "deep"
```

## Lazy and cached

Nothing is read at collection. The directory is walked once; each file decodes on first
access and the result is memoized, so repeated access across tests never re-reads or
re-parses.

## Programmatic use

Outside the fixture you can build a tree yourself:

```python
from pathlib import Path
import pytest_resources as pr

tree = pr.build_resources(Path("fixtures"))          # sync
tree = await pr.abuild_resources(Path("fixtures"))   # off the event loop
```
