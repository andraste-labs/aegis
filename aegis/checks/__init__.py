"""Check-layer registry.

Each module under ``aegis.checks.*`` contributes one or more
``CheckLayer`` subclasses. The pipeline imports the registry to know
which layers to run for a given stack and the order to run them in.

Layer execution order matters: structural checks (AST, imports) run
before semantic checks (build, test), which run before judgment checks
(design fidelity, feature coverage).
"""

from __future__ import annotations

from aegis.checks.base import CheckLayer
from aegis.checks.brace_balance import BraceBalanceCheck
from aegis.checks.css_completeness import CssCompletenessCheck
from aegis.checks.design_fidelity import DesignFidelityCheck
from aegis.checks.duplicate_type_declarations import DuplicateTypeDeclarationsCheck
from aegis.checks.feature_coverage import FeatureCoverageCheck
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

# Layers are registered in canonical execution order. The numeric
# comments correspond to the entries in docs/LAYER_INDEX.md.
LAYERS: list[type[CheckLayer]] = [
    # ---- structural / AST layers ----
    PythonImportsCheck,                  # #4
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
    # ---- LLM-judge / hybrid layers ----
    DesignFidelityCheck,                 # #23
    FeatureCoverageCheck,                # #24
]


def all_layers() -> list[type[CheckLayer]]:
    """Return the canonical layer list in execution order."""
    return list(LAYERS)


__all__ = ["LAYERS", "all_layers", "CheckLayer"]
