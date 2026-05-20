# Aegis Roadmap

This document is a planning record. Dates are targets, not commitments
to specific calendar days. Where they slip, we'll update this file with
the new target and the reason.

## September 2026 — Public source release (Apache 2.0) 🎯

The first public release will include:

- The full validator pipeline (24 check layers as of release date)
- `aegis-bench/` reproducible benchmark cohort with 20+ cases
- `aegis-bench/scripts/run_aegis.py` — single-command bench runner
- `aegis-bench/baselines/` — comparison runs against eslint, mypy,
  GPT-4 critique, etc., so reviewers can see what Aegis catches that
  alternatives miss
- `METHODOLOGY.md` — how layers are categorized (deterministic / hybrid /
  llm-judge), how rework dispatch works, how the honest-FAILED contract
  is upheld
- Quick-start docs for Python, Node.js (TS/JS), and static HTML projects

The release will be tagged `v1.0.0` and announced via:

- A blog post on [andrastelabs.com](https://andrastelabs.com)
- A Show HN submission to Hacker News
- A coordinated post to the relevant subreddits (r/programming,
  r/ExperiencedDevs)
- Announcement on the Andraste Labs X account ([@andrastelabs](https://x.com/andrastelabs))

## Q4 2026 — aegis-bench v2

The cohort grows from 20 cases at launch to ≥40, covering:

- More failure modes (off-by-one logic errors, async race conditions,
  resource leaks)
- Larger projects (current cohort is intentionally small; v2 adds
  full-app validation cases)
- Multi-language project cases (Python backend + React frontend in
  one cohort entry)

We expect third-party reviewers and contributors to drive most of v2.
Cases submitted via PR with reproducible failure outputs will be
accepted on the merits.

## 2027 — Stack expansion

The first release supports Python, Node.js (TypeScript / JavaScript),
and static HTML. The 2027 roadmap adds:

- **Go** — `go build`, `go test`, `go vet`, gosec
- **Rust** — `cargo build`, `cargo test`, `cargo clippy`

We are *not* planning to add Java, C#, Ruby, or PHP at this time. If
demand from contributors justifies them, we'll reconsider — but
adding a stack means committing to maintaining its validator pipeline
indefinitely, and we'd rather do 5 stacks well than 15 superficially.

## 2027+ — Aegis-Verified standard

Once Aegis is stable and the bench is broadly reproduced, we plan to
publish an "Aegis-Verified" specification: an open standard that any
project (not just Aegis itself) can use to claim its output meets
the bar.

This is the long-game thesis. The standard is more durable than the
implementation. We want Aegis-the-tool to be excellent; we want
Aegis-Verified-the-standard to outlive Aegis-the-tool.

## What's *not* on the roadmap

We get asked about these. We don't plan to do them:

- **A hosted SaaS version of Aegis.** Aegis is a local CLI by design.
  If you want a hosted multi-agent code generation product, see
  [Team-AI](https://team-ai.andrastelabs.com).
- **A VS Code / IDE plugin** in v1. Maybe later. We want the core
  validator to stabilize before adding integration surface.
- **A commercial enterprise edition.** The validator is and will
  remain Apache 2.0. Andraste Labs' commercial offering is the
  multi-agent product (Team-AI), not Aegis.
- **Replacing the rework loop with autonomous "agentic" exploration.**
  The deterministic rework dispatcher is a feature, not a limitation.

## Updates to this document

This roadmap is updated when:

- A milestone ships
- A target date slips by more than 30 days
- The scope of an upcoming milestone changes
- We decide to add or remove an item from the "not on the roadmap" list

The change history is the git log of this file. Read it.
