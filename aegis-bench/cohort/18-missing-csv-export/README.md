# 18 — missing CSV export

**Category:** J — Feature coverage (hybrid: deterministic keyword scan + LLM judge)
**Stack:** Static HTML + vanilla JS
**Layer fired:** `feature_coverage` (KIND=hybrid; Stage 1 deterministic discriminates here)
**Expected verdict:** `FAIL · feature_coverage · 1/3 missing — CSV export`

> **LLM calibration status:** Stage 1's deterministic keyword scan does
> the discriminating work for THIS case — the marker words `export`
> and `download` do not appear in any source file, period. Stage 2's
> LLM verdict is documented as expected behavior; final calibration
> against claude-opus-4-7 captures the precise score wording before
> public launch.

## What this case demonstrates

The brief lists three features:

1. user table with name, email, signup date columns ✓
2. sort by clicking column headers ✓
3. **export current view to CSV via a download button** ✗

The generated dashboard delivers #1 and #2 cleanly. Column-header
sorting works, the table renders correctly, the styling is consistent
with the brief.

For #3, the code contains:

- **Zero references** to `csv`, `export`, `download`, `Blob`, or
  `text/csv`.
- **No button** in the DOM beyond the table headers.
- **No event handler** that produces a downloadable file.

The agent silently dropped the feature.

## How `feature_coverage` catches it

The layer has two stages:

**Stage 1 — deterministic keyword scan.** For each feature label,
derive 1-3 keyword markers via stopword strip + Turkish suffix
tolerance + length sort. For `"export current view to CSV via a
download button"`, the markers are:

- `export`
- `download`

(Stopwords like "current", "view", "via", "button" are stripped.)
Then scan the lowercased code blob (HTML + JS + CSS concatenated). If
**none** of the markers appear, the feature is **definitively**
absent — Stage 1 says missing.

**Stage 2 — LLM judge.** The LLM gets the full feature list and the
full code and reports `present | missing | partial` per feature with
short evidence. Stage 2 is expected to agree: there is no CSV export
UI, the LLM should say "missing" with evidence pointing at the missing
button.

**Cross-validation.** When Stage 1 says missing AND Stage 2 says
missing → confident FAIL. When Stage 1 says missing AND Stage 2 says
present → the LLM must back up its claim with evidence the keyword
scanner can locate (an id, class, function name, file path). If the
LLM points only at prose ("the feature works"), the rescue path
fails and the feature is demoted to missing anyway.

For this case, both halves agree — the cleanest demo of the hybrid
layer's discipline.

## What every other layer says

| Layer | Verdict | Why |
|---|---|---|
| `js_syntax` | PASS | JS is valid. |
| `static_imports` | PASS | All paths resolve. |
| `ast_brace_balance` | PASS | Braces balanced. |
| `interactivity` | PASS | 3 sort handlers count as interactivity — the layer doesn't know WHICH features they wire. |
| `html_js_id_parity` | PASS | JS uses class/data selectors, not phantom ids. |
| **`feature_coverage`** | **FAIL** | Stage 1 + Stage 2 agree: CSV export missing. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **Pure LLM judge** | USUALLY FAIL, sometimes tricked | A tooltip / header that says "export" can fool a pure LLM into "present". Stage 1's strict keyword scan blocks that path. |
| **eslint / stylelint** | PASS | No tool for "verify against feature list". |
| **Manual QA** | FAIL | A user clicks around looking for export, gives up. |
| **Aegis (hybrid)** | **FAIL** | Stage 1 + Stage 2 agree. Even if the LLM rubber-stamped, Stage 1 alone would still flag. |

## Why this case matters

Feature drop is the single most common silent-failure mode of
agent-generated code. The agent reads the brief, builds the obvious
parts, runs out of context or attention, and silently ships without
the feature. No static tool — eslint, tsc, stylelint — has any way
to know what the brief said. `feature_coverage` is the only layer
that explicitly checks against the brief.

This case proves the layer fires correctly when both halves of the
hybrid agree.

## Files

- `brief.json` — dashboard with 3 features including CSV export
- `input/index.html` — table markup only, no export button (THE BUG)
- `input/app.js` — sorting logic, zero CSV references (THE BUG)
- `input/styles.css` — table styles
- `expected.json` — documented verdict with deterministic findings
