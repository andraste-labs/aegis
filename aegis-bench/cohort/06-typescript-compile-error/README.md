# 06 — typescript compile error

**Category:** E — Build failures
**Stack:** Node.js (React 18 + TypeScript + Vite)
**Layer fired:** `tsc` (deterministic; subprocess `npx tsc --noEmit`)
**Expected verdict:** `FAIL · tsc · TS2339 Property 'fullName' does not exist on type 'UserProfile'`

## What this case demonstrates

The brief asks for a React + TypeScript component that displays a user
profile. The generated code looks clean at a glance — interface, props,
type-safe JSX — but there's a quiet shape mismatch:

```ts
// src/types.ts
export interface UserProfile {
  id: string;
  name: string;        // ← declared as `name`
  email: string;
  joinedAt: string;
}
```

```tsx
// src/UserCard.tsx
<h2>{user.fullName}</h2>   // ← code reads `fullName`
```

The type declares `name`; the component reads `fullName`. Both files
parse cleanly. `npm install` completes without issue (deps are all
real, peer-resolvable versions). The bug only surfaces when `tsc`
walks the AST, looks up `fullName` on `UserProfile`, and reports
**TS2339**.

This is one level deeper than case 05: install works, statics pass,
the failure is in semantic type-checking. It's the case that justifies
running the real TypeScript compiler in the validator pipeline rather
than trusting bundled type-checks from other tooling.

## What every other layer says

Aegis runs ~21 layers against this input before reaching `tsc`. None
of them fire — and they shouldn't. Each verifies a different invariant:

| Layer | Verdict | Why it's silent |
|---|---|---|
| `node_deps_completeness` | PASS | All imports (`react`, `react-dom/client`, `./types`, `./UserCard`) are declared. |
| `react_prop_consistency` | PASS | `<UserCard user={…} />` matches the declared `UserCardProps`. The mismatch is INSIDE the component, not at the call site. |
| `named_import_consistency` | PASS | `import type { UserProfile } from './types'` — `UserProfile` IS exported. |
| `import_case_consistency` | PASS | All paths match disk casing. |
| `static_imports` | PASS | All relative imports resolve. |
| `npm_install` | PASS | Deps install cleanly. |
| **`tsc`** | **FAIL — TS2339** | Compiler walks property access. `fullName` ∉ `UserProfile`. |

Static checks have a clear ceiling. Past that ceiling, the actual
compiler is the only check left — which is why it's in the pipeline.

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **eslint (no plugins)** | PASS | Plain eslint doesn't run the TS checker. |
| **@typescript-eslint** | DEPENDS | Catches only with type-aware rules (`@typescript-eslint/parser` + `parserOptions.project`); most teams don't enable type-aware linting by default. |
| **Raw Claude critique** | UNRELIABLE | Sometimes catches on careful read; LLM judgment of types-at-distance is inconsistent. |
| **GPT-4 critique** | Same as above. |
| **`tsc --noEmit`** | **FAIL — TS2339** | The ground truth. This is what Aegis runs. |

## The bug, in one line

`UserCard.tsx:15` reads `user.fullName` — a field that doesn't exist
on the `UserProfile` interface declared in `types.ts`.

## Files

- `brief.json` — project intent and stack
- `input/package.json` — React 18 + TS, lockfile-free
- `input/tsconfig.json` — strict mode, no-emit, JSX `react-jsx`
- `input/index.html` — Vite entry
- `input/src/main.tsx` — React root mount
- `input/src/App.tsx` — sample usage (passes the test props)
- `input/src/types.ts` — declares `UserProfile` with `name` field
- `input/src/UserCard.tsx` — reads `user.fullName` (THE BUG)
- `expected.json` — what Aegis should report
