# Changelog

All notable changes to Aegis are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial package layout (`aegis/`, `aegis_cli/`) and `pyproject.toml`
  shipping `aegis-validator` on PyPI.
- Top-level `aegis.validate()` async entry point + `ValidationPipeline`.
- `aegis check` CLI with `--brief`, `--json`, `--no-llm`,
  `--exit-on-fail`, `--verbose`.
- `LLMClient` Protocol with `AnthropicClient` reference implementation;
  Anthropic SDK ships as an optional `[anthropic]` extra.
- `aegis.subprocess_runner.run_cmd` — sandboxed subprocess runner with
  credential env scrub and per-command timeout.
- 24 check layers under `aegis/checks/`, registered in canonical
  execution order:

  - `python_imports`, `python_completeness`, `python_deps_completeness`
  - `router_prefix_consistency`
  - `node_deps_completeness`, `css_completeness`
  - `react_prop_consistency`, `named_import_consistency`,
    `import_case_consistency`, `duplicate_type_declarations`,
    `hook_destructure_consistency`
  - `ast_brace_balance`
  - `static_imports`, `html_js_id_parity`, `interactivity`
  - `js_syntax`, `npm_install`, `tsc`, `pytest`
  - `design_fidelity` (hybrid), `feature_coverage` (hybrid)

- `aegis-bench/` cohort: 16 cases under `cohort/05-` through
  `cohort/20-`, each with `brief.json`, `input/`, `expected.json`,
  and a short technical README. `METHODOLOGY.md` describes case
  structure, run command, and reproducibility rules.
- 284 unit tests under `tests/unit/`.
- GitHub Actions workflow (`.github/workflows/test.yml`) — matrix
  pytest on Ubuntu / macOS / Windows for Python 3.11 + 3.12, plus a
  package-build job that produces wheel + sdist artifacts.
- `docs/LAYER_INDEX.md` — single canonical table of layers sourced
  from the registry.

### Notes

- Cases 16, 17, 18, 19 have been calibrated end-to-end against
  `claude-opus-4-7`. Each `expected.json` records the per-dimension
  scores and override behavior from that run.
- `tools/calibrate_llm_cases.py` re-runs the calibration against the
  current model. `.env` (git-ignored) supplies the API key.

[Unreleased]: https://github.com/andraste-labs/aegis/commits/main
