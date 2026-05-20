# 13 — npm `--ignore-scripts` supply-chain guard

**Category:** H — Security & supply chain
**Stack:** Node.js (vanilla)
**Layer fired:** `npm_install` runs WITH `--ignore-scripts`
**Expected verdict:** `PASS · npm_install · side-effect file absent`

## What this case demonstrates

This is a **positive** case — a PASS that proves the security stance.
The package.json declares two hostile lifecycle hooks:

```json
{
  "scripts": {
    "preinstall":  "node -e \"require('fs').writeFileSync('PWNED.txt', ...); console.log('SECURITY-LEAK: preinstall executed')\"",
    "postinstall": "node -e \"require('fs').writeFileSync('PWNED-POST.txt', ...)\""
  }
}
```

If Aegis ran plain `npm install`, both hooks would execute. `PWNED.txt`
and `PWNED-POST.txt` would appear in the project directory, and the
`SECURITY-LEAK` line would appear in stdout. In a real supply-chain
attack, these hooks would exfiltrate `.env` files, pull and execute
remote binaries, or write to the user's home directory.

Aegis hardcodes `--ignore-scripts` in the `npm_install` layer
([aegis/checks/npm_install.py](../../../aegis/checks/npm_install.py)).
The install completes — exit 0 — but **the lifecycle hooks do not run**.
After validation:

| Side effect | Plain `npm install` | Aegis `npm install --ignore-scripts` |
|---|---|---|
| `PWNED.txt` exists | Yes | **No** |
| `PWNED-POST.txt` exists | Yes | **No** |
| `SECURITY-LEAK` in stdout | Yes | **No** |
| Validator verdict | PASS | **PASS** |

The verdict is identical (PASS in both cases) — that's the trap. A
shallow security audit that only checks the verdict misses the
difference. The bench verifies the **side-effect absence** as the real
signal.

## Bench verification

The case's `expected.json` includes a `side_effect_check` field
declaring which files must NOT exist after the validator runs.
The bench runner is responsible for checking these files post-run.

```json
"side_effect_check": {
  "file_must_not_exist": "PWNED.txt"
}
```

## What every other layer says

| Layer | Verdict | Why |
|---|---|---|
| `js_syntax` | PASS | `index.js` is a one-liner; trivially valid. |
| `node_deps_completeness` | PASS | No bare imports. |
| `static_imports` | PASS | No relative imports. |
| **`npm_install`** | **PASS** | Install completes; preinstall + postinstall skipped via `--ignore-scripts`. |

## Why baselines miss the security implication

| Tool | Verdict | Why |
|---|---|---|
| **Plain `npm install`** | PASS, but PWNED files created | Lifecycle hooks run by default. |
| **`yarn install`** | Same as above. | Hooks run by default. |
| **`pnpm install`** | Same. | Hooks run by default. |
| **GitHub Actions default** | Hooks run. | CI pipelines typically don't pass `--ignore-scripts`. |
| **`npm audit`** | Catches some known-bad versions | But doesn't catch hostile lifecycle hooks in fresh packages. |
| **Aegis** | **PASS, no side effects** | `--ignore-scripts` is non-negotiable in the `npm_install` layer source. |

## Files

- `brief.json` — trivial hello script with security-audit notes
- `input/package.json` — declares preinstall + postinstall hooks (THE PAYLOAD)
- `input/index.js` — one-line console.log
- `expected.json` — passed=true plus the side-effect-absent check
