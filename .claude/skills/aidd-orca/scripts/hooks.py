"""Reactive pre- and post-execution hooks for ORCA ADE fronts.

Deterministic state-machine transitions + event-file signal for
zero-polling orchestration. Zero LLM cost.

Specs:
  - docs/features/orquestracao-orca-ade/10-arquitetura-hooks-reativos-pre-e-pos-execucao.md
"""

from __future__ import annotations

import time
from pathlib import Path

from .gate_auditor import audit_front
from .state_engine import (
    FrontState,
    load_state,
    render_memory_md,
    save_state,
    update_front_state,
    _write_atomic,
)


def _write_memory(state: dict, state_path: Path) -> None:
    """Persist memory.md next to (or near) the state file."""
    memory_path = state_path.parent / "memory.md"
    _write_atomic(memory_path, render_memory_md(state))


def executar_pre_hook(
    front_name: str,
    worktree_path: Path,
    state_path: Path,
) -> dict:
    """Execute the pre-hook before dispatching an agent to a front.

    1. Validates worktree_path exists (raises FileNotFoundError if not).
    2. Loads state, transitions front to RUNNING, saves atomically.
    3. Writes updated memory.md.
    4. Returns summary dict.
    """
    if not worktree_path.exists():
        raise FileNotFoundError(f"Worktree not found: {worktree_path}")

    state = load_state(state_path)
    state = update_front_state(state, front_name, FrontState.RUNNING)
    save_state(state, state_path)
    _write_memory(state, state_path)

    return {
        "status": FrontState.RUNNING.value,
        "timestamp": time.time(),
        "front": front_name,
    }


def executar_post_hook(
    front_name: str,
    worktree_path: Path,
    state_path: Path,
    agent_exit_code: int,
    touched_paths: list[str],
) -> dict:
    """Execute the post-hook after the agent process exits.

    1. Determines new state from exit_code + gate audit.
    2. Persists state + memory.md atomically.
    3. Emits event file ``.orca/events/<front>.done`` for reactive wakeup.
    4. Returns summary dict.
    """
    if agent_exit_code != 0:
        new_state = FrontState.FAILED
    else:
        verdict = audit_front(worktree_path, front_name, touched_paths)
        new_state = (
            FrontState.GATE_PASSED if verdict.approved else FrontState.FAILED
        )

    state = load_state(state_path)
    state = update_front_state(state, front_name, new_state)
    save_state(state, state_path)
    _write_memory(state, state_path)

    event_dir = worktree_path / ".orca" / "events"
    event_dir.mkdir(parents=True, exist_ok=True)
    event_file = event_dir / f"{front_name}.done"
    event_file.write_text(new_state.value, encoding="utf-8")

    return {
        "front": front_name,
        "state": new_state.value,
        "event_file": str(event_file),
    }
