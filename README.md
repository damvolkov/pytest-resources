# pytest-resources

Lazy, typed, attribute-navigable fixtures for test resource files — decoded through the
**Python standard library** by default (`json` + `tomllib`, zero extra dependencies),
extensible to **any** canonical `bytes -> object` loader. The optional
[`e-serde`](https://pypi.org/project/e-serde/) extra is **recommended** as the fast,
multi-format official loader; anything without a parser is handed back as raw `bytes`.

You point it at one or more directories of sample files; it recursively indexes the tree
without reading anything, and you reach, filter, randomise and synthesize parsed values
the way they read:

```python
from dataclasses import dataclass

import pytest_resources as pr


@dataclass
class User:
    name: str
    age: int


def test_profile(resources: pr.Resources):
    user = resources.structured.user          # sample dir -> dict (decoded, cached)
    body = resources.unstructured.intro       # a .md -> str
    blob = resources.binary.logo              # no codec bound -> raw bytes

    jsons = resources.data.select("*.json")   # filter a folder (glob / regex / kind)
    pick = resources.data.choice("*.json")    # random pick, seeded per run

    ada = resources.make(User, name="ada")    # random model instance    [objects]
    squad = resources.batch(User, 8)          # a typed list of them     [objects]
    pdf = resources.file("report.pdf")        # synthetic file, indexed [files]
```

## Install

```bash
uv add --group test pytest-resources            # default: stdlib (json + tomllib), zero extra deps
uv add --group test "pytest-resources[serde]"   # e-serde — fast, multi-format loader (recommended)
uv add --group test "pytest-resources[objects]" # resources.make()/batch(): random model objects
uv add --group test "pytest-resources[files]"   # resources.file(): synthetic files, 25 formats
uv add --group test "pytest-resources[random]"  # both synthesis backends
```

The `resources` fixture auto-loads via the `pytest11` entry point — no imports in your
`conftest.py`. Everything (index, navigation, synthesis) is async-test friendly:
`make`/`batch` are pure in-memory CPU and `abuild_resources`/`awalk` keep the loop free;
a missing extra raises `ExtraNotInstalledError` with the exact install command — the plugin
never hard-depends on e-serde, polyfactory or faker-file.

## What you get

| Idea | Mechanism |
|---|---|
| **Recursive index, zero read** | each root is walked once (off the loop); only paths are held |
| **Lazy + cached** | a file decodes on first access and is memoized for the session |
| **Attr / item / iter views** | `r.a.b`, `r["a"]["b"]`, `list(r.a)` → list of decoded values |
| **Extract from a folder** | `select`/`first` · `paths` · `walk`/`awalk` (sync/async, lazy) · `similar` (fuzzy) · `as_dict`, by glob / regex / `kind` |
| **Randomise the pick** | `r.a.choice(...)` (session-seeded) or pass your own `rng` |
| **Synthesize on the fly** | `make(Model \| hint, seed, **pins)` / `batch(Model \| hint, n)` for objects, `file(kind \| name, ...)` for real files adopted into the tree — optional `[objects]` / `[files]` / `[random]` extras |
| **Typed by suffix** | `FileType` (`StrEnum`) resolves the extension; the loader table decodes |
| **Open-ended fallback** | `CSV`/`TSV`/`PDF`/… and any unknown kind stay raw `bytes` |
| **Many roots, one tree** | CLI / ini / `pytest_resources_roots` hook, merged (later wins), auto-created |
| **Pluggable codecs** | override or add any kind through the `pytest_resource_loaders` hook |
| **Stdlib default, e-serde opt-in** | `json`/`tomllib` by default; register `eserde_loaders()` for the fast multi-format backend |
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

### The recommended official loader: e-serde

The default is the standard library. Install the `[serde]` extra and register one call to
make [`e-serde`](https://pypi.org/project/e-serde/) your official loader — ultrarapid,
native Rust/C, and it decodes JSONC/YAML/INI too:

```python
from pytest_resources import eserde_loaders

def pytest_resource_loaders(register):
    register(eserde_loaders())
```

## Programmatic use

Outside pytest, build a tree yourself:

```python
from pathlib import Path
import pytest_resources as pr

tree = pr.build_resources(Path("fixtures"))                      # sync, one root
tree = pr.build_resources([Path("a"), Path("b")])               # merged roots, later wins
tree = await pr.abuild_resources(Path("fixtures"))              # off the event loop
table = pr.default_loaders()                                    # stdlib codecs (json + tomllib)
tree = pr.build_resources(Path("fixtures"), pr.eserde_loaders())  # opt into e-serde instead
```

## Development

```bash
make install   # uv sync + git hooks
make check     # ruff + ty + tach + validate + tests
make ci        # everything the pipeline runs (adds coverage gate + docs + zizmor)
```

## License

MIT
