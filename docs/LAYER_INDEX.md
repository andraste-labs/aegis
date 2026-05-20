# Aegis Validator — Layer Index

**Last updated:** 2026-05-20
**Source of truth (pre-extraction):** `Team-AI/src/agents/integration_validator.py`
**Source of truth (post-extraction, Sept 2026):** `aegis/checks/`

This document is the canonical, honest list of every validation pass
Aegis runs. We do not market a round number ("9 layers", "6 layers"); we
publish the real count and the source code that backs it.

## Categories

| Category | Count | Definition |
|---|---|---|
| **Deterministic** | 22 | AST parsing / regex / file I/O / subprocess. No LLM call. Reproducible without API keys. |
| **LLM-as-judge** | 1 | Sends artifact to Claude for evaluation; LLM verdict is final. |
| **Hybrid (LLM + deterministic override)** | 1 | LLM judges; a deterministic evidence scan can OVERRIDE the LLM verdict. |
| **Total** | **24** | |

The headline number for marketing is **22 / 24 = ~92% deterministic**.
Any visitor can verify this by reading the source. There is no fixed
"6 layers" or "9 layers" claim — those numbers were earlier marketing
shorthand that has been corrected.

## Deterministic layers (22)

| # | Method | What it checks | v2 bench case |
|---|---|---|---|
| 1 | `_detect_stacks` | Stack identification (Python / Node / static HTML) via build-config files. | Used by all cases |
| 2 | `_clone_project_repo` / `_materialize_artifacts_from_db` | Repo clone or artifact materialization from local input. | Setup, all cases |
| 3 | `_run_cmd` (venv + pip install) | Isolated venv creation and Python dependency install with timeout. | 07, 20 |
| 4 | `_check_python_imports` | Every relative Python import resolves to an existing module file. | 07 |
| 5 | `_check_python_completeness` | Flags `pass` / `...` / `raise NotImplementedError` stub bodies. | (planned) |
| 6 | `_check_python_deps_completeness` | Every third-party Python import declared in requirements.txt / pyproject.toml. | (planned) |
| 7 | `_check_router_prefix_consistency` | FastAPI router prefix double-mount detection (`/api/api/...`). | (planned) |
| 8 | `_check_node_deps_completeness` | Bare-specifier JS/TS imports declared in package.json. | 05 |
| 9 | `_check_css_completeness` | CSS files contain real rules, not stub comments. | (planned) |
| 10 | `_check_react_prop_consistency` | JSX prop pass-through mismatch detection. | (planned) |
| 11 | `_check_named_import_consistency` | Named imports target modules that actually export them. | (planned) |
| 12 | `_check_import_case_consistency` | Case-permutation mismatches in import names + file paths (TS/JS + Python). | **04** |
| 13 | `_check_duplicate_type_declarations` | TypeScript `interface` / `type` collisions across files. | (planned) |
| 14 | `_check_hook_destructure_consistency` | React hook consumers don't destructure non-existent fields. | (planned) |
| 15 | `_check_brace_balance` | Brace / paren / bracket balance in JS files. | (planned) |
| 16 | `_check_static_imports` | Relative imports and `<script src>` exist on disk. | (planned) |
| 17 | `_check_html_js_id_parity` | Every `#id` JS hooks into exists in the HTML. | (planned) |
| 18 | `_check_interactivity` | Interactive HTML elements have at least one wired event handler. | **10** |
| 19 | `_check_js_syntax` | `node --check` over every JS file (static_html projects). | (planned) |
| 20 | `_run_cmd` (npm install --ignore-scripts) | Node dependency install, sandboxed against supply-chain scripts. | **05**, **13** |
| 21 | `_run_cmd` (tsc) | TypeScript compiler type-check. | **06** |
| 22 | `_run_cmd` (pytest / jest) | Test suite execution if tests exist. | **08**, **09** |

## LLM-as-judge layer (1)

| # | Method | What it judges | Why LLM | v2 bench case |
|---|---|---|---|---|
| 23 | `_check_design_fidelity_async` | Whether output respects the design brief (palette, philosophy, density, microcopy tone). | AST has nothing structural to grip on for "tone" or "philosophy alignment." | **01**, **02**, **16**, **17** |

The LLM verdict here is **guarded by a deterministic override** for
specific dimensions: when the brief lists palette hexes, the validator
greps the CSS for each hex; when fewer than N appear, `palette` is
capped at 4 regardless of the LLM's score. This is what bench cases
01 and 16 exercise.

## Hybrid layer (1)

| # | Method | LLM responsibility | Deterministic guard | v2 bench case |
|---|---|---|---|---|
| 24 | `_check_feature_coverage_async` | LLM judges whether each declared feature is actually implemented. | Deterministic scan looks for code evidence markers; if LLM says PASSED but no markers exist, the scan **OVERRIDES** the LLM and the check FAILS. The deterministic layer has the final word. | **18**, **19** |

## Layer coverage in the bench

| Phase | Cases | Layers exercised | Coverage |
|---|---|---|---|
| v1 (4 cases) | 01–04 | 1, 4, 12, 20, 21, 23 (partial via case 01–02) | ~6 / 24 |
| v2 (20 cases) | 01–20 | All 24 at least once | 24 / 24 |

The v2 cohort is designed so that every layer fires at least once and
every layer that uses LLM judgment is also exercised against its
deterministic override. See `aegis-bench/PLAN_V2.md` for the
per-case design.

## Honesty notes

- **Earlier `integration_validator.py` docstring** said *"this agent
  does NOT call an LLM"*. That was inaccurate; corrected on 2026-05-06.
- **Marketing claims** of "6 layers" (Andraste Stratejik Finans Rapor
  §3) and "9 layers" (earlier pitch deck slide) **understated** the
  architecture. The actual surface is broader. Both have been updated
  to refer to this document.
- **The investor-relevant metric** is "what fraction of validation runs
  without LLM in the loop?" — currently 22/24 ≈ **92% deterministic**.
  Two LLM passes (one of them deterministic-override-guarded) sit at
  the semantic edges where structural analysis can't reach.
- **Reproducibility:** any of the 22 deterministic checks can be run
  on a fresh machine without an Anthropic API key. This is the
  `aegis check --no-llm` mode.

## Pluggable LLM client (post-extraction)

In the public Aegis package, the LLM-using layers (23 and 24) consume
an `LLMClient` Protocol rather than a hard-coded Anthropic SDK call.
The default implementation is `AnthropicClient`; users can swap in
their own to use a different model or provider without forking Aegis.
See `docs/CODE_EXTRACTION_PLAN.md` for the API design and
`aegis/llm_client.py` (post-extraction) for the implementation.

This means **the moat in this layer index is not "Anthropic" — it's
the architecture: 22 deterministic layers + 1 LLM judge guarded by
deterministic override + 1 hybrid layer with deterministic final
word.** Whether the LLM is Claude or GPT or local Llama is the user's
choice.

## When you change the validator

If you add a check, update this table **in the same PR**. If you remove
or rename one, update both this file and the docstring in the
implementation. The audit principle is: **the public number must
match the code, always.**

## Cross-references

- Implementation: `aegis/checks/` (post-extraction) /
  `Team-AI/src/agents/integration_validator.py` (today)
- Extraction plan: [`CODE_EXTRACTION_PLAN.md`](./CODE_EXTRACTION_PLAN.md)
- Bench cases that exercise each layer:
  [`../aegis-bench/PLAN_V2.md`](../aegis-bench/PLAN_V2.md)
- Methodology for what counts as a hit/miss:
  [`../aegis-bench/METHODOLOGY.md`](../aegis-bench/METHODOLOGY.md)
