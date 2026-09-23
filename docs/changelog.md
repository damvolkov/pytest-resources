# Changelog

This page mirrors the repository changelog. See
<https://github.com/damvolkov/pytest-resources/blob/main/CHANGELOG.md> for the canonical file.

## [0.1.0] - 2026-09-23

Initial public release.

- `resources` session fixture: a lazy, cached index over one or more resource directories,
  navigable by attribute, item and iteration.
- `FileType` + a frozen suffix table; unknown kinds fall back to `BINARY` / raw `bytes`.
- Pluggable loaders: [`e-serde`](https://pypi.org/project/e-serde/) by default (the optional
  `[serde]` extra), a stdlib (`json` + `tomllib`) fallback otherwise, and a
  `pytest_resource_loaders` hook to bind or override any codec.
- Extraction helpers: `select` / `first` / `choice` / `paths` / `walk` / `awalk` / `similar`
  / `as_dict`.
- Multiple roots via repeatable `--resources-root`, the `resources_root` ini list, and the
  `pytest_resources_roots` hook — merged into one tree, later root wins.
- Programmatic `build_resources` / `abuild_resources` (sync and async), and typed misses
  with a "did you mean" hint.
