# 07 — python missing import

**Category:** E — Build failures
**Stack:** Python 3.11+
**Layer fired:** `pytest` (deterministic; subprocess `python -m pytest -q`)
**Expected verdict:** `FAIL · pytest · NameError: name 'asyncio' is not defined`

## What this case demonstrates

The brief asks for a small async clock helper with tests. The generated
code declares the function correctly — `async def get_time()`, awaits
a sleep, returns an ISO timestamp — but forgets one line at the top:

```python
# src/api.py
from datetime import datetime, timezone
# ← missing: import asyncio


async def get_time() -> dict[str, str]:
    await asyncio.sleep(1)        # ← NameError lurks here
    return {"now": datetime.now(timezone.utc).isoformat()}
```

The module IMPORTS without error — `asyncio.sleep` is referenced inside
a function body, not at module top level, so Python doesn't try to
resolve the name until the function is actually called. The bug is
runtime-deferred.

Every Aegis static layer for Python passes:

- `python_imports` — verifies that imports that ARE present resolve to
  real files. Missing imports aren't its job.
- `python_completeness` — flags stub functions; `get_time` has a real
  body.
- `python_deps_completeness` — verifies declared deps cover used
  third-party packages. `asyncio` is stdlib — out of scope.

The failure shows up only when `pytest` runs the test, calls
`asyncio.run(get_time())`, the function body executes, and Python tries
to resolve `asyncio.sleep` for the first time — `NameError`.

## Why this matters

This is one of the cases that argues hardest for keeping `pytest` in
the deterministic layer stack. There's no static check in Aegis that
catches "name used but never imported" for stdlib references — `ruff`
with `F821` would catch it externally, but inside our pipeline `pytest`
is the backstop. The same applies to typo'd identifiers, missing
helpers in shared modules, and any other "valid syntax, missing name"
class of bug.

## What every other layer says

| Layer | Verdict | Why it's silent |
|---|---|---|
| `python_imports` | PASS | All imports present in the file resolve. The missing `import asyncio` isn't there to check. |
| `python_completeness` | PASS | `get_time` has a real body — not a stub. |
| `python_deps_completeness` | PASS | Declared deps (`pytest`, `pytest-asyncio`) cover everything imported. `asyncio` is stdlib. |
| `router_prefix_consistency` | PASS | No FastAPI routers in this case. |
| `import_case_consistency` | PASS | Casing is fine. |
| **`pytest`** | **FAIL — NameError** | Runs the test, executes the function, raises NameError on `asyncio.sleep`. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **pyflakes** | FAIL | Has a specific rule for "name used but not imported". Aegis does not currently run pyflakes inline; pytest catches the same failure at runtime. |
| **ruff F821** | FAIL | Same as pyflakes — undefined-name rule. |
| **mypy** | FAIL with `--strict` | Treats undefined names as type errors in strict mode. |
| **Raw Claude critique** | UNRELIABLE | Sometimes catches, sometimes overlooks. Depends on prompt. |
| **No-linter setups** | PASS | A project without a linter ships the bug; only running the tests reveals it. |

## Files

- `brief.json` — project intent and stack
- `input/requirements.txt` — pytest + pytest-asyncio only
- `input/src/__init__.py` — package marker
- `input/src/api.py` — async clock helper, MISSING `import asyncio` (THE BUG)
- `input/tests/__init__.py` — package marker
- `input/tests/test_api.py` — runs `get_time` via `asyncio.run`, expects a dict
- `expected.json` — what Aegis should report
