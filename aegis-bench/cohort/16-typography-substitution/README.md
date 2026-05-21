# 16 — typography substitution (Lora + Inter → system-ui)

**Category:** I — Design fidelity (hybrid: LLM judge + deterministic override)
**Stack:** Static HTML + CSS
**Layer fired:** `design_fidelity` (KIND=hybrid; deterministic override caps LLM)
**Expected verdict:** `FAIL · design_fidelity · forced_fail · philosophy 4/10 (Lora + Inter NOT FOUND)`

> **LLM calibration status:** the layer's final numeric scores are
> documented as **expected** here; final capture against `claude-opus-4-7`
> happens before public launch. The deterministic override portion is
> independently verifiable: scan `styles.css` for `Lora` and `Inter` —
> neither appears. Override fires regardless of the LLM's score.

## What this case demonstrates

The brief asks for an editorial blog with quiet, considered typography:
**Lora** for headings, **Inter** for body. The brief explicitly says
"this brand's voice IS its typography".

The generated code:

- Honors the palette perfectly (every required hex appears in styles.css).
- Honors the layout (masthead + three cards + footer, spacious padding,
  thin divider).
- **Drops typography entirely** — every `font-family` declaration is
  `system-ui, sans-serif`. Lora and Inter never appear in the code
  (no `@import` URL, no `<link>` tag, no `font-family` reference).

A pure LLM judge — given the rendered HTML/CSS — would tend to score
this 7-8 / 10. The palette IS right, the layout IS clean, and reading
plain text in the prompt doesn't expose "wrong font" as starkly as
"wrong color". The LLM rubber-stamps.

The `design_fidelity` layer's **deterministic override** runs after
the LLM verdict:

1. For each required palette hex, search the code blob for the literal
   `#hex`, `#HEX`, `hex`, `HEX`, `rgb(...)`, and `rgba(...)` variants.
   Cap palette dimension only if ≥ half are missing. → **palette OK**.
2. For each required font name, search the code blob (case-insensitive)
   for the family name and its first word. Cap philosophy dimension if
   ALL required fonts are missing. → **philosophy CAPPED to 4/10**.
3. Set `forced_fail = true`. Set the missing-items list to surface the
   override.

`forced_fail` trumps numeric thresholds — even if the LLM scored
overall 10/10, the result is FAIL because the deterministic check
proved typography was substituted.

This is the cleanest demonstration of the moat: pure-LLM judging is
not validation. A senior reviewer comparing pure-LLM vs Aegis on this
case sees the difference immediately.

## What every other layer says

| Layer | Verdict | Why |
|---|---|---|
| `js_syntax` | SKIP | No JS. |
| `static_imports` | PASS | All `<link>` paths resolve. |
| `css_completeness` | PASS | Real CSS with rules + custom properties. |
| `ast_brace_balance` | PASS | (No JS to scan.) |
| **`design_fidelity`** | **FAIL — forced_fail** | LLM scores high; deterministic font check overrides. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **Pure LLM judge** | PASS (7-8/10) | Palette is right, layout is clean, LLM reads text not pixels. |
| **stylelint** | PARTIAL | Has rules for font-family validity, no presets compare to a brief. |
| **eslint, ruff, tsc** | N/A | Not their domain. |
| **Manual design review** | FAIL | A designer opens the page and instantly knows. But humans don't run on every PR. |
| **Aegis (LLM + deterministic override)** | **FAIL — forced_fail** | Font search has the final word; LLM cannot rubber-stamp. |

## Files

- `brief.json` — editorial blog, palette + Lora/Inter typography
- `input/index.html` — masthead + 3 article cards + footer
- `input/styles.css` — correct palette hexes, BUT `font-family: system-ui` everywhere (THE BUG)
- `expected.json` — documented expected verdict with deterministic override detail
