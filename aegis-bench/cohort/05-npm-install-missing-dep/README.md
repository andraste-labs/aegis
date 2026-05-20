# 05 — npm install missing dep

**Category:** E — Build failures
**Stack:** Node.js (React 18 + Vite)
**Layer fired:** `build_install` (deterministic; subprocess `npm install`)
**Expected verdict:** `FAIL · build_install · ENOTFOUND react@99.0.0`

## What this case demonstrates

The brief describes a simple React todo app. The generated code itself
is fine — clean functional components, correct hook usage, idiomatic
React 18. The only problem is in `package.json`:

```json
"dependencies": {
  "react": "99.0.0",
  ...
}
```

Version `99.0.0` of React doesn't exist on the npm registry (current
major is 18). When the validator runs `npm install --ignore-scripts`,
the resolution step fails with `ENOTFOUND` (or `ETARGET`, depending on
npm version). The install never completes, so all downstream layers
(`build_compile`, `test_run`, `design_fidelity`) are skipped — Aegis
short-circuits because there's no built project to validate.

This is the simplest case in the build-failure category. It exists to
demonstrate that **Aegis runs actual `npm install`** rather than just
parsing `package.json`.

## Why baselines miss this

| Tool | Verdict | Why |
|---|---|---|
| **eslint** | PASS | eslint reads `.js` / `.jsx` source files, not `package.json` registry resolution. |
| **Raw Claude critique** | "Looks fine, maybe flag the unusual version" | Reads code but does not perform install. May notice `99.0.0` is unusual; cannot verify the package exists. |
| **GPT-4 critique** | Same | Reads code; doesn't run install. |
| **`npm audit`** | N/A (requires installed packages) | Operates on `package-lock.json` after install. Can't run until install succeeds. |
| **`npm outdated`** | N/A (requires installed packages) | Same. |
| **Aegis (this case)** | **FAIL — ENOTFOUND** | Runs `npm install --ignore-scripts`; catches the missing version at registry resolution. |

This is the value proposition for layer 20 (the `npm install`
subprocess) — no amount of static analysis substitutes for actually
running the install.

## Adversarial variant (not part of this case)

A more adversarial version of this failure would use a typosquatted
package name (`reactt`, `react-doom`) that resolves to a real malicious
package. That's covered separately by **case 13 — malicious-preinstall-script**,
which exercises the `--ignore-scripts` flag.

This case (05) stays narrow: the package is missing, not malicious.
The job is to verify Aegis runs `npm install` and reports the failure
honestly, rather than passing on parsing-only checks.

## Files

- `brief.json` — DesignDNA + project intent
- `input/package.json` — the broken manifest with `react@99.0.0`
- `input/index.html` — entry point
- `input/src/index.jsx` — React root mount
- `input/src/App.jsx` — todo list component (clean, no issues)
- `expected.json` — what Aegis should report
