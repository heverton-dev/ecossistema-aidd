# -*- coding: utf-8 -*-
"""
Módulo de Isolamento e Validação de Raio de Impacto para aidd-grill (Ticket 2 / D3 / DoD 2).
Garante que a emissão de relatórios de entrevistas socráticas ocorra apenas em diretórios autorizados.
"""

from __future__ import annotations

from pathlib import Path


class SandboxViolationError(PermissionError):
    """Lançada quando há tentativa de escrita fora do raio permitido."""
    pass


class GrillWorktreeManager:
    """Validador de fronteiras de arquivo para aidd-grill."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root).resolve()
        self.permitidos = {
            self.repo_root / "docs",
            self.repo_root / "secoes",
        }

    def validar_caminho_escrita(self, caminho_alvo: str | Path) -> bool:
        alvo_res = Path(caminho_alvo).resolve()

        for permitido in self.permitidos:
            try:
                alvo_res.relative_to(permitido)
                return True
            except ValueError:
                continue

        raise SandboxViolationError(
            f"[SANDBOX GRILL] Tentativa de escrita bloqueada fora de docs/ ou secoes/: {alvo_res}"
        )
