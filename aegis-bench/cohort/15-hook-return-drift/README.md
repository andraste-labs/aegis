# 15 — `useCoins` return drift vs Dashboard destructure

**Category:** H — Cross-file consistency
**Stack:** Node.js (React 18 + TypeScript)
**Layer fired:** `hook_destructure_consistency` (deterministic; AST-walk hook + consumer)
**Expected verdict:** `FAIL · hook_destructure_consistency · useCoins missing 'lastUpdated'`

## What this case demonstrates

The brief asks for a `useCoins` hook that exposes the coin list, an
`isLoading` state, AND a `lastUpdated` timestamp. The implementation
delivers only the first two:

```ts
// src/hooks/useCoins.ts
export function useCoins() {
  // ...
  return { coins, isLoading };       // ← missing lastUpdated
}
```

The Dashboard consumes the hook expecting all three:

```tsx
// src/Dashboard.tsx (THE CRASH)
const { coins, isLoading, lastUpdated } = useCoins();   // lastUpdated → undefined
// ...
<p>Last updated: {formatDate(lastUpdated)}</p>         // crashes on .toLocaleString()
```

At runtime, `lastUpdated` is `undefined`. `formatDate(undefined)`
calls `.toLocaleString()` on `undefined` → `TypeError: Cannot read
properties of undefined`. The page first renders fine, then crashes
when the data loads and Dashboard switches out of the loading state.

`hook_destructure_consistency` walks every `function useX() { ... }`
and `const useX = (...) => { ... }` (supports concise arrows, block
arrows, traditional functions), extracts the LAST top-level `return
{ ... }` literal's keys, then scans `const {...} = useX()` consumers
and flags any destructured name not in the returned shape. Hooks
whose return shape can't be extracted confidently (spread,
conditional returns, computed keys) are dropped from the audit —
silence beats false positives.

## What every other layer says

| Layer | Verdict | Why it's silent |
|---|---|---|
| `node_deps_completeness` | PASS | Deps fine. |
| `react_prop_consistency` | PASS | No JSX prop mismatch. |
| `named_import_consistency` | PASS | `useCoins` is exported. |
| `static_imports` | PASS | All paths resolve. |
| `duplicate_type_declarations` | PASS | No type dupes. |
| `tsc` | SKIP | No tsconfig.json (case ships without one — real failure mode). |
| **`hook_destructure_consistency`** | **FAIL** | useCoins returns {coins, isLoading}; Dashboard destructures lastUpdated. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **tsc** | PARTIAL | Would catch IF useCoins had an explicit return type annotation. Agent code rarely declares one — tsc infers from the literal and lets the consumer destructure anything. |
| **eslint-plugin-react-hooks** | PASS | Existing rules (exhaustive-deps, rules-of-hooks) don't validate hook return shape vs. consumer destructure. |
| **Raw Claude critique** | UNRELIABLE | Catches in small files; misses cross-file return drift. |
| **Manual QA** | FAIL | User sees the page crash after the loading state ends. Easy to miss in code review because the static read of both files looks fine in isolation. |

## Why this layer matters

Hook return drift is one of the most common React bugs in
agent-generated code — the hook author and the consumer author edited
the same conceptual surface at different times, and the LLM rarely
notices the divergence at write time. The static check fires in
milliseconds and surfaces a clean per-hook report:

> `useCoins() returns {coins, isLoading} but consumer destructures missing field(s): ['lastUpdated']`

Compared to the alternative (waiting until QA clicks through and the
page crashes), this is the rework loop's cleanest possible signal.

## Files

- `brief.json` — Coin Dashboard expecting coins, isLoading, lastUpdated
- `input/package.json` — React 18 + TS deps
- `input/src/hooks/useCoins.ts` — returns only `{ coins, isLoading }` (THE BUG)
- `input/src/Dashboard.tsx` — destructures `{ coins, isLoading, lastUpdated }`
- `input/src/App.tsx` — top-level wrapper
- `expected.json` — what Aegis should report
