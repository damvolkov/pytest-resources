# Configuration

## Root directories

By default the plugin indexes `<rootdir>/tests/resources`. When the fixture runs it
**creates any resolved root that is missing**, so a fresh checkout never errors. You can
point it at several directories at once:

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

All resolved roots are indexed and **merged into one navigable tree**. On a top-level name
clash the **later** root wins (hook-appended roots come last), so a more specific root can
override a shared one. `build_resources` / `abuild_resources` accept a single path or a
sequence of paths.

## File kinds

`FileType` is a `StrEnum` resolved from the file extension. Known kinds:
`JSON, JSONC, NDJSON, YAML, TOML, INI, CSV, TSV, MARKDOWN, TEXT, HTML, XML, PYTHON,
BINARY`. Anything unknown resolves to `BINARY`.

## The loader table

Decoding is a mapping `FileType -> (bytes -> object)`. `default_loaders()` returns the
best table available:

- **e-serde installed** (`pytest-resources[serde]`): native codecs for JSON/JSONC/YAML/
  TOML/INI, producing native `dict`s.
- **otherwise**: the standard library — `json` for JSON/NDJSON, `tomllib` for TOML.
- **unbound kinds** (CSV, HTML, …): raw `bytes`, for the caller to decode.

## Registering custom loaders

Bind or override any kind from a `conftest.py` through the hook:

```python
from pytest_resources import FileType
import csv, io

def pytest_resource_loaders(register):
    register({FileType.CSV: lambda b: list(csv.DictReader(io.StringIO(b.decode())))})
```

`register` merges into the session table, so it overrides defaults and adds new kinds with
the same call.
