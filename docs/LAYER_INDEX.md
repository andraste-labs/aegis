# Aegis Validator — Layer Index

This is the canonical list of every layer Aegis runs, in pipeline
execution order. The registry source is
[`aegis/checks/__init__.py`](../aegis/checks/__init__.py).

## Summary

| Kind | Count |
|---|---|
| Deterministic | 22 |
| Hybrid (LLM + deterministic override) | 1 |
| LLM-as-judge | 1 |
| **Total** | **24** |

## Numbering

Layers #1–#3 are pipeline scaffolding (stack detection, code-path
materialisation, environment setup) — not check layers in their own
right. The check-layer numbering below starts at #4.

## Layers

| # | Name | Kind | Applies to | Source |
|---|---|---|---|---|
| 4 | `python_imports` | deterministic | python | [`aegis/checks/python_imports.py`](../aegis/checks/python_imports.py) |
| 5 | `python_completeness` | deterministic | python | [`aegis/checks/python_completeness.py`](../aegis/checks/python_completeness.py) |
| 6 | `python_deps_completeness` | deterministic | python | [`aegis/checks/python_deps_completeness.py`](../aegis/checks/python_deps_completeness.py) |
| 7 | `router_prefix_consistency` | deterministic | python | [`aegis/checks/router_prefix_consistency.py`](../aegis/checks/router_prefix_consistency.py) |
| 8 | `node_deps_completeness` | deterministic | node | [`aegis/checks/node_deps_completeness.py`](../aegis/checks/node_deps_completeness.py) |
| 9 | `css_completeness` | deterministic | node, static_html | [`aegis/checks/css_completeness.py`](../aegis/checks/css_completeness.py) |
| 10 | `react_prop_consistency` | deterministic | node | [`aegis/checks/react_prop_consistency.py`](../aegis/checks/react_prop_consistency.py) |
| 11 | `named_import_consistency` | deterministic | node | [`aegis/checks/named_import_consistency.py`](../aegis/checks/named_import_consistency.py) |
| 12 | `import_case_consistency` | deterministic | node, python | [`aegis/checks/import_case_consistency.py`](../aegis/checks/import_case_consistency.py) |
| 13 | `duplicate_type_declarations` | deterministic | node | [`aegis/checks/duplicate_type_declarations.py`](../aegis/checks/duplicate_type_declarations.py) |
| 14 | `hook_destructure_consistency` | deterministic | node | [`aegis/checks/hook_destructure_consistency.py`](../aegis/checks/hook_destructure_consistency.py) |
| 15 | `ast_brace_balance` | deterministic | node, static_html | [`aegis/checks/brace_balance.py`](../aegis/checks/brace_balance.py) |
| 16 | `static_imports` | deterministic | node, static_html | [`aegis/checks/static_imports.py`](../aegis/checks/static_imports.py) |
| 17 | `html_js_id_parity` | deterministic | static_html, node | [`aegis/checks/html_js_id_parity.py`](../aegis/checks/html_js_id_parity.py) |
| 18 | `interactivity` | deterministic | static_html, node | [`aegis/checks/interactivity.py`](../aegis/checks/interactivity.py) |
| 19 | `js_syntax` | deterministic | static_html, node | [`aegis/checks/js_syntax.py`](../aegis/checks/js_syntax.py) |
| 20 | `npm_install` | deterministic | node | [`aegis/checks/npm_install.py`](../aegis/checks/npm_install.py) |
| 21 | `tsc` | deterministic | node | [`aegis/checks/tsc.py`](../aegis/checks/tsc.py) |
| 22 | `pytest` | deterministic | python | [`aegis/checks/pytest_check.py`](../aegis/checks/pytest_check.py) |
| 23 | `design_fidelity` | hybrid | static_html, node, python | [`aegis/checks/design_fidelity.py`](../aegis/checks/design_fidelity.py) |
| 24 | `feature_coverage` | hybrid | static_html, node, python | [`aegis/checks/feature_coverage.py`](../aegis/checks/feature_coverage.py) |

## Pluggable LLM client

Layers #23 and #24 invoke an `LLMClient` (see
[`aegis/llm_client.py`](../aegis/llm_client.py)). Aegis ships an
`AnthropicClient` against the Anthropic SDK; the `LLMClient` Protocol
allows alternative backends. When no client is configured (or
`--no-llm` is passed), these layers skip cleanly.

## Layer ordering

The pipeline runs layers in the order declared in
`aegis/checks/__init__.py:LAYERS`. Structural layers (AST, balance)
run first; subprocess layers (`npm_install`, `tsc`, `pytest`) follow;
hybrid LLM layers run last. A failure does not short-circuit the
pipeline — every applicable layer reports its own verdict and the
final pass/fail is the conjunction.
