# pytest-resources

Lazy, typed, attribute-navigable fixtures for test resource files — JSON / JSONC / YAML /
TOML / INI decoded through [`e-serde`](https://pypi.org/project/e-serde/) by default,
extensible to **any** canonical `bytes -> object` loader, and anything else handed back as
raw `bytes`.

You point it at one or more directories of sample files; it recursively indexes the tree
without reading anything, and you reach, filter and randomise parsed values the way they
read:

```python
import pytest_resources as pr

def test_profile(resources: pr.Resources):
    user = resources.structured.user          # sample dir -> dict (decoded, cached)
    body = resources.unstructured.intro       # a .md -> str
    blob = resources.binary.logo              # no codec bound -> raw bytes

    jsons = resources.data.select("*.json")   # filter a folder (glob / regex / kind)
    pick = resources.data.choice("*.json")    # random pick, seeded per run
```

## Install

```bash
uv add --group test "pytest-resources[serde]"   # e-serde default codecs
uv add --group test pytest-resources            # stdlib-only (json + tomllib)
```

The `resources` fixture auto-loads via the `pytest11` entry point — no imports in your
`conftest.py`.

## What you get

| Idea | Mechanism |
|---|---|
| **Recursive index, zero read** | each root is walked once (off the loop); only paths are held |
| **Lazy + cached** | a file decodes on first access and is memoized for the session |
| **Attr / item / iter views** | `r.a.b`, `r["a"]["b"]`, `list(r.a)` → list of decoded values |
| **Extract from a folder** | `select` (values) · `paths` (files) · `walk` (recursive) · `similar` (fuzzy), by glob / regex / `kind` |
| **Randomise the pick** | `r.a.choice(...)` (session-seeded) or pass your own `rng` |
| **Typed by suffix** | `FileType` (`StrEnum`) resolves the extension; the loader table decodes |
| **Open-ended fallback** | `CSV`/`TSV`/`PDF`/… and any unknown kind stay raw `bytes` |
| **Many roots, one tree** | CLI / ini / `pytest_resources_roots` hook, merged (later wins), auto-created |
| **Pluggable codecs** | override or add any kind through the `pytest_resource_loaders` hook |
| **e-serde default, optional** | native Rust/C config codecs when installed; stdlib otherwise |
| **Friendly misses** | `EntryNotFoundError` / `KeyError` carry a "did you mean" hint |

## Configuring the roots

By default the plugin indexes `<rootdir>/tests/resources` (and **creates it if missing**).
Point it at one or several directories:

```toml
# pyproject.toml
[tool.pytest.ini_options]
resources_root = ["fixtures", "fixtures/shared"]   # default: <rootdir>/tests/resources
```

Or per run (`--resources-root` is repeatable), or additively from your `conftest.py`:

```python
from pathlib import Path

def pytest_resources_roots(roots):
    roots.append(Path("tests/fixtures/shared"))
```

CLI wins over ini, which wins over the default. Every resolved root is merged into one
navigable tree; on a top-level clash the **later** root wins.

## Custom loaders (the extension seam)

The plugin never assumes e-serde. Bind any parser declaratively in your `conftest.py`:

```python
from pytest_resources import FileType
import yaml, csv, io

def pytest_resource_loaders(register):
    register({FileType.CSV: lambda b: list(csv.DictReader(io.StringIO(b.decode())))})
    register({FileType.YAML: yaml.safe_load})
```

`register` merges into the session's table, so you can override a default kind as easily
as add an unknown one. Kinds left unbound hand back **raw bytes**.

## Programmatic use

Outside pytest, build a tree yourself:

```python
from pathlib import Path
import pytest_resources as pr

tree = pr.build_resources(Path("fixtures"))                      # sync, one root
tree = pr.build_resources([Path("a"), Path("b")])               # merged roots, later wins
tree = await pr.abuild_resources(Path("fixtures"))              # off the event loop
table = pr.default_loaders()                                    # best available codecs
```

## Development

```bash
make install   # uv sync + git hooks
make check     # ruff + ty + tach + validate + tests
make ci        # everything the pipeline runs (adds coverage gate + docs + zizmor)
```

## License

MIT
