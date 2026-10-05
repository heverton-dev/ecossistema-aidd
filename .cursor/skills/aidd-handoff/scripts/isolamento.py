# -*- coding: utf-8 -*-
"""
Módulo de Isolamento de Raio de Impacto e Gestão de Worktree para aidd-handoff (D3).
Garante que a ferramenta aidd-handoff opere em modo isolado:
- Escritas no repositório permitidas APENAS em docs/secoes/.
- Gestão de worktrees efêmeras para sandboxing quando aplicável.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class SandboxViolationError(PermissionError):
    """Lançada quando há tentativa de escrita fora do raio de impacto autorizado de aidd-handoff."""
    pass


class HandoffWorktreeManager:
    """Gerencia a validação de caminhos e ciclo de vida de worktree para o aidd-handoff."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root).resolve()
        self.permitidos_raiz = {
            self.repo_root / "docs" / "secoes",
        }

    def validar_caminho_escrita(self, caminho_alvo: str | Path, worktree_ativa: Optional[Path] = None) -> bool:
        alvo_res = Path(caminho_alvo).resolve()

        if worktree_ativa is not None:
            wt_res = Path(worktree_ativa).resolve()
            try:
                alvo_res.relative_to(wt_res)
                return True
            except ValueError:
                pass

        for permitido in self.permitidos_raiz:
            try:
                alvo_res.relative_to(permitido)
                return True
            except ValueError:
                continue

        raise SandboxViolationError(
            f"[SANDBOX HANDOFF] Tentativa de escrita bloqueada fora do raio de impacto: {alvo_res}"
        )

    def obter_caminho_worktree(self, slug: str) -> Path:
        nome_worktree = f"worktrees_handoff-{slug}"
        return self.repo_root.parent / nome_worktree


def validar_caminho_escrita(caminho_alvo: str | Path, repo_root: str | Path) -> bool:
    manager = HandoffWorktreeManager(repo_root=repo_root)
    return manager.validar_caminho_escrita(caminho_alvo)
