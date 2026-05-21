---
name: Bug report
about: Aegis gave the wrong verdict or crashed on valid input
title: '[Bug] '
labels: bug, needs-triage
assignees: ''
---

## What happened

A clear description of what Aegis did versus what you expected.

## Reproduction

Smallest possible failing case. Paste the directory contents (or attach
a zip) and the exact command you ran.

```bash
# Command:
aegis check ./<your-test-case>

# What Aegis output:
[paste output here]

# What you expected:
[describe expected output]
```

## Layer

If you know which layer fired (or should have fired), name it:

- [ ] Syntax / AST
- [ ] Imports
- [ ] Semantic
- [ ] Build (npm / pytest / etc.)
- [ ] Tests
- [ ] Design fidelity (LLM judge)
- [ ] Feature coverage (hybrid)
- [ ] Other / not sure

## Environment

- Aegis version: `aegis --version`
- OS:
- Python version (if running from source):
- Node.js / npm version (if relevant):

## Is the failing input in a public repo we can clone?

If yes, link. If not, the smallest synthetic reproduction is fine.

## Anything else

Logs, screenshots, theories about the root cause.
