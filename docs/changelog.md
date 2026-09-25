# Changelog

This page mirrors the repository changelog. See
<https://github.com/damvolkov/pytest-resources/blob/main/CHANGELOG.md> for the canonical file.

## [0.3.0] - 2026-09-25

- **Default loader is now the standard library** (`json` + `tomllib`); the core has zero
  third-party dependencies. e-serde is an opt-in `[serde]` extra (register
  `eserde_loaders()`), recommended as the fast, multi-format official loader. `JSONC`,
  `YAML` and `INI` are `bytes` until you register a codec.

## [0.2.0] - 2026-09-24

- Optional on-the-fly synthesis behind `[objects]` (polyfactory), `[files]` (faker-file) and
  `[random]`: `make()` / `batch()` build model instances or bare hints, `file()` writes a
  real synthetic file (25 formats) and adopts it into the tree. New document/image
  `FileType`s. A missing extra raises `ExtraNotInstalledError` with the install command.

## [0.1.0] - 2026-09-23

- `resources` session fixture: a lazy, cached index over one or more resource directories,
  navigable by attribute, item and iteration.
- `FileType` + a frozen suffix table; unknown kinds fall back to `BINARY` / raw `bytes`.
- Pluggable loaders with a `pytest_resource_loaders` hook to bind or override any codec.
- Extraction helpers: `select` / `first` / `choice` / `paths` / `walk` / `awalk` / `similar`
  / `as_dict`.
- Multiple roots via repeatable `--resources-root`, the `resources_root` ini list, and the
  `pytest_resources_roots` hook — merged into one tree, later root wins.
- Programmatic `build_resources` / `abuild_resources` (sync and async), and typed misses
  with a "did you mean" hint.
