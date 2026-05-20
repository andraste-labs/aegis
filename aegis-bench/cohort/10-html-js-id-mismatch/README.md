# 10 — HTML id ↔ JS hook mismatch

**Category:** G — Semantic & runtime
**Stack:** Static HTML + vanilla JS
**Layer fired:** `html_js_id_parity` (deterministic; cross-file regex scan)
**Expected verdict:** `FAIL · html_js_id_parity · phantom ids: theme-toggle, decrement-btn`

## What this case demonstrates

The brief asks for a tip calculator with a theme toggle and +/− people
buttons. The generated HTML and JS are individually correct:

```html
<!-- index.html -->
<button id="theme-switch">🌙</button>
<button id="people-decrement">−</button>
```

```js
// app.js
document.getElementById('theme-toggle').addEventListener('click', …);
document.getElementById('decrement-btn').addEventListener('click', …);
```

Both files pass:
- `node --check` ✓
- HTML validator ✓
- Brace balance ✓
- `interactivity` layer ✓ (HTML has 5 interactive elements, JS has 4 event bindings)

The bug is at the **seam**: HTML and JS were generated independently
and settled on different naming conventions. `theme-switch` vs
`theme-toggle`, `people-decrement` vs `decrement-btn`. At runtime,
`getElementById` returns `null`, the listener is attached to a phantom
node, and clicking does nothing. There is no error message — the page
just refuses to respond.

This is the canonical Tip-Calc-v4 bug from the Team-AI rework history:
all single-file static checks pass, the page renders perfectly, only a
user clicking buttons reveals the broken wiring.

`html_js_id_parity` cross-references every `#id` the JS hooks into via
`getElementById` or `querySelector('#…')` against every `id="…"` in
the HTML files. Phantom hooks are flagged.

## What every other layer says

| Layer | Verdict | Why it's silent |
|---|---|---|
| `js_syntax` | PASS | `node --check` — JS is valid. |
| `static_imports` | PASS | All `<script src>` / `<link href>` paths resolve. |
| `ast_brace_balance` | PASS | Braces balanced. |
| `interactivity` | PASS | 5 interactive HTML elements + 4 JS bindings — interactivity check counts presence, not correctness. |
| `css_completeness` | PASS | Real CSS rules. |
| **`html_js_id_parity`** | **FAIL** | JS hooks `#theme-toggle` + `#decrement-btn`, neither exists in any HTML file. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **eslint** | PASS | Single-file linter; no cross-file id awareness. |
| **eslint-plugin-html** | PARTIAL | Exists but rare in real configs; coverage of cross-file `getElementById` lookups is limited. |
| **HTML validator** | PASS | Both files are individually valid markup/JS. |
| **`node --check`** | PASS | JS is syntactically fine. |
| **Raw Claude critique** | UNRELIABLE | Small files: usually catches. Larger projects: misses. |
| **Manual QA** | FAIL | Catches on first click — but the validator is supposed to obviate manual QA for predictable bugs. |
| **Aegis** | **FAIL — html_js_id_parity** | The cross-file id parity scan catches in milliseconds. |

## Files

- `brief.json` — tip calculator with theme toggle and people-count buttons
- `input/index.html` — declares `id="theme-switch"` + `id="people-decrement"`
- `input/app.js` — hooks `#theme-toggle` + `#decrement-btn` (THE BUG)
- `input/styles.css` — real CSS (irrelevant to the bug, present so `css_completeness` doesn't skip)
- `expected.json` — what Aegis should report
