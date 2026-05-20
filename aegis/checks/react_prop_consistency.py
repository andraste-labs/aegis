"""Layer #10 — JSX call sites must pass props the component declares.

Catches the canonical React/TS bug where one file calls
``<CryptoCard crypto={c} />`` while ``CryptoCard.tsx`` declares
``interface CryptoCardProps { coin: CryptoCurrency }`` — ``tsc`` would
eventually flag it as ``TS2322``, but the rework signal is buried in
compiler output. A clean static signal — "X passes 'crypto' but Y
declares 'coin'" — gives the rework prompt unambiguous direction.

Conservative — false positives would derail the build instead of
fixing it, so we skip:

- HTML elements (lowercase first char).
- Components that take ``{...rest}`` (spread) or whose Props extend
  ``HTMLAttributes`` / another type via intersection.
- Components whose Props type can't be parsed cleanly.
- Built-in JSX attributes (``key``, ``ref``, ``className``,
  ``style``, ``children``, common event handlers, ``data-*``,
  ``aria-*``).

Extracted from
``Team-AI/src/agents/integration_validator.py:_check_react_prop_consistency``.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from aegis.checks._ts_helpers import find_tsx_sources
from aegis.checks.base import CheckLayer, ValidationContext
from aegis.result import LayerKind, LayerResult, Verdict


# Built-in JSX attributes that any component implicitly accepts. Keeping
# the set narrow on purpose — anything genuinely common (event handlers,
# accessibility) is here, anything domain-specific is not.
_BUILTIN_ATTRS: frozenset[str] = frozenset([
    "key", "ref", "className", "style", "children", "id",
    "role", "tabIndex", "onClick", "onChange", "onSubmit",
    "onFocus", "onBlur", "onKeyDown", "onKeyUp", "onKeyPress",
    "onMouseEnter", "onMouseLeave", "onMouseDown", "onMouseUp",
    "onScroll", "onWheel", "onContextMenu", "onDoubleClick",
    "onInput", "onSelect", "data-testid",
    "aria-label", "aria-labelledby", "aria-describedby",
    "aria-hidden", "aria-live", "aria-atomic", "aria-busy",
])


# `interface XProps { … }` or `type XProps = { … }`.
_PROPS_DECL_RE = re.compile(
    r"""(?:^|\s)
        (?:export\s+)?
        (?:interface\s+(\w+Props)\s*\{([^}]*)\}
          |type\s+(\w+Props)\s*=\s*\{([^}]*)\})
    """,
    re.MULTILINE | re.VERBOSE | re.DOTALL,
)

# `interface XProps extends …` or `type XProps = SomeOther & …`. Marks
# the component as extensible — strict prop checks would false-positive.
_PROPS_EXTENSION_RE = re.compile(
    r"""(?:^|\s)
        (?:export\s+)?
        (?:interface\s+(\w+Props)\s+extends\s+
          |type\s+(\w+Props)\s*=\s*[\w<>\[\]\s,]+\s*&)
    """,
    re.MULTILINE | re.VERBOSE,
)

# `name:` or `name?:` inside an interface/type body → property key.
_PROP_KEY_RE = re.compile(r"(?:^|;|\n)\s*(\w+)\s*\??\s*:")

# JSX open tag for a component (capital-first): `<Component … />` or
# `<Component … >`.
_USAGE_RE = re.compile(r"<([A-Z]\w*)\b([^/>]*?)(?:/?>)", re.DOTALL)

# Attribute key inside a JSX open tag: `name=` (not preceded by word
# char or hyphen).
_ATTR_RE = re.compile(r"(?<![\w-])([\w-]+)\s*=")


def collect_component_props(sources: list[Path]) -> tuple[dict[str, set[str]], set[str]]:
    """Walk ``sources`` and return ``(component → declared props, extensible_set)``.

    A component name is derived by stripping the ``Props`` suffix from
    the type name (``CryptoCardProps`` → ``CryptoCard``). When the type
    extends another or contains ``...``, the component is marked
    extensible and excluded from strict prop checks downstream.
    """
    component_props: dict[str, set[str]] = {}
    extensible: set[str] = set()

    for tsx in sources:
        try:
            src = tsx.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in _PROPS_DECL_RE.finditer(src):
            name = m.group(1) or m.group(3)
            body = m.group(2) or m.group(4) or ""
            if not name:
                continue
            comp = name[: -len("Props")] if name.endswith("Props") else name
            if "..." in body:
                extensible.add(comp)
                continue
            keys = set(_PROP_KEY_RE.findall(body))
            if keys:
                component_props.setdefault(comp, set()).update(keys)

        for m in _PROPS_EXTENSION_RE.finditer(src):
            name = m.group(1) or m.group(2)
            if name and name.endswith("Props"):
                extensible.add(name[: -len("Props")])

    return component_props, extensible


def find_prop_problems(
    sources: list[Path],
    component_props: dict[str, set[str]],
    extensible: set[str],
    root: Path,
) -> list[dict[str, str | list[str]]]:
    """Walk ``sources`` for JSX call sites and report prop mismatches.

    Returns a list of dicts ready to embed in ``LayerResult.details``.
    """
    problems: list[dict[str, str | list[str]]] = []
    for tsx in sources:
        try:
            src = tsx.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = tsx.relative_to(root).as_posix()

        for m in _USAGE_RE.finditer(src):
            comp = m.group(1)
            if comp not in component_props or comp in extensible:
                continue
            attrs_blob = m.group(2)
            if "{..." in attrs_blob:
                continue
            used = set(_ATTR_RE.findall(attrs_blob))
            used -= _BUILTIN_ATTRS
            used = {a for a in used if not a.startswith(("data-", "aria-"))}
            if not used:
                continue
            undeclared = used - component_props[comp]
            if undeclared:
                problems.append({
                    "file": rel,
                    "component": comp,
                    "undeclared": sorted(undeclared),
                    "declared": sorted(component_props[comp]),
                })
    return problems


class ReactPropConsistencyCheck(CheckLayer):
    """Layer #10 — JSX prop usage must match the component's declared Props."""

    NAME = "react_prop_consistency"
    KIND = LayerKind.deterministic
    APPLIES_TO = ("node",)
    DESCRIPTION = (
        "JSX call sites must pass props the receiving component declares. "
        "Catches the canonical `<X foo={…}>` vs `interface XProps { bar }` "
        "mismatch that tsc would flag as TS2322 (but with a noisier signal)."
    )

    def run(self, ctx: ValidationContext) -> LayerResult:
        start = time.monotonic()
        root = ctx.code_path
        if not root.is_dir():
            return self._skip("code_path is not a directory")

        sources = find_tsx_sources(root)
        if not sources:
            return self._skip("No TSX/JSX files in input")

        component_props, extensible = collect_component_props(sources)
        if not component_props:
            return self._skip("No component Props types found")

        problems = find_prop_problems(sources, component_props, extensible, root)

        if problems:
            shown = problems[:20]
            return self._result(
                Verdict.failed,
                summary=(
                    f"{len(problems)} JSX call site(s) pass props the "
                    f"component does not declare "
                    f"({len(component_props)} components scanned)"
                ),
                start_time=start,
                details={
                    "components_scanned": len(component_props),
                    "extensible_components": sorted(extensible),
                    "problems": shown,
                    "truncated": len(problems) > 20,
                },
            )

        return self._result(
            Verdict.passed,
            summary=(
                f"All JSX usages match their component Props "
                f"({len(component_props)} components, {len(sources)} files)"
            ),
            start_time=start,
            details={
                "components_scanned": len(component_props),
                "files_scanned": len(sources),
            },
        )


__all__ = [
    "ReactPropConsistencyCheck",
    "collect_component_props",
    "find_prop_problems",
]
