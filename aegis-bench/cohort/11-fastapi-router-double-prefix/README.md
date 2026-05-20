# 11 — FastAPI router prefix double-mount

**Category:** G — Semantic & runtime
**Stack:** Python 3.11+ / FastAPI
**Layer fired:** `router_prefix_consistency` (deterministic; AST cross-reference)
**Expected verdict:** `FAIL · router_prefix_consistency · /api/api landing path`

## What this case demonstrates

The brief asks for an auth service with endpoints under `/api/auth/*`.
The generator splits the implementation across two files:

```python
# app/api/auth.py
router = APIRouter(prefix="/api", tags=["auth"])   # ← prefix here

@router.post("/auth/login")
def login(creds): ...

@router.post("/auth/register")
def register(creds): ...
```

```python
# main.py
from app.api.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router, prefix="/api")     # ← prefix AGAIN
```

Both files compile. `python_imports` resolves the cross-file import.
`python_completeness` confirms both endpoints have real bodies.
`python_deps_completeness` confirms FastAPI + Pydantic are declared.
But the prefix is mounted **twice**: the router brings its own `/api`,
and `include_router` adds another `/api`. Every endpoint actually
lives at `/api/api/auth/login` and `/api/api/auth/register`. Every
real client returns 404.

This is the canonical Auth-Todo-run bug from the Team-AI rework
history. The router prefix layer walks the AST in two passes:

1. **Pass 1** — record `(file, var_name) → declared_prefix` for every
   `X = APIRouter(prefix="P")` assignment. Also record every
   `from M import V [as A]` to build a per-file alias map.
2. **Pass 2** — for every `*.include_router(arg, prefix="Q")` call,
   resolve `arg`'s root name through the file's alias map back to
   `(origin_file, origin_var)`, then look up its declared prefix.
   Both non-empty → flag the conflict with the landing path.

## What every other layer says

| Layer | Verdict | Why it's silent |
|---|---|---|
| `python_imports` | PASS | The cross-file import resolves. |
| `python_completeness` | PASS | Both endpoint handlers have real bodies. |
| `python_deps_completeness` | PASS | FastAPI + Pydantic declared. |
| `import_case_consistency` | PASS | Casing is fine. |
| **`router_prefix_consistency`** | **FAIL** | Prefix is non-empty on both the APIRouter() declaration AND the include_router() call. |
| `pytest` | SKIP | No tests in the case input. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **pylint** | PASS | Both files are idiomatic FastAPI. |
| **ruff** | PASS | Same. |
| **mypy** | PASS | Type signatures align — `APIRouter(prefix=...)` and `include_router(..., prefix=...)` are both valid. |
| **pytest with mocks** | USUALLY PASS | Unit tests that test handlers directly or use mocked client never hit the prefix math. |
| **Raw Claude critique** | INCONSISTENT | Sometimes catches; often interprets as "deliberate layering". |
| **Live HTTP request** | FAIL | Every request returns 404 — but requires running the server, which the validator avoids. |
| **Aegis** | **FAIL — router_prefix_consistency** | AST cross-reference catches the double prefix in milliseconds. |

## Files

- `brief.json` — auth service expecting `/api/auth/*` endpoints
- `input/requirements.txt` — FastAPI + Pydantic
- `input/app/__init__.py` + `input/app/api/__init__.py` — package markers
- `input/app/api/auth.py` — declares `APIRouter(prefix="/api")` (PREFIX #1)
- `input/main.py` — calls `include_router(auth_router, prefix="/api")` (PREFIX #2 — THE BUG)
- `expected.json` — what Aegis should report
