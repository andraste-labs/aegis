# Aegis

A deterministic validator for AI-generated code. Apache 2.0.

> 🚧 **Public source release: September 2026.** Star this repo or
> [watch for releases](https://github.com/andraste-labs/aegis/releases)
> to be notified at launch.

## What it does

Aegis runs a multi-layer pipeline against a directory of AI-generated code
and reports whether it's shippable.

- **24 check layers** — 22 deterministic (AST, regex, build, test runners),
  1 LLM-as-judge (design fidelity), 1 hybrid (feature coverage with
  deterministic override).
- **Multi-stack** — Python, Node.js (TypeScript / JavaScript), and static
  HTML in the first release. Go and Rust are on the roadmap.
- **Honest FAILED** — if the layers can't be made green within the rework
  budget, Aegis writes a structured failure report instead of marking
  the output green anyway.

## Why it exists

AI coding tool adoption rose from 70% (2023) to 84% (2025). Trust in
tool accuracy fell from 40% (2024) to 29% (2025). The industry settled
for that trade-off. Aegis is for the minority who didn't.

## How it works (preview)

```bash
# Single command, any directory:
aegis check ./my-buggy-ai-output

[Aegis 24-layer pipeline]
✓ Syntax (AST parse)               0.3s
✓ Imports resolved                 0.5s
✗ Semantic — MISSING_HOOK_HANDLER  1.2s
  → Rework triggered
✓ Semantic (after rework)          4.1s
✓ Build (npm install + build)      3.2s
✓ Tests pass                       5.8s
✓ Design fidelity (LLM judge)      2.1s

[Total: 17.2s · 1 error found · 1 auto-fixed · SHIP ✓]
```

## Roadmap

| Date | Milestone |
|---|---|
| **September 2026** | **Apache 2.0 public release — full source** |
| Q4 2026 | aegis-bench v2: 20+ cohort cases, third-party baseline comparisons |
| 2027 | Go and Rust stack support |
| 2027+ | "Aegis-Verified" badge program — open standard |

## Reproducible benchmark

Once released, the `aegis-bench/` suite will let any developer reproduce
our results on their own machine:

```bash
git clone https://github.com/andraste-labs/aegis
cd aegis/aegis-bench
python scripts/run_aegis.py
```

The output is the evidence. No screenshots, no demos — runnable code.

## Contributing

We're not accepting contributions until the public release in September 2026.
After launch, see [CONTRIBUTING.md](./CONTRIBUTING.md) for how to help.

If you'd like to be a **Founding Architect** (first 100 contributors after
the public release), star this repo and watch for the launch announcement.

## License

Aegis is released under the [Apache License 2.0](./LICENSE). The license
applies to all repository contents from this commit forward.

## About

Aegis is the open infrastructure layer of [Andraste Labs](https://andrastelabs.com) —
a lab building tools for the era of weighed code. Team-AI is the first
product built on top.

- 🌐 [andrastelabs.com](https://andrastelabs.com)
- 🛡️ [aegis.andrastelabs.com](https://aegis.andrastelabs.com)
- ✉️ [github@andrastelabs.com](mailto:github@andrastelabs.com)

---

*Andraste Labs · İstanbul · Delaware C-Corp + TR subsidiary*
