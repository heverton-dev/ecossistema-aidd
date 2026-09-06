# -*- coding: utf-8 -*-
"""Gate auditor for work "fronts" inside git worktrees.

Decides which verification commands to run based on paths the front touches,
then aggregates results into a binary pass/fail verdict.

Rules:
  - paths under tools/<tool-name>/  -> run pytest for that tool
  - paths under gates/ or root-scoped files -> run `python ecossistema.py audit`
  - all relevant commands must exit 0 for an "approved" verdict

Zero LLM cost — pure deterministic subprocess execution.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


# Known tools and the directory name inside tools/
KNOWN_TOOLS = ("aidd-forge", "aidd-generator", "aidd-master", "aidd-enterprise")

# Root-level files/dirs that trigger the meta-audit (ecossistema.py audit)
ROOT_SCOPED_PREFIXES = ("gates/", "scripts/")


@dataclass
class CommandResult:
    """Result of a single verification command."""
    command: str
    cwd: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


@dataclass
class AuditVerdict:
    """Aggregated audit verdict for a front."""
    front_id: str
    commands: list[CommandResult] = field(default_factory=list)

    @property
    def approved(self) -> bool:
        return all(c.passed for c in self.commands) and len(self.commands) > 0


def _extract_tool_name(path: str) -> str | None:
    """Given a relative path, return the tool name if it's under tools/<tool>/."""
    parts = path.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] == "tools":
        tool = parts[1]
        if tool in KNOWN_TOOLS:
            return tool
    return None


def _is_root_scoped(path: str) -> bool:
    """Check if a path is root-scoped (gates/, scripts/, or top-level files)."""
    norm = path.replace("\\", "/")
    if "/" not in norm:
        return True
    return any(norm.startswith(p) for p in ROOT_SCOPED_PREFIXES)


def _run_verification(cmd: list[str], cwd: Path) -> CommandResult:
    """Run a verification command, capture exit code without masking."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return CommandResult(
        command=" ".join(cmd),
        cwd=str(cwd),
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def resolve_commands(touched_paths: list[str]) -> tuple[set[str], bool]:
    """Determine which tools need pytest and whether root audit is needed.

    Args:
        touched_paths: List of paths the front touches (relative to worktree root).

    Returns:
        Tuple of (set of tool names needing pytest, needs_root_audit).
    """
    tools_needed: set[str] = set()
    needs_root_audit = False

    for p in touched_paths:
        tool = _extract_tool_name(p)
        if tool:
            tools_needed.add(tool)
        elif _is_root_scoped(p):
            needs_root_audit = True

    return tools_needed, needs_root_audit


def audit_front(
    worktree_path: str | Path,
    front_id: str,
    touched_paths: list[str],
) -> AuditVerdict:
    """Run relevant verification commands for a front and aggregate verdict.

    Args:
        worktree_path: Path to the worktree (or directory) to audit within.
        front_id: Identifier for the front being audited.
        touched_paths: Paths the front declares it touches (relative to worktree root).

    Returns:
        AuditVerdict with all command results and aggregated pass/fail.
    """
    wt = Path(worktree_path).resolve()
    verdict = AuditVerdict(front_id=front_id)

    tools_needed, needs_root_audit = resolve_commands(touched_paths)

    # 1. Root audit: run ecossistema.py audit if any root-scoped path is touched
    if needs_root_audit:
        ecossistema_py = wt / "ecossistema.py"
        if ecossistema_py.exists():
            result = _run_verification(
                [sys.executable, str(ecossistema_py), "audit"],
                cwd=wt,
            )
            verdict.commands.append(result)

    # 2. Tool pytest suites
    for tool in sorted(tools_needed):
        tool_dir = wt / "tools" / tool
        if tool_dir.is_dir():
            result = _run_verification(
                [sys.executable, "-m", "pytest", "-x", "-q"],
                cwd=tool_dir,
            )
            verdict.commands.append(result)

    return verdict
