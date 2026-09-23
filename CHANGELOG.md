# Changelog

All notable changes to **pytest-resources** are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `ResourceNode.select(*globs_or_regex, kind=...)`: filter a folder's files by name
  (glob, or a compiled regex searched with `.search`) and/or canonical `FileType`;
  returns the decoded values. `values()` now delegates to it.
- `ResourceNode.paths(...)`: the same filter, returning the file `Path`s (raw bytes,
  `open()`, or handing a fixture file to another library).
- `ResourceNode.walk(...)`: depth-first, lazy, recursive file `Path`s across a subtree,
  with the same glob / regex / `kind` filters.
- `ResourceNode.awalk(...)`: the async-generator twin of `walk` for streaming large trees
  with `async for` (pairs with `abuild_resources`).
- `ResourceNode.first(...)`: the first matching file value in name order — the deterministic
  twin of `choice` (raises `ResourceError` when nothing matches).
- `ResourceNode.as_dict()`: the whole subtree as a plain nested `dict` (folders recurse,
  files are decoded values) — for snapshots and payload comparison.
- `ResourceNode.similar(term, kind=..., n=..., cutoff=...)`: values whose file *stem* is
  lexically close to `term` (`difflib.get_close_matches`), best first — a fuzzy lookup.
- `ResourceNode.choice(*globs_or_regex, kind=..., rng=...)`: a random file value, using the
  session-seeded global `random` by default (so `pytest-randomly` keeps it reproducible) or
  a caller-supplied `random.Random`.
- A "did you mean" hint, via `difflib`, on `EntryNotFoundError` / `KeyError` misses.
- `pytest_resources_roots(roots)` hook: contribute extra resource directories from a
  `conftest.py`, additively (mirrors `pytest_resource_loaders`).
- **Multiple resources roots**: `--resources-root` is now repeatable and the
  `resources_root` ini key is a list. Every resolved root is indexed and merged into one
  navigable tree; on a top-level name clash the later root wins.
- `build_resources` / `abuild_resources` accept a single path or a sequence of paths.
- The `resources` fixture creates a missing root (e.g. a fresh `tests/resources`) instead
  of erroring; the programmatic `build_resources` stays strict (raises `ResourceError`).

### Removed

- Dropped the unused `pytest-xdist` test dependency (nothing enabled `-n`/`--dist`).

## [0.1.0]

### Added

- `resources` pytest fixture: a session-scoped, lazy index over a resources directory
  (default `<rootdir>/tests/resources`), exposed as an attribute/item/iterable tree.
- `FileType` (`StrEnum`) mapping file extensions to canonical kinds; unknown → `BINARY`.
- A pluggable loader table (`default_loaders`) that prefers
  [`e-serde`](https://pypi.org/project/e-serde/) native codecs (JSON/JSONC/YAML/TOML/INI)
  when installed and falls back to the standard library (`json` + `tomllib`); kinds with
  no parser return raw `bytes`.
- `pytest_resource_loaders(register)` hook to bind or override loaders declaratively from
  any `conftest.py`.
- `--resources-root` CLI option and `resources_root` ini key to relocate the indexed root.
- Programmatic `build_resources` (sync) and `abuild_resources` (off-loop) constructors.
- Module-lifetime decode cache per tree: a resource parsed once is reused across the session.

### Fixed

- n/a (initial release).

[unreleased]: https://github.com/damvolkov/pytest-resources/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/damvolkov/pytest-resources/releases/tag/v0.1.0
