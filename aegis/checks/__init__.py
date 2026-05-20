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
from aegis.checks.python_completeness import PythonCompletenessCheck
from aegis.checks.python_deps_completeness import PythonDepsCompletenessCheck
from aegis.checks.python_imports import PythonImportsCheck

# Layers are registered here as they're extracted. Each module exports
# its own CheckLayer subclasses; this list is the canonical order.
#
# Order matters: structural checks (AST, balance) run before semantic
# (build), which run before judgment (LLM). An early failure
# short-circuits the more expensive layers downstream.
LAYERS: list[type[CheckLayer]] = [
    # ---- Phase 1.2: structural / AST layers ----
    PythonImportsCheck,           # #4  in LAYER_INDEX.md
    PythonCompletenessCheck,      # #5
    PythonDepsCompletenessCheck,  # #6
    BraceBalanceCheck,            # #15
    # ---- (more layers land here as extraction progresses) ----
]


def all_layers() -> list[type[CheckLayer]]:
    """Return the canonical layer list in execution order."""
    return list(LAYERS)


__all__ = ["LAYERS", "all_layers", "CheckLayer"]
