"""Layer #20 — `npm install` (or `npm ci`) must succeed.

For Node projects this is the most concrete signal that the
``package.json`` is at least cohesive enough to resolve all deps. If
``npm install`` fails — version conflicts, missing registry packages,
incompatible peer deps — the project cannot ship regardless of how
clean the static checks looked.

Strategy:

1. If ``package-lock.json`` exists, prefer ``npm ci --ignore-scripts``
   (faster, reproducible). Fall back to ``npm install --ignore-scripts``
   if ``npm ci`` exits non-zero.
2. ``--ignore-scripts`` is non-negotiable: an attacker-controlled
   ``preinstall``/``postinstall`` is the entire supply-chain attack
   surface this layer is supposed to neutralize.
3. Long-running by nature; honors ``ctx.timeout_per_command``.
4. Skipped when no ``package.json`` is present (not a Node project).
5. When ``npm`` isn't on PATH, returns a failure (not a skip) — the
   user explicitly asked to validate a Node project.

Extracted from the ``stack_type == 'node'`` branch in
``Team-AI/src/agents/integration_validator.py``.
"""

from __future__ import annotations

import time
from pathlib import Path

from aegis.checks.base import CheckLayer, ValidationContext
from aegis.result import LayerKind, LayerResult, Verdict
from aegis.subprocess_runner import run_cmd, scrub_env


# Windows ships `npm` and `npx` as `.cmd` shims; pick the right one.
def _npm_argv0() -> str:
    import platform
    return "npm.cmd" if platform.system() == "Windows" else "npm"


class NpmInstallCheck(CheckLayer):
    """Layer #20 — `npm ci` (or `npm install`) on the project root."""

    NAME = "npm_install"
    KIND = LayerKind.deterministic
    APPLIES_TO = ("node",)
    DESCRIPTION = (
        "Run `npm ci --ignore-scripts` (or `npm install --ignore-scripts` "
        "as fallback). A non-zero exit means the project cannot "
        "actually be installed; static checks alone are insufficient signal."
    )

    async def run_async(self, ctx: ValidationContext) -> LayerResult:
        start = time.monotonic()
        root = ctx.code_path
        if not root.is_dir():
            return self._skip("code_path is not a directory")
        if not (root / "package.json").exists():
            return self._skip("No package.json at root")

        npm = _npm_argv0()
        env = {**scrub_env(), "CI": "true"}
        timeout = ctx.timeout_per_command

        has_lock = (root / "package-lock.json").exists()
        first_argv = (
            [npm, "ci", "--ignore-scripts"]
            if has_lock
            else [npm, "install", "--ignore-scripts"]
        )

        try:
            primary = await run_cmd(first_argv, cwd=root, timeout=timeout, env=env)
        except FileNotFoundError:
            return self._result(
                Verdict.failed,
                summary="`npm` not on PATH — cannot run install",
                start_time=start,
                details={"error": "npm_not_found"},
            )

        if primary.returncode == 0 and not primary.timed_out:
            return self._result(
                Verdict.passed,
                summary=f"`{' '.join(first_argv[1:])}` succeeded",
                start_time=start,
                details={
                    "command": first_argv,
                    "duration_seconds": primary.duration_seconds,
                    "stdout_tail": primary.stdout.strip()[-500:],
                },
            )

        # If we tried `npm ci` and it failed for any reason other than
        # timeout, fall back to `npm install` (the lockfile may be stale
        # in agent-generated projects).
        fallback_run = None
        if has_lock and not primary.timed_out:
            try:
                fallback_run = await run_cmd(
                    [npm, "install", "--ignore-scripts"],
                    cwd=root,
                    timeout=timeout,
                    env=env,
                )
            except FileNotFoundError:
                pass

        if fallback_run is not None and fallback_run.returncode == 0 and not fallback_run.timed_out:
            return self._result(
                Verdict.passed,
                summary="`npm install --ignore-scripts` succeeded (npm ci fallback)",
                start_time=start,
                details={
                    "command": [npm, "install", "--ignore-scripts"],
                    "fallback_used": True,
                    "duration_seconds": fallback_run.duration_seconds,
                    "stdout_tail": fallback_run.stdout.strip()[-500:],
                },
            )

        final = fallback_run if fallback_run is not None else primary
        summary = (
            "npm install timed out"
            if final.timed_out
            else f"npm install failed (exit {final.returncode})"
        )
        return self._result(
            Verdict.failed,
            summary=summary,
            start_time=start,
            details={
                "command_primary": first_argv,
                "fallback_used": fallback_run is not None,
                "exit_code": final.returncode,
                "timed_out": final.timed_out,
                "stderr_tail": final.stderr.strip()[-2000:],
                "stdout_tail": final.stdout.strip()[-1000:],
            },
        )

    def run(self, ctx: ValidationContext) -> LayerResult:  # pragma: no cover
        import asyncio
        return asyncio.run(self.run_async(ctx))


__all__ = ["NpmInstallCheck"]
