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
PYTHON`, the document/image families `PDF, DOCX, XLSX, PPTX, EPUB, RTF, ODT, ODS, ODP,
EML, MP3, ZIP, TAR, ICO, BMP, GIF, JPEG, PNG, TIFF, WEBP`, and `BINARY`. Any other
extension resolves to `BINARY`. Every kind is a navigation and loader key; document and
image kinds are typed but bind no codec by default, so they decode to raw `bytes` — and
they are exactly the kinds the `[files]` extra can synthesize.

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
| `CSV`, `TSV`, `HTML`, `XML`, `PYTHON`, documents/images (`PDF`, `DOCX`, `XLSX`, `PNG`, …), `BINARY`, unknown | `bytes` | `bytes` |

With e-serde installed the five config formats it supports (`JSON/JSONC/YAML/TOML/INI`) all
decode natively; `NDJSON` is line-split JSON and `MARKDOWN`/`TEXT` are UTF-8 decoded.
Without it, only `JSON`/`TOML`/`NDJSON`/`MARKDOWN`/`TEXT` decode and the rest stay `bytes`.
`CSV`, `TSV`, `HTML`, `XML`, `PYTHON` and every document or image kind (`PDF`, `DOCX`,
`XLSX`, `PNG`, …) are **never** decoded by default — they are `bytes` until you register
a loader (the honest, open-ended fallback). The document and image kinds exist so they
are *typed* and so the `[files]` extra can synthesize them.

## Installing

```bash
uv add --group test "pytest-resources[serde]"   # e-serde default codecs (recommended)
uv add --group test pytest-resources            # stdlib-only, zero extra deps
uv add --group test "pytest-resources[objects]" # random objects from your models (polyfactory)
uv add --group test "pytest-resources[files]"   # synthetic files, 25 formats (faker-file)
uv add --group test "pytest-resources[random]"  # both synthesis backends
```

`e-serde` is an optional `[serde]` extra, never a core dependency of the plugin. The
synthesis extras gate `resources.make()` / `resources.batch()` (`[objects]`) and
`resources.file()` (`[files]`); calling either without its extra raises
`ExtraNotInstalledError` naming the exact install command.

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
