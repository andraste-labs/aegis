# Aegis

A deterministic validator for AI-generated code.

## Status

🚧 Private development. Public Apache 2.0 launch planned for **September 2026**.

⭐ Watch this repo to be notified at launch.

## What it does

Aegis runs a multi-layer pipeline against any code directory and reports whether the output is shippable. Today:

- **24 check layers** — 22 deterministic (AST, regex, build, test runners), 1 LLM-as-judge (design fidelity), 1 hybrid (feature coverage, with deterministic override).
- **Multi-stack** — Python, Node.js (TypeScript/JavaScript), and static HTML. Go and Rust are on the roadmap.
- **Reproducible** — `aegis-bench/` runs the same cohort on any machine, with the same results.

## Why it exists

AI coding tool adoption rose from 70% (2023) to 84% (2025). Trust in tool accuracy fell from 40% (2024) to 29% (2025). The industry settled for that trade-off. Aegis is for the minority who didn't.

## Roadmap

- **September 2026** — Apache 2.0 public release, full source
- **Q4 2026** — aegis-bench v2: 20+ cases, third-party baseline comparisons
- **2027** — Multi-language expansion (Go, Rust)

## Contact

[andrastelabs.com](https://andrastelabs.com) · github@andrastelabs.com

---

*Andraste Labs — building tools for the era of weighed code.*
