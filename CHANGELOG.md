# Changelog

All notable changes to **pytest-resources** are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-09-24

### Added

- Optional synthesis surface on `Resources`, loaded lazily only when used: `make()` and
  `batch()` build random instances of project models (dataclass, pydantic, msgspec, attrs,
  TypedDict) or any bare type hint — singly or in size-`n` lists, with field overrides and
  `seed`; `file()` writes a real
  synthetic file in 25 formats (PDF, DOCX, XLSX, images, archives, …) to disk and **adopts**
  it into the tree, so it navigates, filters and decodes like any authored resource.
- Extras `[objects]` (polyfactory), `[files]` (faker-file) and `[random]` (both). Calling a
  method without its extra raises `ExtraNotInstalledError` — a `ResourceError` /
  `ImportError` carrying the exact install command. The backends are hidden behind a single
  vendor seam (`pytest_resources.synth`) and a structural port on `Resources`.
- `FileType` growth: document and image kinds (`PDF, DOCX, XLSX, PPTX, EPUB, RTF, ODT, ODS,
  ODP, EML, MP3, ZIP, TAR, ICO, BMP, GIF, JPEG, PNG, TIFF, WEBP`) now resolve from their
  suffixes instead of collapsing into `BINARY`. Decode behaviour is unchanged — unbound
  kinds still hand back raw `bytes` — and these are the kinds `file()` can synthesize.

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

[unreleased]: https://github.com/damvolkov/pytest-resources/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/damvolkov/pytest-resources/releases/tag/v0.2.0
[0.1.0]: https://github.com/damvolkov/pytest-resources/releases/tag/v0.1.0
