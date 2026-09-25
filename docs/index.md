# pytest-resources

Lazy, typed, **attribute-navigable** fixtures for test resource files.

Point it at one or more directories of samples and it recursively indexes the tree
*without reading anything*, then hands you a decoded value the moment you touch it — cached
for the whole session.

```python
import pytest_resources as pr


def test_profile(resources: pr.Resources):
    user = resources.structured.user  # .json -> dict (decoded, cached)
    body = resources.unstructured.intro  # .md   -> str
    blob = resources.binary.logo  # no codec bound -> raw bytes

    jsons = resources.data.select("*.json")  # filter a folder
    pick = resources.data.choice("*.json")  # random pick (seeded per run)

    rows = resources.make(list[tuple[str, int]])  # random data from a type hint [objects]
    pdf = resources.file("report.pdf")  # a real synthesized PDF, already indexed [files]
```

JSON / JSONC / YAML / TOML / INI decode through
[e-serde](https://pypi.org/project/e-serde/) by default (any other kind is pluggable and
falls back to raw `bytes`), with the standard library used automatically when e-serde is
absent. `make()` / `batch()` / `file()` synthesize model instances and files in 25
formats on the fly, adopted into the same navigable tree, behind the optional
`[objects]` / `[files]` / `[random]` extras. Everything is async-test friendly:
`abuild_resources` and `awalk` keep the loop free, `make`/`batch` are pure CPU.

## At a glance

| Capability | How |
|---|---|
| Navigate like the filesystem | `r.a.b`, `r["a"]["b"]`, `list(r.a)`, `.keys()/.values()/.items()`, `in`, `len` |
| Extract from a folder | `select`/`first` (values) · `paths` (files) · `walk`/`awalk` (recursive, sync/async) · `similar` (fuzzy) · `as_dict` (nested export) |
| Randomise a pick | `r.a.choice(...)` (session-seeded) or pass your own `rng` |
| Synthesize on the fly | `make(Model \| hint)` · `batch(Model \| hint, n)` · `file(kind \| name)` — optional `[objects]` / `[files]` / `[random]` |
| Async-test friendly | `abuild_resources`/`awalk` off the loop; `make`/`batch` are pure CPU; adopted files navigate like any other |
| Lazy + cached | nothing read at collection; each file decoded once per session |
| Any format, honest fallback | unknown or unbound kinds hand back `bytes` |
| One tree from many roots | CLI / ini / `pytest_resources_roots` hook, merged (later wins) |
| Pluggable codecs | `pytest_resource_loaders` hook; e-serde optional (`[serde]`) |
| Typed misses | `EntryNotFoundError` with a "did you mean" hint |

- [Usage](usage.md) — navigation, filtering, randomising, programmatic API.
- [Configuration](configuration.md) — roots, the format matrix, custom loaders.
- [Changelog](changelog.md)
