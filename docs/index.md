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
```

JSON / JSONC / YAML / TOML / INI decode through
[e-serde](https://pypi.org/project/e-serde/) by default (any other kind is pluggable and
falls back to raw `bytes`), with the standard library used automatically when e-serde is
absent.

## At a glance

| Capability | How |
|---|---|
| Navigate like the filesystem | `r.a.b`, `r["a"]["b"]`, `list(r.a)`, `.keys()/.values()/.items()`, `in`, `len` |
| Extract from a folder | `select` (values) · `paths` (files) · `walk` (recursive) · `similar` (fuzzy) — by glob / regex / kind |
| Randomise a pick | `r.a.choice(...)` (session-seeded) or pass your own `rng` |
| Lazy + cached | nothing read at collection; each file decoded once per session |
| Any format, honest fallback | unknown or unbound kinds hand back `bytes` |
| One tree from many roots | CLI / ini / `pytest_resources_roots` hook, merged (later wins) |
| Pluggable codecs | `pytest_resource_loaders` hook; e-serde optional (`[serde]`) |
| Typed misses | `EntryNotFoundError` with a "did you mean" hint |

- [Usage](usage.md) — navigation, filtering, randomising, programmatic API.
- [Configuration](configuration.md) — roots, the format matrix, custom loaders.
- [Changelog](changelog.md)
