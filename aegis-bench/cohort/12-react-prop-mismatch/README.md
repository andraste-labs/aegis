# 12 — React prop name mismatch

**Category:** G — Semantic & runtime
**Stack:** Node.js (React 18 + TypeScript)
**Layer fired:** `react_prop_consistency` (deterministic; JSX call-site scan)
**Expected verdict:** `FAIL · react_prop_consistency · <CryptoCard crypto={…}> — declared prop is "coin"`

## What this case demonstrates

The brief asks for a crypto dashboard with three coin cards. The
generator declares the component correctly:

```tsx
// src/CryptoCard.tsx
export interface CryptoCardProps {
  coin: CryptoCurrency;
}

export function CryptoCard({ coin }: CryptoCardProps) {
  return <article>${coin.price.toFixed(2)}</article>;
}
```

…but the consumer passes a differently-named prop:

```tsx
// src/CryptoGrid.tsx
{SAMPLE.map((c) => (
  <CryptoCard key={c.symbol} crypto={c} />   // ← should be coin={c}
))}
```

At runtime, `CryptoCard` receives `coin` as `undefined` and crashes
on `coin.price.toFixed()`. `tsc` would catch this as **TS2322** if
the project had a `tsconfig.json`, but this generated codebase has
none (a real failure mode — agent generated a TS project without
the config file). The static `react_prop_consistency` layer catches
it anyway.

The layer walks every JSX open tag for capital-letter components:

1. Looks up the component's declared Props interface.
2. Parses the attribute names in the open tag.
3. Subtracts builtins (`key`, `ref`, `className`, `on*`, `data-*`,
   `aria-*`) and spread props (`{...rest}`).
4. Flags any remaining attributes not present in the declared Props.

## What every other layer says

| Layer | Verdict | Why it's silent |
|---|---|---|
| `node_deps_completeness` | PASS | All imports declared. |
| `named_import_consistency` | PASS | `CryptoCard`, `CryptoCurrency` are exported by their source files. |
| `import_case_consistency` | PASS | Casing matches. |
| `duplicate_type_declarations` | PASS | No type duplicates. |
| `ast_brace_balance` | PASS | Braces balanced. |
| `static_imports` | PASS | All relative paths resolve. |
| `npm_install` | PASS | Deps install cleanly. |
| `tsc` | SKIP | No tsconfig.json. (Tsc WOULD catch this, but the case demonstrates the static layer firing first.) |
| **`react_prop_consistency`** | **FAIL** | `<CryptoCard crypto={…}>` passes `crypto` but Props only declares `coin`. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **tsc (if tsconfig present)** | FAIL — TS2322 | The ground truth, but only fires when the project is configured to compile and the build runs. |
| **vanilla eslint** | PASS | Doesn't cross-reference component declarations. |
| **eslint-plugin-react** | PARTIAL | `react/prop-types` validates PropTypes runtime declarations, not TypeScript interfaces. |
| **Raw Claude critique** | UNRELIABLE | Spots the mismatch sometimes; often reads as "two different valid prop names for the same data". |
| **Manual QA** | FAIL | The component crashes on first render. |
| **Aegis** | **FAIL — react_prop_consistency** | Static cross-file JSX scan catches in milliseconds. |

## Why we ship this static layer instead of relying on tsc

tsc is in the pipeline (layer #21) and would catch the bug WHEN a
tsconfig is present. But three real failure modes work against tsc:

1. **No tsconfig** (this case). Generator builds a TS project but
   skips the config file. tsc is skipped, the bug ships.
2. **Slow signal**. tsc runs after npm_install; the rework loop has
   to wait 30+ seconds for the bug to surface.
3. **Buried output**. tsc emits hundreds of lines for a moderate
   project; the prop mismatch is one buried diagnostic among many.
   The rework agent's prompt is noisier than it needs to be.

The static `react_prop_consistency` layer fires in milliseconds, runs
without tsconfig, and surfaces one clean per-component message. That's
the moat.

## Files

- `brief.json` — crypto dashboard, three coin cards, dense layout
- `input/package.json` — React 18 + TS + Vite, but NO tsconfig.json
- `input/src/types.ts` — declares `CryptoCurrency`
- `input/src/CryptoCard.tsx` — declares `interface CryptoCardProps { coin }`
- `input/src/CryptoGrid.tsx` — passes `<CryptoCard crypto={…}>` (THE BUG)
- `input/src/App.tsx` — top-level wrapper
- `expected.json` — what Aegis should report
