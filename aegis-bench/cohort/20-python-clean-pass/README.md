# 20 — Python clean pass (baseline)

**Category:** K — Clean pass / baseline
**Stack:** Python 3.11+ / FastAPI
**Layer fired:** none (all applicable layers pass)
**Expected verdict:** `PASS · 6 passed · 0 failed · ~15 skipped (correct stack mismatch)`

## What this case demonstrates

This is the Python equivalent of the Node clean-pass case (#03 in v1).
A minimal FastAPI service with:

- `app/__init__.py` declaring `__version__`
- `app/main.py` with a single `GET /health` route
- `tests/test_health.py` with a happy-path test using `fastapi.testclient`
- `requirements.txt` declaring fastapi + httpx + pytest

Idiomatic project layout, no architectural shortcuts, no failure modes.

The pipeline runs every Python-applicable layer:

| Layer | Verdict | What it checked |
|---|---|---|
| `python_imports` | PASS | All `from app import …` resolve. |
| `python_completeness` | PASS | Both function bodies are real implementations (not `pass` / `...`). |
| `python_deps_completeness` | PASS | fastapi, httpx, pytest all declared. |
| `router_prefix_consistency` | PASS | Zero prefixed routers + zero include_router calls → nothing to mis-mount. |
| `import_case_consistency` | PASS | All `from X import Y` casing matches what X exports. |
| `pytest` | PASS | One test, exits 0. |

Other layers correctly skip — Node/static-HTML layers are out of scope
for a Python project. design_fidelity + feature_coverage skip when
no LLM client is configured.

## Why this case matters

A bench full of failure cases is incomplete without baselines. If
Aegis ever starts false-FAILing healthy code — a layer flagging a
non-bug — case 20 is the canary. The PR that introduced the false
positive can't ship without this case turning red.

The contrast with case 03 (Node clean pass, in v1) is also
intentional: both stacks must produce clean PASS verdicts under
identical pipeline rules. If Python and Node clean cases diverge,
that's a stack-coverage gap.

## What every other layer says

Same as the verdict table above — every applicable layer passes,
inapplicable layers skip cleanly.

## Why baselines all also pass

| Tool | Verdict | Why |
|---|---|---|
| **pylint** | PASS | Idiomatic Python, no warnings. |
| **ruff** | PASS | No rule violations. |
| **mypy** | PASS | Types align. |
| **pytest direct** | PASS | The test passes. |
| **Aegis** | **PASS** | Every layer agrees with the baselines. |

## Files

- `brief.json` — minimal health service intent
- `input/requirements.txt` — fastapi + httpx + pytest
- `input/app/__init__.py` — exports `__version__`
- `input/app/main.py` — `GET /health` returning status + version + timestamp
- `input/tests/__init__.py` — package marker
- `input/tests/test_health.py` — single happy-path test using fastapi.testclient
- `expected.json` — passed=true, list of expected per-layer outcomes
