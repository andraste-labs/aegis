# 17 — density / spacing-rhythm violation

**Category:** I — Design fidelity (LLM-judge dependent — no deterministic floor on this axis)
**Stack:** Static HTML + CSS
**Layer fired:** `design_fidelity` (KIND=hybrid; this case exercises the LLM-judge portion)
**Expected verdict:** `FAIL · design_fidelity · density_motion < 3 (spacious requested, compact delivered)`

> **LLM calibration status:** pending. The deterministic override does
> NOT fire on this case — palette is correct, fonts are imported and
> used, and the `editorial` philosophy has no forbidden-pattern entries.
> The FAIL relies entirely on the LLM judge reading the brief's
> `density: spacious` instruction and the CSS's 0.25-0.5rem
> tight-spacing pattern, and recognising the mismatch. Final scoring
> captured before public launch.

## What this case demonstrates

The brief asks for a magazine-style landing page with **explicit**
spacing language:

- `density: "spacious"`
- `spacing_scale: "spacious"`
- Notes: "generous whitespace, slow reading rhythm, vertical
  breathing room between sections"

The generated code honors palette and typography:

- Five required hexes — all present in `styles.css`.
- Playfair Display + Source Sans 3 — both `@import`-ed and used in
  `font-family` declarations.
- HTML semantics fine, copy fits the brand voice.

But the CSS ships SaaS-tight defaults:

```css
.container { gap: 0.5rem; }
.hero      { padding: 0.5rem 0; }
.value     { padding: 0.5rem 0; }
.value h2  { margin: 0 0 0.25rem 0; }
.cta       { padding: 0.375rem 0.75rem; }
```

For an editorial landing, that's wrong by an order of magnitude. The
brief asked for breathing room; the code delivers a dashboard.

## Why the deterministic override doesn't fire here

`design_fidelity`'s deterministic override only checks three things:

1. **Palette hexes** — are the brief's hex codes literally present in
   any form (`#hex`, `rgb()`, etc.)? Yes → palette **not** capped.
2. **Font families** — do the required font names appear in code?
   Yes → philosophy **not** capped on typography.
3. **Forbidden patterns per philosophy** — does the chosen philosophy
   have a forbidden-pattern entry? `editorial` does NOT (only
   `apple-flat`, `kenya-hara-minimalism`, `swiss-international`, and
   `brutalist` do). → philosophy **not** capped on this axis.

So none of the override paths apply. The case is **intentionally**
designed to leave the LLM's verdict standing — that's the point.
This is how Aegis ships honestly: the deterministic floor catches
what it can; the LLM catches the rest; the hybrid uses both.

## What the LLM judge is expected to see

| Dimension | Expected score | Reason |
|---|---|---|
| palette | 9/10 | All hexes present. |
| philosophy | 5-6/10 | Typography honored, but the spatial rhythm reads SaaS. |
| **density_motion** | **3-4/10** | CRITICAL: brief says spacious, code is compact. Below the `_MIN_DIMENSION_SCORE=3` threshold trips a weak-dimension FAIL even with high overall. |
| tone_microcopy | 8/10 | Copy fits the brand voice. |
| **overall** | **~6/10** | Borderline pass on overall; density_motion is the weakness. |

The LLM is the only check that can connect the brief's `spacious`
instruction to the CSS's `gap: 0.5rem` pattern. The deterministic
floor is silent because spacing isn't its job.

## What every other layer says

| Layer | Verdict | Why |
|---|---|---|
| `static_imports` | PASS | All `<link>` paths resolve. |
| `css_completeness` | PASS | Real CSS with rules + custom properties. |
| `ast_brace_balance` | PASS / SKIP | No JS to scan. |
| **`design_fidelity`** | **FAIL — LLM-driven** | density_motion below threshold. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **stylelint** | PASS | No rule for "compare spacing to brief". |
| **Other static design linters** | PASS | None of them know the brief. |
| **Pure LLM judge** | LIKELY FAIL if specific | The LLM CAN read brief + CSS and notice. Whether it does depends on prompt specificity — and Aegis's prompt is specifically tuned to look for this. |
| **Manual design review** | FAIL | A designer opens the page and immediately knows. But humans don't run on every PR. |

## Files

- `brief.json` — magazine-style landing with explicit spacious-density requirement
- `input/index.html` — semantically clean editorial markup (hero, two value props, quote, CTA)
- `input/styles.css` — palette + fonts honored, density TIGHT (THE BUG)
- `expected.json` — documented expected verdict with explicit LLM-dependence note
