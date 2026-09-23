# Changelog

All notable changes to **pytest-resources** are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-09-23

First release.

### Added

- `resources` pytest fixture: a session-scoped, lazy index over one or more resource
  directories, navigable as an attribute / item / iterable tree
  (`r.a.b`, `r["a"]["b"]`, `list(r.a)`, `.keys()/.values()/.items()`, `in`, `len`).
- `FileType` (`StrEnum`) resolving extensions to canonical kinds through a frozen suffix
  table; anything unknown resolves to `BINARY`.
- A pluggable loader table (`default_loaders`) that prefers
  [`e-serde`](https://pypi.org/project/e-serde/) native codecs (JSON / JSONC / YAML / TOML /
  INI) when installed and falls back to the standard library (`json` + `tomllib`); kinds
  with no parser return raw `bytes`. e-serde is an optional `[serde]` extra, never a core
  dependency.
- Extraction helpers on every node: `select` / `first` (filtered values), `paths` (file
  paths), `walk` / `awalk` (recursive, sync and async), `similar` (fuzzy stem match),
  `choice` (randomised pick) and `as_dict` (nested dict export).
- Root configuration: `--resources-root` (repeatable), the `resources_root` ini list, and
  the `pytest_resources_roots` hook for contributions; multiple roots are merged into one
  tree, with the later root winning a top-level clash. The fixture creates a missing root;
  the programmatic API stays strict.
- A `pytest_resource_loaders(register)` hook to bind or override any codec declaratively.
- Programmatic `build_resources` / `abuild_resources` (sync and off-the-loop), each taking a
  single path or a sequence of paths.
- A module-lifetime decode cache per tree, and typed misses (`EntryNotFoundError` /
  `KeyError`) that carry a `difflib` "did you mean" hint.

[unreleased]: https://github.com/damvolkov/pytest-resources/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/damvolkov/pytest-resources/releases/tag/v0.1.0
