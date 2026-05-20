"""Check-layer registry.

Each module under ``aegis.checks.*`` contributes one or more
``CheckLayer`` subclasses. The pipeline imports the registry to know
which layers to run for a given stack and which order to run them in.

Layer execution order matters: structural checks (AST, imports) run
before semantic checks (build, test), which run before judgment checks
(design fidelity, feature coverage). A layer that fails early can
short-circuit the run before the more expensive layers consume
subprocess or LLM time.

This registry is populated as Phase 1 extraction progresses. Pre-launch,
the list is intentionally small; v1.0.0 release will expose all 24.
"""

from __future__ import annotations

from aegis.checks.base import CheckLayer
from aegis.checks.brace_balance import BraceBalanceCheck
from aegis.checks.css_completeness import CssCompletenessCheck
from aegis.checks.duplicate_type_declarations import DuplicateTypeDeclarationsCheck
from aegis.checks.hook_destructure_consistency import HookDestructureConsistencyCheck
from aegis.checks.html_js_id_parity import HtmlJsIdParityCheck
from aegis.checks.import_case_consistency import ImportCaseConsistencyCheck
from aegis.checks.interactivity import InteractivityCheck
from aegis.checks.js_syntax import JsSyntaxCheck
from aegis.checks.named_import_consistency import NamedImportConsistencyCheck
from aegis.checks.node_deps_completeness import NodeDepsCompletenessCheck
from aegis.checks.npm_install import NpmInstallCheck
from aegis.checks.pytest_check import PytestCheck
from aegis.checks.python_completeness import PythonCompletenessCheck
from aegis.checks.python_deps_completeness import PythonDepsCompletenessCheck
from aegis.checks.python_imports import PythonImportsCheck
from aegis.checks.react_prop_consistency import ReactPropConsistencyCheck
from aegis.checks.router_prefix_consistency import RouterPrefixConsistencyCheck
from aegis.checks.static_imports import StaticImportsCheck
from aegis.checks.tsc import TscCheck

# Layers are registered here as they're extracted. Each module exports
# its own CheckLayer subclasses; this list is the canonical order.
#
# Order matters: structural checks (AST, balance) run before semantic
# (build), which run before judgment (LLM). An early failure
# short-circuits the more expensive layers downstream.
LAYERS: list[type[CheckLayer]] = [
    # ---- Phase 1.2: structural / AST layers ----
    PythonImportsCheck,                  # #4  in LAYER_INDEX.md
    PythonCompletenessCheck,             # #5
    PythonDepsCompletenessCheck,         # #6
    RouterPrefixConsistencyCheck,        # #7
    NodeDepsCompletenessCheck,           # #8
    CssCompletenessCheck,                # #9
    ReactPropConsistencyCheck,           # #10
    NamedImportConsistencyCheck,         # #11
    ImportCaseConsistencyCheck,          # #12
    DuplicateTypeDeclarationsCheck,      # #13
    HookDestructureConsistencyCheck,     # #14
    BraceBalanceCheck,                   # #15
    StaticImportsCheck,                  # #16
    HtmlJsIdParityCheck,                 # #17
    InteractivityCheck,                  # #18
    # ---- subprocess layers ----
    JsSyntaxCheck,                       # #19
    NpmInstallCheck,                     # #20
    TscCheck,                            # #21
    PytestCheck,                         # #22
    # ---- (LLM layers land here next) ----
]


def all_layers() -> list[type[CheckLayer]]:
    """Return the canonical layer list in execution order."""
    return list(LAYERS)


__all__ = ["LAYERS", "all_layers", "CheckLayer"]
