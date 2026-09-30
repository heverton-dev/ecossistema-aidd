# -*- coding: utf-8 -*-
"""
Módulo de Isolamento de Raio de Impacto e Gestão de Worktree Efêmera para aidd-tdd (D3).
Garante que a ferramenta aidd-tdd opere em modo isolado:
- Escritas no repositório principal permitidas APENAS em docs/tdd/.
- Execuções com modificação de código contidas em worktree efêmera ../worktrees_tdd-<slug>/.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Generator, Optional


class SandboxViolationError(PermissionError):
    """Lançada quando há tentativa de escrita fora do raio de impacto autorizado de aidd-tdd."""
    pass


class TddWorktreeManager:
    """Gerencia a criação, validação de caminho e ciclo de vida de worktrees para o fluxo TDD."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root).resolve()
        self.permitidos_raiz = {
            self.repo_root / "docs" / "tdd",
            self.repo_root / "secoes",
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
            f"[SANDBOX TDD] Tentativa de escrita bloqueada fora do raio de impacto: {alvo_res}"
        )

    def obter_caminho_worktree(self, slug: str) -> Path:
        nome_worktree = f"worktrees_tdd-{slug}"
        return self.repo_root.parent / nome_worktree

    def criar_worktree(self, slug: str, branch_base: str = "HEAD") -> Path:
        caminho_wt = self.obter_caminho_worktree(slug)
        branch_nome = f"tdd-isolated/{slug}"

        if caminho_wt.exists():
            self.remover_worktree(caminho_wt, branch_nome)

        cmd = [
            "git", "worktree", "add", "-b", branch_nome,
            str(caminho_wt), branch_base
        ]
        res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Falha ao criar git worktree: {res.stderr}")

        return caminho_wt

    def remover_worktree(self, caminho_wt: Path, branch_nome: Optional[str] = None) -> None:
        if caminho_wt.exists():
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(caminho_wt)],
                cwd=self.repo_root,
                capture_output=True
            )
            if caminho_wt.exists():
                shutil.rmtree(caminho_wt, ignore_errors=True)

        if branch_nome:
            subprocess.run(
                ["git", "branch", "-D", branch_nome],
                cwd=self.repo_root,
                capture_output=True
            )

    @contextlib.contextmanager
    def contexto_worktree(self, slug: str) -> Generator[Path, None, None]:
        wt_path = self.criar_worktree(slug)
        try:
            yield wt_path
        finally:
            self.remover_worktree(wt_path, f"tdd-isolated/{slug}")
