# pytest-resources

Lazy, typed, **attribute-navigable** fixtures for test resource files.

Point it at a directory of samples and it recursively indexes the tree *without reading
anything*, then hands you a decoded value the moment you touch it — cached for the whole
session.

```python
import pytest_resources as pr

def test_profile(resources: pr.Resources):
    user = resources.structured.user        # .json -> dict (decoded, cached)
    body = resources.unstructured.intro     # .md   -> str
    blob = resources.binary.logo            # no codec bound -> raw bytes
```

JSON / JSONC / YAML / TOML / INI decode through
[e-serde](https://pypi.org/project/e-serde/) by default; any other kind is pluggable.

- [Usage](usage.md)
- [Configuration](configuration.md)
- [Changelog](changelog.md)
