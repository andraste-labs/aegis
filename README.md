# Aegis

A deterministic validator for AI-generated code. Apache 2.0.

## What it does

`aegis check ./path` runs a 24-layer pipeline against a directory of
code and reports whether the validation passes. Layers cover AST
parsing, import resolution, cross-file consistency, package install,
type check, test execution, design-brief fidelity, and feature
coverage. 22 layers are deterministic (no model call); 1 is LLM-judge;
1 is hybrid (LLM verdict with a deterministic override).

## Install

```
pip install aegis-validator
```

Anthropic SDK is an optional extra for the LLM-using layers:

```
pip install aegis-validator[anthropic]
```

## Quick start

```
aegis check ./my-code                          # deterministic + LLM
aegis check ./my-code --no-llm                 # deterministic only
aegis check ./my-code --brief brief.json       # include design / feature layers
aegis check ./my-code --json report.json       # machine-readable report
aegis check ./my-code --exit-on-fail           # exit 1 on FAIL
```

The LLM-using layers (`design_fidelity`, `feature_coverage`) skip
unless an `ANTHROPIC_API_KEY` is set and a `brief.json` is supplied.

## Layers

See [`docs/LAYER_INDEX.md`](./docs/LAYER_INDEX.md) for the full list
of layers, their kinds (deterministic / hybrid / llm_judge), and the
file under `aegis/checks/` that implements each one.

## Benchmark

`aegis-bench/` contains a cohort of reproducible cases. Each case has
a `brief.json`, an `input/` directory, an `expected.json` describing
the validator output, and a short technical README.

```
python -m aegis_cli check aegis-bench/cohort/<case>/input \
    --brief aegis-bench/cohort/<case>/brief.json \
    --no-llm
```

See [`aegis-bench/METHODOLOGY.md`](./aegis-bench/METHODOLOGY.md) for
case structure and reproducibility rules.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

[Apache License 2.0](./LICENSE).

## Maintainer

Aegis is maintained by [Andraste Labs](https://andrastelabs.com).
Contact: [github@andrastelabs.com](mailto:github@andrastelabs.com).
