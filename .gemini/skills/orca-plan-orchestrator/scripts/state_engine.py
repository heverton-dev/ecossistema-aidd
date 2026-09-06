"""State engine for ORCA ADE orchestration.

Atomic persistence of .orca_state.json, state machine with 6 states,
memory.md rendering, and crash-recovery classification.

Zero LLM cost — pure deterministic state management.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from enum import Enum
from pathlib import Path
from typing import Any


class FrontState(str, Enum):
    """The 6 states from the ORCA ADE manual."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    GATE_PASSED = "GATE_PASSED"
    MERGED = "MERGED"
    FAILED = "FAILED"
    PAUSED_QUOTA = "PAUSED_QUOTA"


class ResumeAction(str, Enum):
    """Actions classified during crash-recovery resume."""

    IGNORE = "ignore"
    READY_TO_MERGE = "ready_to_merge"
    RESUME_RUNNING = "resume_running"
    RETRY = "retry"
    NO_ACTION = "no_action"


class ResumeClassification:
    """Result of classifying a single front for resume."""

    def __init__(self, front_name: str, state: FrontState, action: ResumeAction):
        self.front_name = front_name
        self.state = state
        self.action = action

    def __repr__(self) -> str:
        return (
            f"ResumeClassification({self.front_name!r}, "
            f"{self.state.value}, {self.action.value})"
        )


def _write_atomic(path: Path, content: str) -> None:
    """Write content to a file atomically using temp file + rename.

    This ensures that if the process dies mid-write, the original file
    (if any) remains intact.
    """
    dir_path = path.parent
    dir_path.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _read_state_file(path: Path) -> dict[str, Any]:
    """Read and parse the .orca_state.json file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def create_initial_state(front_names: list[str]) -> dict[str, Any]:
    """Create a fresh state dict with all fronts in PENDING."""
    now = time.time()
    return {
        "version": 1,
        "created_at": now,
        "updated_at": now,
        "fronts": {
            name: {
                "state": FrontState.PENDING.value,
                "branch": None,
                "commit_sha": None,
                "updated_at": now,
            }
            for name in front_names
        },
    }


def save_state(state: dict[str, Any], state_path: Path) -> None:
    """Atomically save state to .orca_state.json."""
    state["updated_at"] = time.time()
    _write_atomic(state_path, json.dumps(state, indent=2, ensure_ascii=False))


def load_state(state_path: Path) -> dict[str, Any]:
    """Load state from .orca_state.json."""
    return _read_state_file(state_path)


def update_front_state(
    state: dict[str, Any],
    front_name: str,
    new_state: FrontState,
    branch: str | None = None,
    commit_sha: str | None = None,
) -> dict[str, Any]:
    """Update a single front's state in the state dict."""
    if front_name not in state["fronts"]:
        raise KeyError(f"Front {front_name!r} not found in state")
    front = state["fronts"][front_name]
    front["state"] = new_state.value
    if branch is not None:
        front["branch"] = branch
    if commit_sha is not None:
        front["commit_sha"] = commit_sha
    front["updated_at"] = time.time()
    state["updated_at"] = time.time()
    return state


def render_memory_md(state: dict[str, Any]) -> str:
    """Render a human-readable memory.md from the current state.

    Returns a Markdown string with a table of fronts and their statuses.
    """
    lines = [
        "# ORCA ADE — Progresso da Orquestração",
        "",
        "| Frente | Estado | Branch | Commit | Última Atualização |",
        "|--------|--------|--------|--------|--------------------|",
    ]

    for name, info in state["fronts"].items():
        st = info.get("state", "?")
        branch = info.get("branch") or "—"
        sha = (info.get("commit_sha") or "—")[:8] if info.get("commit_sha") else "—"
        ts = info.get("updated_at")
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else "—"
        lines.append(f"| {name} | {st} | {branch} | {sha} | {ts_str} |")

    lines.append("")
    return "\n".join(lines)


def classify_resume(state: dict[str, Any]) -> list[ResumeClassification]:
    """Classify each front's resume action based on current state.

    Rules from the manual:
    - MERGED -> ignore (skip entirely)
    - GATE_PASSED -> ready to merge
    - RUNNING -> mark as resume candidate (stub — real agent dispatch
      is Item 3/6 of the orchestration plan)
    - FAILED -> retry
    - PENDING / PAUSED_QUOTA / other -> no action yet
    """
    results: list[ResumeClassification] = []
    for name, info in state["fronts"].items():
        try:
            current_state = FrontState(info["state"])
        except ValueError:
            current_state = FrontState.PENDING

        if current_state == FrontState.MERGED:
            action = ResumeAction.IGNORE
        elif current_state == FrontState.GATE_PASSED:
            action = ResumeAction.READY_TO_MERGE
        elif current_state == FrontState.RUNNING:
            action = ResumeAction.RESUME_RUNNING
        elif current_state == FrontState.FAILED:
            action = ResumeAction.RETRY
        else:
            action = ResumeAction.NO_ACTION

        results.append(ResumeClassification(name, current_state, action))

    return results


def retomar_frente_em_execucao(
    front_name: str, state: dict[str, Any]
) -> dict[str, Any]:
    """Stub for resuming a RUNNING front.

    The real implementation (agent CLI subprocess dispatch) comes in
    Item 3/6 of the orchestration plan. This function currently just
    returns the state unchanged as a placeholder.
    """
    # TODO: Implement real agent dispatch in Item 3/6 of the
    # orchestration plan (agent_spawner.py subprocess call).
    return state
