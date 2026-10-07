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

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


# Known tools and the directory name inside tools/
KNOWN_TOOLS = ("aidd-forge", "aidd-pure", "aidd-master", "aidd-enterprise")

# Root-level files/dirs that trigger the meta-audit (ecossistema.py audit).
# Ecosystem gates live in each slice's gates/ folder (MAPA-GATES.json, ciclo-03 VSA).
ROOT_SCOPED_PREFIXES = (
    "gates/",
    "scripts/",
    "modulos/01-governanca-e-qualidade/gates/",
    "modulos/02-triade-motores/fluxo-01-pure/gates/",
    "modulos/02-triade-motores/fluxo-02-open/gates/",
    "modulos/02-triade-motores/fluxo-03-freedom/gates/",
    "modulos/03-plataforma-e-entrega/gates/",
    "modulos/04-nucleo-compartilhado/gates/",
    "modulos/04-nucleo-compartilhado/contracts/",
)


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
    """Given a relative path, return the tool name if it's under modulos/**/aidd-<tool>/."""
    parts = path.replace("\\", "/").split("/")
    if parts[0] == "modulos":
        tool = next((p for p in parts[:-1] if p in KNOWN_TOOLS), None)
        if tool:
            return tool
    return None


def _tool_dir(wt: Path, tool: str) -> Path:
    """Canonical folder of a tool under modulos/ (field "pasta" of MAPA-DONOS-FERRAMENTAS.json)."""
    mapa = wt / "componentes" / "compartilhado" / "specs" / "MAPA-DONOS-FERRAMENTAS.json"
    try:
        return wt / json.loads(mapa.read_text(encoding="utf-8"))[tool]["pasta"]
    except (OSError, KeyError, ValueError):
        return wt / "modulos" / tool


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
        tool_dir = _tool_dir(wt, tool)
        if tool_dir.is_dir():
            result = _run_verification(
                [sys.executable, "-m", "pytest", "-x", "-q"],
                cwd=tool_dir,
            )
            verdict.commands.append(result)

    return verdict
