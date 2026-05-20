# Aegis Code Extraction Plan

**Status:** Pre-launch planning (May 2026)
**Target:** September 2026 — Apache 2.0 public release
**Source:** `Team-AI/src/agents/integration_validator.py` (5,301 lines)
**Destination:** This repository

This document describes how the validator code currently embedded in
Team-AI is extracted into a standalone Apache 2.0 library, without
breaking the running Team-AI product. It's an internal engineering
plan — published here in the spirit of "open infrastructure" so that
anyone curious about the rigor of the extraction can read it.

## Why a plan (not just `git mv`)

A naive copy of `integration_validator.py` into this repo wouldn't
work. The file has Team-AI dependencies — agent framework, task/
artifact models, database session helpers, GitHub client — that
shouldn't follow it into a public library. Extracting cleanly requires
identifying what's *core validator* (moves) versus what's *Team-AI
orchestration* (stays), and designing a clean API at the boundary.

Doing this in phases — with golden-output tests between phases — keeps
Team-AI working while the extraction happens.

## Dependency inventory (May 2026 audit)

### Direct top-level imports (3)

| Import | Role | Migration plan |
|---|---|---|
| `from src.agents.base_agent import BaseAgent` | Agent framework — lifecycle, run loop | Stays in Team-AI. Wrapper agent class consumes the extracted library. |
| `from src.models.task import Task` | Input task model | Stays in Team-AI. Maps to a simpler `ValidationRequest` dataclass in aegis. |
| `from src.models.artifact import Artifact, ArtifactType` | Output artifact model | Stays in Team-AI. Maps to `ValidationReport` in aegis. |

### Indirect imports (inside methods, 7)

| Import | Where it's used | Migration plan |
|---|---|---|
| `from src.models.database import get_async_session` | DB read for project metadata | Stays in Team-AI. Replaced with a pluggable `MetadataProvider` interface in aegis (default: file system / kwargs). |
| `from src.models.project import Project as ProjectModel` | Project lookup | Same — Team-AI-only concept. |
| `from src.models.user import User` | User lookup (legacy) | Same. |
| `from src.utils.code_fence import strip_code_fence` | Strip markdown fences from LLM output | **Moves to aegis** — core utility. |
| `from src.utils.design_dna_io import load_design_dna` | Parse brief.json | **Moves to aegis** — core utility. |
| `from src.utils.design_fidelity import check_design_fidelity_async` | LLM-judge design check | **Moves to aegis** — core check layer. |
| `from src.utils.github_client import GitHubClient` | Clone user repos for validation | Stays in Team-AI. Aegis works on a local path; whoever wants to validate a GitHub repo clones it first. |

### Standard library + third-party (stays — already portable)

`asyncio`, `json`, `logging`, `os`, `re`, `shutil`, `subprocess`,
`tempfile`, `datetime`, `pathlib`, `typing`. All present in CPython
stdlib. No third-party deps in the top imports — confirmed via
inspection.

The LLM-judge layers indirectly use `anthropic` SDK via
`src.utils.llm_client`. This becomes a pluggable interface in aegis
(see "LLM client abstraction" below).

## Target package layout

```
aegis-repo/
├── aegis/                         # Pure Python library — pip-installable
│   ├── __init__.py                # Public API: ValidationPipeline, validate(), Report
│   ├── pipeline.py                # Orchestrates the 24 check passes
│   ├── stack_detection.py         # _detect_stacks (python / node / static_html)
│   ├── result.py                  # ValidationReport, LayerResult dataclasses
│   ├── llm_client.py              # LLMClient Protocol + AnthropicClient default impl
│   ├── design_dna.py              # DesignDNA dataclass + brief.json loader
│   ├── subprocess_runner.py       # Sandboxed subprocess (env scrub + timeout + --ignore-scripts)
│   ├── code_fence.py              # strip_code_fence utility
│   └── checks/                    # One module per check layer
│       ├── __init__.py            # Registry of all check classes
│       ├── base.py                # CheckLayer ABC (run(), name(), kind())
│       ├── python_ast.py          # _check_python_imports, _check_python_completeness
│       ├── python_build.py        # pip install + pytest subprocess
│       ├── python_security.py     # bandit-style regex/AST checks
│       ├── node_ast.py            # _check_named_import_consistency, etc.
│       ├── node_build.py          # npm install --ignore-scripts + tsc
│       ├── node_test.py           # jest / vitest subprocess
│       ├── html_js.py             # _check_html_js_id_parity, interactivity
│       ├── css.py                 # _check_css_completeness
│       ├── design_fidelity.py     # LLM-judge + deterministic override
│       └── feature_coverage.py    # Hybrid layer
├── aegis_cli/                     # Standalone CLI
│   ├── __init__.py
│   └── __main__.py                # `python -m aegis_cli check ./path` entrypoint
├── pyproject.toml                 # Package metadata + dependencies
├── aegis-bench/                   # Bench cohort (already scaffolded)
└── tests/
    ├── unit/                      # Per-check unit tests
    ├── golden/                    # Golden-output regression tests
    │   └── fixtures/              # Same input → same output before + after extraction
    └── integration/               # End-to-end pipeline tests
```

### Public API (what users see)

```python
import aegis

# Simple usage: validate a directory, get a report
report = aegis.validate("./my-ai-generated-code")
if report.passed:
    print("Ship it.")
else:
    print(report.summary())  # human-readable
    print(report.to_json())  # machine-readable

# Advanced: customize pipeline
pipeline = aegis.ValidationPipeline(
    stacks=["python", "node"],
    llm_client=aegis.AnthropicClient(api_key=os.environ["ANTHROPIC_API_KEY"]),
    rework_budget=3,
    timeout_per_command=300,
)
report = await pipeline.validate(
    code_path="./my-code",
    brief=aegis.load_brief("brief.json"),
)
```

### CLI

```bash
# Deterministic-only (no API key required)
aegis check ./my-code

# Full pipeline (requires ANTHROPIC_API_KEY)
aegis check ./my-code --brief brief.json

# CI-friendly outputs
aegis check ./my-code --json report.json --exit-on-fail
```

## LLM client abstraction

The validator has two LLM-using layers (design fidelity, feature
coverage). Today they call Claude directly via Team-AI's
`llm_client.py`. For Aegis to be a library others can use without
locking them to Anthropic, we define a `Protocol`:

```python
# aegis/llm_client.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class LLMClient(Protocol):
    """A pluggable LLM client. Aegis ships with an Anthropic implementation;
    users can pass their own to swap models or providers."""

    async def judge(self, prompt: str, *, max_tokens: int = 4096) -> str:
        """Return the model's verdict text for a judgment prompt."""
        ...
```

Default implementation shipped:

```python
class AnthropicClient:
    """Default LLM client — uses anthropic SDK. Requires ANTHROPIC_API_KEY."""
    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-7"):
        ...
    async def judge(self, prompt: str, *, max_tokens: int = 4096) -> str:
        ...
```

This means:
- Most users do nothing — `aegis.validate()` reads `ANTHROPIC_API_KEY`
  from env and uses the default client.
- Users who want to swap to OpenAI / local Llama / cached judgments
  pass their own client matching the Protocol.
- The validator core does NOT hard-import `anthropic` — it's a runtime
  dependency of `AnthropicClient` only.

This addresses Marka v2 §3.8 sütun 2 honestly: today we're
Anthropic-only in default behavior, but the architecture allows
multi-LLM. The library's *contract* doesn't lock users into one
vendor.

## Migration phases

Each phase is independently shippable. Team-AI must keep working
between phases.

### Phase 0 — Discovery (✅ done)

- Identified 3 direct + 7 indirect Team-AI deps (this document)
- Confirmed `aegis_check.py` already exposes deterministic layers as
  standalone CLI
- Confirmed `docs/validator-layers.md` exists as layer index

### Phase 1 — Extract core validator (target: June 2026)

**Goal:** Create `aegis/` package in this repo with the 24 check passes
extracted as pure Python (no Team-AI imports). Team-AI continues to
use its own copy unchanged.

**Steps:**

1. Create `aegis/` package skeleton with `__init__.py` + module stubs.
2. For each `_check_*` method in `integration_validator.py`:
   a. Identify what it reads (file content, AST, etc.).
   b. Identify what it depends on (other `_check_*` methods, helpers).
   c. Extract as a standalone function or `CheckLayer` subclass under
      `aegis/checks/<module>.py`.
   d. Write a unit test that runs the extracted check against a fixture
      and asserts the verdict.
3. Build `ValidationPipeline` orchestrator: detects stack, sequences
   check layers, collects results, applies overrides.
4. Build `ValidationReport` dataclass and `report.to_json()` /
   `report.summary()` methods.

**Acceptance:** All 24 layers extracted, each has at least one unit
test, `aegis/__init__.py` exports `validate(path)` and
`ValidationPipeline`. `pip install -e .` works locally.

**Risk:** Subtle behavior differences between extracted and original.
Mitigation: golden-output tests in Phase 2.

### Phase 2 — Golden-output validation (target: June 2026)

**Goal:** Prove the extracted aegis produces the same verdicts as
Team-AI's original validator on every existing bench case.

**Steps:**

1. Set up `tests/golden/` directory.
2. For each of the 4 existing v1 bench cases, copy the case input and
   the most recent passing result JSON into `tests/golden/fixtures/`.
3. Write a pytest test: `for fixture in fixtures: run aegis on input,
   assert report.to_dict() == expected.json`.
4. Run the test. Fix any divergences in the extracted code — NOT in
   the bench cases (the original behavior is the contract).
5. Commit only when all 4 cases produce identical output.

**Acceptance:** 4/4 golden tests pass. `aegis-bench` results pre- and
post-extraction are byte-for-byte identical.

**Risk:** A check has a hidden dependency on Team-AI behavior we miss.
Mitigation: golden tests are deterministic and reproducible — if a
case diverges, the diff tells us exactly which layer changed behavior.

### Phase 3 — Standalone CLI (target: late June 2026)

**Goal:** Replace the existing `aegis-bench/scripts/aegis_check.py`
with a formal `aegis_cli` package.

**Steps:**

1. Create `aegis_cli/__main__.py` with argparse-based CLI.
2. Implement `aegis check ./path`, `--brief`, `--json`,
   `--exit-on-fail`, `--no-llm`, `--verbose` options.
3. Register entry point in `pyproject.toml`:
   `aegis = "aegis_cli.__main__:main"`.
4. Replace `aegis-bench/scripts/aegis_check.py` with a one-line shim:
   `from aegis_cli.__main__ import main; main()`.

**Acceptance:** `pip install -e .` exposes the `aegis` command. CLI
output matches the old `aegis_check.py` behavior.

### Phase 4 — Migrate Team-AI to consume aegis (target: July 2026)

**Goal:** Team-AI's `integration_validator.py` shrinks from 5,301
lines to ~150 lines — a thin BaseAgent wrapper around `aegis.validate`.

**Steps:**

1. Add `aegis` as a dependency in Team-AI's `requirements.txt` (initially
   `aegis @ git+https://github.com/andraste-labs/aegis.git@main` until
   we tag a release).
2. Rewrite `Team-AI/src/agents/integration_validator.py`:
   ```python
   import aegis
   from src.agents.base_agent import BaseAgent
   from src.models.task import Task
   from src.models.artifact import Artifact, ArtifactType

   class IntegrationValidatorAgent(BaseAgent):
       async def run(self, task: Task) -> Artifact:
           report = await aegis.validate(
               code_path=task.code_path,
               brief=task.brief,
               llm_client=self._get_llm_client(task.user_id),
           )
           return Artifact(
               type=ArtifactType.VALIDATION_REPORT,
               content=report.to_json(),
               passed=report.passed,
           )
   ```
3. Run Team-AI's full integration tests + the aegis-bench cohort.
4. Verify all 4 bench cases still produce identical results in
   production (regression check on real data).
5. Deploy to Railway. Monitor logs for 1 week.

**Acceptance:** Team-AI in production uses extracted aegis. No
regressions in bench, no user-visible behavior changes, validator agent
fewer than 200 lines.

**Risk:** Team-AI in production breaks. Mitigation: feature flag —
`USE_EXTRACTED_AEGIS=true` env var. Roll back instantly if needed.

### Phase 5 — Move aegis-bench from Team-AI to aegis-repo (target: July 2026)

**Goal:** The benchmark lives in the public repo alongside the code
it benches.

**Steps:**

1. `git mv Team-AI/aegis-bench/* aegis-repo/aegis-bench/`.
2. Update `run_aegis.py` to import `aegis` package instead of
   `src.agents.integration_validator`.
3. Delete the `sys.path` hack at top of `run_aegis.py`.
4. Run full bench locally. 4/4 pass.
5. Add `aegis-bench` run to aegis-repo's CI (`ci.yml` — enable the
   `bench` job currently disabled).

**Acceptance:** `aegis-bench/` exists only in this repo. CI runs it on
every PR. Team-AI no longer has an `aegis-bench/` directory.

### Phase 6 — Draft v2 bench cases (target: July–August 2026)

Per `aegis-bench/PLAN_V2.md`:
- July: cases 05–10 (build + test + simple semantic)
- Late July: cases 11–15 (semantic + security)
- August: cases 16–20 (design + feature + multi-stack)

Each case is its own PR with bench result attached. CI ensures none
regress prior cases.

### Phase 7 — Baselines run (target: August 2026)

For each case, run the comparison baselines (raw LLM critique, static
tools, GPT-4) and commit results to `aegis-bench/baselines/<case>/`.
This is the evidence for "Aegis catches what baselines miss."

### Phase 8 — Pre-launch hardening (target: August–September 2026)

- Documentation polish: every public function has a docstring; quick-
  start guide in `README.md`; layer-by-layer doc in `docs/`.
- Performance: profile and optimize the bench runner; target sub-30s
  full bench run on a developer laptop.
- Security review: third-party (or trusted independent) reviewer
  audits subprocess sandboxing.
- Release v1.0.0-rc1, then rc2 if needed, then v1.0.0 on launch day.

### Phase 9 — Public release (September 2026)

- Tag v1.0.0.
- Publish to PyPI: `pip install aegis-validator`.
- Blog post on andrastelabs.com.
- Show HN with link to repo + bench results.
- X / LinkedIn announcements.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Extraction introduces subtle behavior changes | Medium | High | Golden-output tests in Phase 2; identical bench results contract |
| Team-AI production breaks during Phase 4 | Low | High | Feature flag + instant rollback; deploy off-hours |
| Public API churn after launch | Medium | Medium | Take time in Phase 1-2; don't ship until API feels right; semver-strict (1.x never breaks) |
| Bench timing slips beyond September | Medium | Medium | Ship with ≥16 cases if needed (still credible); plan v2.x for the rest |
| LLM client lock-in concern (we're Anthropic-only by default) | Low | Low | Protocol-based; documented in README; user can plug their own |
| Security disclosure during pre-launch | Low | High | SECURITY.md established; coordinated disclosure window |
| Subprocess sandboxing weakness discovered post-launch | Medium | High | Independent review in Phase 8; security patch process documented |

## What's out of scope (intentionally)

- **Replacing the rework dispatcher with autonomous agents.** The
  deterministic dispatcher is a feature, not a limitation. Listed in
  `ROADMAP.md` not-on-roadmap.
- **A hosted SaaS version of Aegis.** Team-AI is the commercial
  product. Aegis stays a library + CLI.
- **VS Code / IDE integration in v1.** Stabilize the core first; IDE
  surface can come in v1.x.
- **Multi-language ports.** Aegis is Python (validator code) + Node
  (some subprocess targets). Porting validator to Go or Rust is not
  on the roadmap.
- **A "lite" commercial edition** with proprietary checks. The whole
  validator is and will remain Apache 2.0. The commercial product is
  Team-AI, which uses Aegis.

## Decisions locked in (2026-05-20)

The three questions that needed to be answered before Phase 1 are
resolved. They cannot be revisited mid-extraction without breaking
downstream work.

### 1. Package name on PyPI: **`aegis-validator`**

PyPI availability check (2026-05-20):

| Candidate | Status |
|---|---|
| `aegis` | ❌ Taken (small unrelated package) |
| **`aegis-validator`** | ✅ **Available — chosen** |
| `aegis-check` | ✅ Available (short but ambiguous) |
| `aegis-bench` | ✅ Available (but bench is a sub-thing) |
| `aegis-cli` | ❌ Taken (this affected decision #2) |

The PyPI distribution name and the Python import name are different
on purpose (same pattern as `scikit-learn` → `import sklearn`):

```bash
pip install aegis-validator
```
```python
import aegis
report = aegis.validate("./code")
```

Rationale: descriptive distribution name (so PyPI search surfaces the
package for "validator" queries), short import name (so user code
isn't cluttered with `aegis_validator.validate(...)` calls).

### 2. Package layout: **Single package, CLI included by default**

Because `aegis-cli` is taken on PyPI, a clean two-package split isn't
available. We ship one package with the CLI bundled:

```bash
pip install aegis-validator
```
gets you both `import aegis` (library) and `aegis check ./path` (CLI).

Rationale: the CLI has no heavy dependencies (argparse is in stdlib;
pretty output uses minimal `rich` or none at all). Splitting into
`[cli]` extra adds cognitive load for users without saving meaningful
install footprint. Single source of truth, single version number.

### 3. Python floor: **3.11+**

| Version | EOL | September 2026 launch buffer |
|---|---|---|
| 3.10 | Oct 2026 | EOL within a month of launch — not worth supporting |
| **3.11** | **Oct 2027** | **1-year buffer — chosen floor** |
| 3.12 | Oct 2028 | Officially supported |
| 3.13 | Oct 2029 | Officially supported |

Rationale:
- 3.10 reaches EOL one month after launch — any user on 3.10 will
  need to upgrade for security patches anyway.
- 3.11 brought significant runtime speedups and improved error
  messages, both of which matter for a validator that runs subprocess
  Python compilation.
- Team-AI runs on 3.11 internally; matching simplifies the extraction
  (no version-shim code for typing differences).
- Aegis's *target* code (the projects it validates) can be any Python
  version — `aegis check` runs the target's own interpreter, not its
  own. The 3.11 floor is for Aegis itself, not for the code it
  validates.

### Implications

These three decisions lock in `pyproject.toml` content for Phase 1:

```toml
[project]
name = "aegis-validator"
version = "0.1.0-dev"
requires-python = ">=3.11"
description = "A deterministic validator for AI-generated code."
authors = [{ name = "Andraste Labs", email = "github@andrastelabs.com" }]
license = { text = "Apache-2.0" }
readme = "README.md"

[project.scripts]
aegis = "aegis_cli.__main__:main"

[project.urls]
homepage = "https://aegis.andrastelabs.com"
repository = "https://github.com/andraste-labs/aegis"
documentation = "https://github.com/andraste-labs/aegis/tree/main/docs"
```

The `pyproject.toml` is added in Phase 1 alongside the first extracted
code.

## Timeline summary

```
 May 2026  ✅ Phase 0 — Discovery, this plan
 Jun 2026  ⏳ Phase 1 — Extract core validator
 Jun 2026  ⏳ Phase 2 — Golden tests
 Jun 2026  ⏳ Phase 3 — Standalone CLI
 Jul 2026  ⏳ Phase 4 — Migrate Team-AI
 Jul 2026  ⏳ Phase 5 — Move aegis-bench here
 Jul-Aug   ⏳ Phase 6 — Draft v2 bench cases (05-20)
 Aug 2026  ⏳ Phase 7 — Baselines
 Aug-Sep   ⏳ Phase 8 — Pre-launch hardening
 Sep 2026  ⭐ Phase 9 — v1.0.0 public release
```

Each phase produces a shippable deliverable. If something slips, the
release happens with fewer cases or less polish — the release does NOT
slip past September. The brand strategy assumes that date; multiple
downstream dates (pre-seed close December 2026, seed May 2027) depend
on it.
