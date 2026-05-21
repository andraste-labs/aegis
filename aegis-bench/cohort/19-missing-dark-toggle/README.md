# 19 — missing dark-mode toggle (LLM rubber-stamp guard)

**Category:** J — Feature coverage (hybrid: deterministic keyword scan + LLM judge override)
**Stack:** Static HTML + vanilla JS
**Layer fired:** `feature_coverage` (KIND=hybrid; override path expected to fire)
**Expected verdict:** `FAIL · feature_coverage · override_fired · "light/dark mode toggle" missing`

> **Status:** Stage 1 (deterministic keyword scan) is INDEPENDENTLY
> VERIFIED — the markers `[toggle, light, dark]` derived from the
> feature label "light/dark mode toggle" appear in **zero** input
> files. Stage 2 LLM verdict + final score capture against
> `claude-opus-4-7` runs before public launch.

## What this case demonstrates

This is the bench's strongest "LLM-can-rubber-stamp, deterministic-
floor-saves-us" demo.

The brief asks for three features:

1. write a note in the textarea + Add button → ✓ delivered
2. notes appear in a list below → ✓ delivered
3. **light/dark mode toggle** → ✗ DROPPED

The generated code:

- Renders a CHARCOAL background by default via CSS variables
  (`--surface-1: #0F172A`). The page LOOKS like a dark-mode app.
- Has zero occurrences of the words `light`, `dark`, or `toggle` in
  any source file.
- Has no toggle button in the markup.
- Has no theme-swap handler in the JS.

A **pure LLM judge** reading this code may very well score the
"light/dark mode toggle" feature as `present`, citing evidence like
"dark theme is visible via CSS variables" or "the app uses a dark
palette". The page IS dark; the LLM rubber-stamps.

`feature_coverage`'s **hybrid layer** prevents this:

1. **Stage 1 (deterministic).** Extract markers from the feature
   label: `["toggle", "light", "dark"]` after stopword strip. Scan
   the lowercased code blob. **None of the three markers appear**
   — Stage 1 flags the feature MISSING.

2. **Stage 2 (LLM judge).** The LLM might say `present`.

3. **Cross-validation.** When Stage 1 says missing AND Stage 2 says
   present, the LLM's evidence string is checked. The evidence must
   point at a concrete code symbol (an id, a class name, a function
   name) that the keyword scanner can locate. **Prose evidence
   doesn't rescue the feature.** "dark theme is visible via CSS
   variables" is prose, not a concrete symbol. The rescue fails.
   Feature stays missing. `override_fired = true`.

This is the moat in one sentence: **the LLM cannot rubber-stamp a
feature whose marker words appear nowhere in the code, unless its
evidence points at a real symbol.**

## Why we strip `dark` from the code intentionally

A different generated codebase could have a `data-theme="dark"`
attribute or a `.dark-mode` class. In that case, the word `dark`
would appear, Stage 1 would not flag, and the layer would rely on
the LLM alone — which might fail to notice the missing toggle UI.
That's a real layer limitation; future Aegis releases plan an
"interactive-element subcheck" for binary state features. For this
case, we want to demonstrate the rubber-stamp guard in its clearest
form, so we ensure the dark-styling implementation uses generic
variable names (`--surface-1`, `--text-1`) without leaking the
discriminating words.

## What every other layer says

| Layer | Verdict | Why |
|---|---|---|
| `js_syntax` | PASS | JS is valid. |
| `static_imports` | PASS | All paths resolve. |
| `ast_brace_balance` | PASS | Braces balanced. |
| `html_js_id_parity` | PASS | All hooked ids exist in HTML. |
| `interactivity` | PASS | Composer + Enter keybind count as interactivity. |
| `css_completeness` | PASS | Real CSS with rules + custom properties. |
| **`feature_coverage`** | **FAIL — override_fired** | Stage 1 flags + Stage 2 demoted via missing-symbol-evidence. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **Pure LLM judge** | AT RISK — rubber-stamps because dark styling is visible | Without a deterministic floor, the LLM scores from vibes. |
| **eslint / stylelint** | PASS | Neither knows about the brief. |
| **HTML/JS validators** | PASS | Both files are valid. |
| **Manual QA** | FAIL | The user sees dark, looks for a toggle, doesn't find one. |
| **Aegis (hybrid)** | **FAIL — override_fired** | The deterministic floor locks in the missing-feature verdict regardless of LLM rubber-stamp. |

## Files

- `brief.json` — note-taking app, light/dark toggle as feature #3
- `input/index.html` — composer + list markup, no toggle button (THE BUG)
- `input/app.js` — composer handlers + render loop, no theme handler (THE BUG)
- `input/styles.css` — charcoal-by-default palette via generic surface variables
- `expected.json` — documented verdict with Stage 1 finding + override expectation
