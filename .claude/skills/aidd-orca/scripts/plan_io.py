"""Generic Flight Plan JSON persistence.

Shared by both execution modes (worktree and subagent) — pure I/O, no
mechanism-specific logic. Lets a user open, review and edit a compiled
Flight Plan (harness, model, subagent_type or prompt) before confirming
execution.
"""

from __future__ import annotations

import json
from pathlib import Path


def salvar_plano_de_voo(data: dict, path: str | Path) -> Path:
    """Persist a compiled flight plan dict as indented JSON.

    Returns the resolved Path written to.
    """
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return resolved


def carregar_plano_de_voo(path: str | Path) -> dict:
    """Load a previously saved (and possibly user-edited) flight plan JSON."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
