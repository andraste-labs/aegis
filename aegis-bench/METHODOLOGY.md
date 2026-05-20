# aegis-bench — Methodology

This document defines exactly **what counts as a hit, what counts as a
miss, and how scores are computed.** When the benchmark says
*"Aegis caught 18 of 20 failures"*, this document defines what 18 means.

> 🚧 **Pre-launch notice (May 2026):** The cases live in
> `Team-AI/aegis-bench/` today (4 cases as of this writing). At the
> September 2026 public release, the cases — plus 16 new ones described
> in [PLAN_V2.md](./PLAN_V2.md) — land here. This methodology document
> is the contract for what those cases will measure.

## The four primitives

Every test case in `cohort/` is built from the same four primitives:

| Primitive | What it is | Where it lives |
|---|---|---|
| **Brief** | A `DesignDNA` instance — palette, fonts, philosophy, density, motion, tone | `cohort/<n>/brief.json` |
| **Code** | The (typically broken) codebase that an agent might have produced from the brief | `cohort/<n>/input/` |
| **Expected verdict** | What the validator should report when given the (brief, code) pair | `cohort/<n>/expected.json` |
| **Actual verdict** | What the validator actually reports when run | Computed by `scripts/run_aegis.py` |

A case **passes the benchmark** when the actual verdict matches the
expected verdict on these dimensions:

1. **`passed` field** — actual `passed` must equal expected `passed`.
2. **Failing layer name** — when expected says
   `"failed_layer": "build_install"`, the actual verdict must list that
   layer in its failure trace.
3. **Capped dimensions** — every dimension that expected says is capped
   ≤ N must actually be ≤ N in the verdict (applies to design-fidelity
   cases).
4. **Override marker** — if expected says
   `"deterministic_override_expected": true`, the actual verdict's
   `missing` list must contain a string starting with `"DETERMINISTIC OVERRIDE"`.

## Test case categories

The cohort organizes cases into categories that mirror both the audit
critiques the benchmark answers and the layer types of the validator
pipeline.

### A — Palette substitution (1 case in v1, retained in v2)

The brief specifies a palette (e.g. `primary: #2A5252`); the code uses
a different color (e.g. `#4f46e5`, the generic indigo Tailwind default).
The LLM judge often rates this 6–7/10 ("looks fine") because the layout
is otherwise OK. The deterministic override caps `palette` ≤ 4 and the
verdict fails.

```json
{
  "passed": false,
  "min_capped_dimensions": { "palette": 4 },
  "deterministic_override_expected": true
}
```

### B — Forbidden-pattern violation (1 case in v1, retained in v2)

The brief specifies a philosophy that bans certain CSS patterns (e.g.
`apple-flat` forbids `linear-gradient`, `box-shadow: 0 0 *`,
`backdrop-filter`, `text-shadow`). The code uses one or more. The
deterministic override caps `philosophy` ≤ 4.

```json
{
  "passed": false,
  "min_capped_dimensions": { "philosophy": 4 },
  "deterministic_override_expected": true
}
```

### C — Clean pass (2 cases in v2 — Node and Python)

Brief fully honored. Used to measure **false-positive rate**: if a
clean case fails, the validator is over-eager.

```json
{
  "passed": true,
  "deterministic_override_expected": false
}
```

### D — Runtime correctness (1 case in v1, retained)

A deterministic check fails on something the build/test runners wouldn't
catch on their own (e.g. import case mismatch between files that load
each other dynamically).

```json
{
  "passed": false,
  "check_type": "import_case_consistency",
  "deterministic_override_expected": false
}
```

### E — Build failures (3 cases in v2)

The build runner subprocess fails: `npm install` can't resolve a
package, `tsc` reports a type error, Python's `ast` module rejects the
syntax. Pure deterministic — no LLM involvement.

```json
{
  "passed": false,
  "failed_layer": "build_install",
  "stderr_contains": "ENOTFOUND"
}
```

### F — Test failures (2 cases in v2)

Generated code includes tests; tests fail. Demonstrates the value of
running tests, not just compiling.

```json
{
  "passed": false,
  "failed_layer": "test_run",
  "stderr_contains": "AssertionError"
}
```

### G — Semantic & runtime (3 cases in v2)

Code compiles and tests pass (if any), but a semantic rule fires:
undefined event handler, sync I/O in async function, stale state in
React setter. AST-based.

```json
{
  "passed": false,
  "failed_layer": "semantic_<rule>",
  "rule": "async_sync_io"
}
```

### H — Security & supply chain (3 cases in v2)

Sandbox escape attempts, hardcoded credentials, SQL injection patterns.
Mostly regex + AST; one case (malicious preinstall) tests the
subprocess hardening (`--ignore-scripts`, env scrub).

```json
{
  "passed": false,
  "failed_layer": "regex_security",
  "rule": "hardcoded_credential",
  "line": 12
}
```

### I — Design fidelity (LLM judge + override) (2 cases in v2)

Same shape as Category A but exercising different dimensions
(typography substitution, density violation). Tests the LLM-judge layer
plus its deterministic override.

```json
{
  "passed": false,
  "min_capped_dimensions": { "philosophy": 4 },
  "deterministic_override_expected": true,
  "override_reason": "missing fonts: Lora, Inter"
}
```

### J — Feature coverage (hybrid layer) (2 cases in v2)

The brief lists explicit features ("CSV export button", "dark-mode
toggle"). The hybrid layer asks the LLM whether each feature exists,
then runs a deterministic evidence search for keyword patterns in the
generated code. Both must agree on FAIL for the layer to fire (high
confidence); when they disagree, the override breaks the tie.

```json
{
  "passed": false,
  "failed_layer": "feature_coverage",
  "missing_feature": "csv_export",
  "llm_verdict": "fail",
  "evidence_verdict": "fail",
  "agreement": "high_confidence_fail"
}
```

## Scoring

For a benchmark run of N cases:

- **Pass rate** = #cases where actual matches expected / N
- **Override-fired rate** = #cases where actual triggered override / #cases where expected override = true
- **False-positive rate** = #cases marked clean (Category C, partial 13) where actual reported FAIL / #clean cases
- **Layer coverage** = #distinct layers fired across the run / #total layers (24 in v1)

A "good run" satisfies:

| Metric | Target |
|---|---|
| Pass rate | ≥ 90% |
| Override-fired rate | ≥ 90% |
| False-positive rate | ≤ 5% |
| Layer coverage | ≥ 80% |

When any metric drops below its bar, the failing case names print to
stdout and the script exits non-zero — usable in CI.

## Disagreements between LLM judge and deterministic override

When the LLM scores `palette: 8` but the deterministic check finds no
hex from the brief in the code, the override caps `palette` at 4 and
marks the verdict with `"DETERMINISTIC OVERRIDE: palette 8->4 (missing #2A5252, #476B57, ...)"` in the `missing` list.

The benchmark records both the original LLM score and the post-override
score so you can compute **override contribution**:

> **Override contribution** = #cases where override changed the outcome
> (passed → failed, or capped a critical dimension) / #total cases.

Expected ranges:

- **0% contribution** — LLM is already accurate enough; override is
  dead weight. Probably the bench cases aren't adversarial enough.
- **15–25% contribution** (v1 actual) — Healthy. LLM is right most of
  the time but wrong about palette-substitution-style cases.
- **>30% contribution** — LLM is unreliable; override is doing the
  heavy lifting. Worth reviewing whether the LLM judge is mis-prompted.

## Baselines

The bench publishes comparison verdicts from three reference systems
per case (under `baselines/`):

1. **Raw LLM critique** — same model, same brief, no validator pipeline.
   The "is this just an LLM wrapper?" baseline.
2. **Conventional static tools** — eslint, ruff, mypy, bandit, tsc,
   gitleaks, trufflehog. The "is this just a linter aggregator?" baseline.
3. **GPT-4 turbo critique** — different model, same task. The "is this
   a Claude-specific quirk?" baseline.

If Aegis catches a failure that all three baselines miss, that's a
point for Aegis. If a baseline catches something Aegis misses, that's
a point against Aegis — and a candidate for a new layer.

## How to add a new test case

1. Create `cohort/<NN>-<short-name>/`.
2. Write `brief.json` — a valid `DesignDNA` JSON (use existing cases
   as templates).
3. Place the broken (or clean) code under `input/`. Keep it small —
   single `index.html` plus optional `style.css` and `app.js` is ideal.
   For Node.js or Python projects, the smallest functional shape.
4. Write `expected.json` with the required fields plus any additional
   capping expectations (Category I) or layer expectations (E-H).
5. Write `README.md` — 2-4 paragraphs explaining what the case
   demonstrates, what each baseline produces, and why this case matters.
6. Run `python scripts/run_aegis.py --case <NN>-<short-name>` to verify
   the validator behaves as expected. If it doesn't, fix the case OR
   fix the validator — and explain which in the PR description.
7. Update `cohort/SUMMARY.md` so the new case is listed in the index.

## The audit principle

**A new validator layer is not "shipped" until a benchmark case
demonstrates what it catches.**

This means every claim Aegis makes in its README is backed by a
reproducible case in this directory. A reviewer running `run_aegis.py`
sees the same numbers we publish.

## Reproducibility commitments

For the bench to be a credible standard, we commit to:

- **Deterministic input.** Every `input/` directory is checked in
  verbatim, not regenerated from an LLM at run time.
- **Pinned LLM versions.** When the LLM judge is invoked, the request
  pins to a specific Claude model version (`anthropic-version` + model
  ID); model upgrades produce a new bench run, not a silent number change.
- **Public results.** Every bench run output JSON is committed to
  `results/` with timestamp. Numbers in marketing materials are
  traceable to a specific results file.
- **Failure of the bench is not failure of Aegis alone.** If a case
  fails because Aegis behavior changed, the case is updated alongside
  the change, with a note in the commit explaining why. If a case
  fails because the validator regressed, that's a regression and gets
  fixed before merge.

## Status snapshot

| Version | Cases | Total layer coverage | Run status |
|---|---|---|---|
| v1 (May 2026, in Team-AI repo) | 4 | ~12 of 24 layers | 4/4 PASS · 2/2 override · 0 false positive |
| v2 (planned, Sept 2026 release) | 20 | ~22 of 24 layers | — |
| Q4 2026 | 40+ | 24/24 | — |

The current v1 result file lives in
`Team-AI/aegis-bench/results/`. The most recent run (May 12, 2026)
shows 4/4 PASS at the 4-case level.
