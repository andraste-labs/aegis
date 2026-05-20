# Contributing to Aegis

Thank you for considering a contribution.

> 🚧 **Pre-launch notice (May 2026):** The public source release is planned
> for **September 2026**. We are not accepting code contributions, bug
> reports, or feature requests until then. This document describes how
> contribution will work *after* launch, so we have it in place from day one.

## Code of Conduct

Participation in this project is governed by our
[Code of Conduct](./CODE_OF_CONDUCT.md). Read it before contributing.

## How you can help (post-launch)

### 1. Run the bench, share results

`aegis-bench/` is a reproducible test cohort. Run it against your own
AI-generated code and open a discussion (or PR) with what you found.
Real-world failure modes drive new check layers.

### 2. Add a check layer

The validator has 24 layers today; some are simple AST checks, some are
deterministic build/test runners, one is an LLM judge with a deterministic
override. New layers are welcome if they:

- **Are deterministic where possible.** LLM judgment is allowed only when
  no deterministic signal is available, and only with a deterministic
  override that can fail the layer regardless of the LLM's vote.
- **Have a bench case.** Every new layer ships with a cohort case in
  `aegis-bench/cohort/` that demonstrates the failure it catches.
- **Are typed.** Failures are tagged `deterministic`, `hybrid`, or
  `llm_judge` so the rework dispatcher knows how to prioritize them.

### 3. Add a stack

Today: Python, Node.js, static HTML. Roadmap: Go, Rust.

If you want to add a stack, the requirements are:

- A `_detect_<stack>()` function that recognizes the stack from directory
  contents (manifests, dotfiles, language-specific markers).
- A `_validate_<stack>()` pipeline that runs build + tests in a sandboxed
  subprocess with the standard env-scrub and `--ignore-scripts` defaults.
- A bench cohort case in `aegis-bench/cohort/` for the new stack.

### 4. Improve the docs

`METHODOLOGY.md` and `docs/` are first-class deliverables. Clarity
improvements, examples, and translation contributions are welcome.

## What we won't accept

- **Layers that add LLM judgment without deterministic override.** If a
  check can't fail without the model agreeing, it isn't a check — it's
  a vibe. We don't ship vibes.
- **Stack support without a bench cohort case.** Untested stack support
  is worse than no support.
- **"Refactors" without a reproducible problem.** Style preferences are
  fine; refactors without a measurable improvement are not.

## Workflow

After September 2026:

1. **Discuss before coding.** Open an issue describing the problem before
   writing a PR. Many "improvements" turn out to be opinion.
2. **Branch from `main`.** Name the branch `<type>/<short-description>`,
   e.g., `feat/go-stack-validator` or `fix/regex-import-resolution`.
3. **Keep PRs focused.** One layer per PR, one bug fix per PR. Mixed PRs
   take longer to review and to revert.
4. **Run `aegis-bench`.** CI runs it; you should run it locally too.
5. **Write a test.** New behavior needs a test. Bench cohort cases count.
6. **Sign your commits.** Use `git commit -s` to add a DCO line.

## Founding Architects

The first 100 contributors with merged code will be recognized as
**Founding Architects** in the README of the first major release. This
is a permanent record — not a perk that can be revoked. If you want
your name in the list, see issue #1 (opened at launch).

## License

By contributing, you agree that your contributions will be licensed
under the [Apache License 2.0](./LICENSE).

## Questions

Open a [discussion](https://github.com/andraste-labs/aegis/discussions)
after launch, or email [github@andrastelabs.com](mailto:github@andrastelabs.com)
in the interim.
