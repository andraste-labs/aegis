# 14 — duplicate `Coin` type, conflicting shapes

**Category:** H — Cross-file consistency
**Stack:** Node.js (React 18 + TypeScript)
**Layer fired:** `duplicate_type_declarations` (deterministic; cross-file regex + member parse)
**Expected verdict:** `FAIL · duplicate_type_declarations · 2 shapes for "Coin"`

## What this case demonstrates

The brief asks for a portfolio page that lists three coins with
symbol, name, price, and 24h change. The canonical type is declared
once in `src/types.ts`:

```ts
// src/types.ts (canonical)
export interface Coin {
  id: string;
  symbol: string;
  name: string;
  price: number;
  change_24h: number;
}
```

But a second file silently redeclares `Coin` with a totally different
shape:

```ts
// src/components/CoinRow.tsx (LOCAL redeclaration — THE BUG)
interface Coin {
  name: string;
  value: number;
}
```

The consumer (`App.tsx`) loads the canonical `Coin[]` from the API
and passes each one to `CoinRow`. `CoinRow` uses its **local** Coin
type, which only knows `name` and `value`. The symbol, price, and
change_24h fields are silently dropped — the UI renders blank cells
where prices should be.

`tsc TS2300` would catch this **only if both declarations were in the
same scope**. Different files = different scopes = both compile. The
bug ships green through every static check except this one.

`duplicate_type_declarations` walks every `interface X { ... }` and
`type X = { ... }`, groups by name, and flags any name with ≥2
distinct member-sets across different files. TS interface merging
(same shape, different files) is intentionally allowed.

## What every other layer says

| Layer | Verdict | Why it's silent |
|---|---|---|
| `node_deps_completeness` | PASS | Deps fine. |
| `named_import_consistency` | PASS | `import type { Coin } from './types'` resolves. |
| `import_case_consistency` | PASS | Casing matches. |
| `react_prop_consistency` | PASS | `<CoinRow coin={c} />` matches `CoinRowProps`. |
| `static_imports` | PASS | All paths resolve. |
| `npm_install` | PASS | Deps install. |
| `tsc` | SKIP | No tsconfig.json (intentional — see case 12 for why this happens). |
| **`duplicate_type_declarations`** | **FAIL** | `Coin` has 2 distinct shapes across 2 files; neither file imports the other's. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **tsc TS2300** | PASS | Same-scope dupes only. Different files = different scopes. |
| **eslint** | PASS | No standard rule for cross-file type-shape divergence. |
| **eslint-plugin-import** | PASS | Tracks imports, not local type duplications. |
| **Raw Claude critique** | UNRELIABLE | Sometimes reads as "careful local typing"; misses the divergence. |
| **Manual QA** | FAIL | User sees blank cells — but the form looks functional. Easy to miss in code review. |

## Files

- `brief.json` — portfolio page expecting full Coin shape
- `input/package.json` — React 18 + TS deps
- `input/src/types.ts` — canonical `interface Coin { id, symbol, name, price, change_24h }`
- `input/src/api.ts` — returns `Coin[]` (the full shape) from a fixture
- `input/src/components/CoinRow.tsx` — REDECLARES `Coin` with `{ name, value }` (THE BUG)
- `input/src/App.tsx` — passes canonical coins to CoinRow (silently drops fields)
- `expected.json` — what Aegis should report
