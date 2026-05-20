# 09 — node deps missing

**Category:** F — Test / dependency failures (case 09 was originally
planned as a jest snapshot mismatch; pivoted to exercise the
`node_deps_completeness` static layer instead, since Aegis does not
currently run jest.)
**Stack:** Node.js (vanilla ESM script)
**Layer fired:** `node_deps_completeness` (deterministic; static AST scan)
**Expected verdict:** `FAIL · node_deps_completeness · axios + date-fns not declared`

## What this case demonstrates

The brief asks for a small fetch script. The generated code imports
two third-party libraries:

```js
// src/fetch.js
import axios from 'axios';
import { format } from 'date-fns';
```

But `package.json` declares zero dependencies:

```json
{
  "name": "fetcher",
  "type": "module",
  "scripts": { "start": "node src/fetch.js" },
  "dependencies": {}
}
```

`node_deps_completeness` walks every JS/TS source, extracts every
bare-specifier import, normalises scoped packages (`@scope/pkg`) and
subpath imports (`lodash/fp`), and reports anything not declared in
`dependencies` / `devDependencies` / `peerDependencies` /
`optionalDependencies`. Both `axios` and `date-fns` surface as missing.

The catch happens in milliseconds, before `npm install` ever runs.
That's the moat: a static AST scan that obviates the slow,
network-dependent subprocess for this class of bug.

## Why this case was pivoted

The original case 09 plan was a jest snapshot mismatch — same category
(test failures), demonstrating the value of running the test suite.
But Aegis's extracted layer set ends at `pytest`; there is no `jest`
or `vitest` layer in the v1 release. Rather than build a layer just
for the bench, we pivoted case 09 to exercise a layer Aegis actually
ships (`node_deps_completeness`), keeping the bench honest.

This is a representative LLM bug: the agent writes `import axios from
'axios'` because that's what real code looks like, but forgets to
add `axios` to `package.json`. The runtime would fail with
`ERR_MODULE_NOT_FOUND` — but only after install, only when the script
actually runs. Catching it statically is the bench's whole point.

## What every other layer says

| Layer | Verdict | Why it's silent |
|---|---|---|
| `js_syntax` | PASS | `node --check src/fetch.js` — the file IS valid JS. |
| `static_imports` | PASS | No relative imports to resolve. |
| `named_import_consistency` | PASS | No relative-named-imports to verify. |
| `import_case_consistency` | PASS | No path casing to check. |
| `ast_brace_balance` | PASS | Braces are balanced. |
| `npm_install` | PASS | `dependencies: {}` is technically valid; npm has nothing to install. (Runtime would crash, but install itself succeeds.) |
| **`node_deps_completeness`** | **FAIL** | Imports use axios + date-fns; neither is declared. |

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **eslint (vanilla)** | PASS | Doesn't know about `package.json`. |
| **eslint-plugin-import (no-extraneous-dependencies rule)** | FAIL | Catches — IF the plugin is installed AND the rule is enabled AND `package.json` resolution is configured. Most teams don't have it. |
| **tsc** | N/A | No tsconfig; this is plain JS. |
| **`npm install`** | PASS | Nothing to install. |
| **`npm start` (runtime)** | FAIL | `ERR_MODULE_NOT_FOUND` — but only at runtime. |
| **Raw Claude critique** | UNRELIABLE | May or may not flag the missing deps. |
| **Aegis** | **FAIL — node_deps_completeness** | Catches in milliseconds via the static AST scan. |

## Files

- `brief.json` — project intent and stack
- `input/package.json` — declares the script entrypoint but `dependencies: {}`
- `input/src/fetch.js` — imports `axios` + `date-fns` (THE BUG: neither declared)
- `expected.json` — what Aegis should report
