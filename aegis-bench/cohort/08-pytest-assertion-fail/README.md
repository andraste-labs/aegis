# 08 — pytest assertion fail (wrong formula)

**Category:** F — Test failures
**Stack:** Python 3.11+
**Layer fired:** `pytest` (deterministic; subprocess `python -m pytest -q`)
**Expected verdict:** `FAIL · pytest · 2 tests failed (got 50.0, expected 1051.25)`

## What this case demonstrates

The brief asks for weekly-compound interest:

> `principal * (1 + annual_rate/52) ** (52 * years)`

The generated `compound_interest` function looks structurally fine —
type hints, docstring, single-line return, rounded to 2 decimals — but
uses **simple** interest instead of weekly-compound:

```python
def compound_interest(principal: float, annual_rate: float, years: int) -> float:
    # Generated code returns: principal * rate * years    (simple interest)
    # Brief asked for:        principal * (1+r/52)**(52t) (weekly compound)
    return round(principal * annual_rate * years, 2)
```

For `1000 @ 5% for 1 year`:
- Brief expects: `1051.25`
- Generated returns: `50.0`

Every static layer passes — there's no structural or syntactic cue that
the formula is wrong. The function takes the right types, returns the
right type, runs without errors. The pytest layer is the only one that
exposes the bug, by computing reference values from the correct formula
and asserting.

## What every other layer says

| Layer | Verdict | Why it's silent |
|---|---|---|
| `python_imports` | PASS | Imports resolve. |
| `python_completeness` | PASS | Function has a real body — not a stub. |
| `python_deps_completeness` | PASS | Declared deps (pytest only) cover everything imported. |
| `import_case_consistency` | PASS | No case mismatches. |
| **`pytest`** | **FAIL** | Reference assertion fails: `isclose(50.0, 1051.25)` is False. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **pylint** | PASS | Well-formed function with type hints and a return. The formula is semantically wrong, not structurally. |
| **ruff** | PASS | Same. |
| **mypy** | PASS | Types check out. |
| **Raw Claude critique** | INCONSISTENT | Sometimes catches by reading the function name vs body, sometimes overlooks. Depends heavily on prompt wording. |
| **GPT-4 critique** | Same as above. |
| **pytest itself** | **FAIL** | The reference scenarios produce the wrong numbers. |

## Why this case matters

This is the textbook argument for keeping test execution in the
validator stack. Static analysis has a hard ceiling — once the
structure is correct, no amount of AST inspection or type-checking
can verify that the *math* is right. Tests are the only check that
catches "the function does the wrong thing".

The generated tests (also AI-written, also wrong in principle) DO
encode the correct formula because the test author worked from the
brief, and the brief specifies the formula explicitly. So even when
both the implementation AND the tests are LLM-output, the divergence
between "implement formula X" and "test formula X" tends to align —
making the test the discriminating signal.

## Files

- `brief.json` — project intent including the explicit weekly-compound formula
- `input/requirements.txt` — just pytest
- `input/src/__init__.py` — package marker
- `input/src/interest.py` — `compound_interest` with the wrong formula (THE BUG)
- `input/tests/__init__.py` — package marker
- `input/tests/test_interest.py` — two reference scenarios with correct expected values
- `expected.json` — what Aegis should report
