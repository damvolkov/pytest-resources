# Configuration

## Root directories

By default the plugin indexes `<rootdir>/tests/resources`. When the fixture runs it
**creates any resolved root that is missing**, so a fresh checkout never errors. You can
point it at one or several directories:

```bash
pytest --resources-root=fixtures --resources-root=fixtures/shared   # repeatable
```

```toml
# pyproject.toml — a list of directories
[tool.pytest.ini_options]
resources_root = ["fixtures", "fixtures/shared"]
```

```python
# conftest.py — contribute roots programmatically (additive)
from pathlib import Path


def pytest_resources_roots(roots):
    roots.append(Path("tests/fixtures/shared"))
```

**Precedence:** the CLI list wins over the `resources_root` ini list, which wins over the
default. The `pytest_resources_roots` hook is *additive*: it extends whichever base was
chosen.

Every resolved root is indexed and **merged into one navigable tree**. On a top-level name
clash the **later** root wins (hook-appended roots come last), so a project-specific root
can override a shared one. `build_resources` / `abuild_resources` accept a single path or a
sequence of paths; the programmatic API is strict and raises `ResourceError` if a root is
not a directory.

## File kinds

`FileType` is a `StrEnum` resolved from the file extension through a frozen suffix table.
Known kinds: `JSON, JSONC, NDJSON, YAML, TOML, INI, CSV, TSV, MARKDOWN, TEXT, HTML, XML,
PYTHON, BINARY`. Any other extension — a `.pdf`, an image, an unknown blob — resolves to
`BINARY`.

## The loader table — what decodes how

Decoding is a mapping `FileType -> (bytes -> object)`. The plugin never hard-depends on
[`e-serde`](https://pypi.org/project/e-serde/): it is the default **when installed**, and
the library degrades to the standard library otherwise. Anything neither covers stays raw
`bytes` for you to handle.

| Kind | `pytest-resources[serde]` (default) | stdlib only | 
|---|---|---|
| `JSON` | native `dict` / `list` | `json` |
| `JSONC` | parsed (comments/trailing commas) | `bytes` |
| `YAML` | native `dict` / `list` | `bytes` |
| `TOML` | native `dict` | `tomllib` |
| `INI` | native `dict` | `bytes` |
| `NDJSON` | `list[dict]` (per line) | `list[dict]` (per line) |
| `MARKDOWN`, `TEXT` | `str` | `str` |
| `CSV`, `TSV`, `HTML`, `XML`, `PYTHON`, `BINARY`, unknown | `bytes` | `bytes` |

With e-serde installed the five config formats it supports (`JSON/JSONC/YAML/TOML/INI`) all
decode natively; `NDJSON` is line-split JSON and `MARKDOWN`/`TEXT` are UTF-8 decoded.
Without it, only `JSON`/`TOML`/`NDJSON`/`MARKDOWN`/`TEXT` decode and the rest stay `bytes`.
`CSV`, `TSV`, `HTML`, `XML` and `PYTHON` are **never** decoded by default — they are
`bytes` until you register a loader (the honest, open-ended fallback).

## Installing

```bash
uv add --group test "pytest-resources[serde]"   # e-serde default codecs (recommended)
uv add --group test pytest-resources            # stdlib-only, zero extra deps
```

`e-serde` is an optional `[serde]` extra, never a core dependency of the plugin.

## Registering custom loaders

Bind or override any kind from a `conftest.py` through the hook. `register` merges into the
session table, so it swaps defaults and adds new kinds with one call:

```python
import csv
import io

from pytest_resources import FileType


def pytest_resource_loaders(register):
    register({FileType.CSV: lambda b: list(csv.DictReader(io.StringIO(b.decode())))})
```

A loader is any canonical `bytes -> object` callable. This is the seam that turns the
default `bytes` for `CSV`/`TSV`/`PDF`/… into typed values, and it works the same with or
without e-serde installed.
