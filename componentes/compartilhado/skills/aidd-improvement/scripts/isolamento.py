# -*- coding: utf-8 -*-
"""
Módulo de Isolamento de Raio de Impacto e Gestão de VSA (Worktree Efêmero).
Garante que a ferramenta aidd-melhoria opere de forma estritamente sandboxed:
- Escritas no repositório permitidas APENAS em docs/ (especificamente docs/melhorias/).
- Qualquer I/O exploratório ou temporário deve ocorrer em Git Worktree isolado.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Generator, Optional


class SandboxViolationError(PermissionError):
    """Lançada quando há tentativa de escrita fora do raio de impacto autorizado."""
    pass


def validar_caminho_escrita(
    caminho: str | Path,
    repo_root: str | Path,
    worktree_dir: Optional[str | Path] = None,
) -> bool:
    """
    Valida se um caminho pretendido para escrita respeita o isolamento de raio de impacto.
    Regra:
      - Permitido: dentro de repo_root/docs/ (ex: docs/melhorias/)
      - Permitido: dentro de worktree_dir (espaço de trabalho temporário/VSA)
      - Proibido: qualquer outro caminho no repo_root ou fora dele.
    """
    caminho_abs = Path(caminho).resolve()
    repo_abs = Path(repo_root).resolve()
    docs_permitido = (repo_abs / "docs").resolve()

    # Checar se está dentro do worktree temporário isolado
    if worktree_dir is not None:
        wt_abs = Path(worktree_dir).resolve()
        try:
            caminho_abs.relative_to(wt_abs)
            return True
        except ValueError:
            pass

    # Checar se está dentro de docs/
    try:
        caminho_abs.relative_to(docs_permitido)
        return True
    except ValueError:
        pass

    # Se estiver tentando escrever em qualquer outro lugar sob repo_root ou no root
    try:
        caminho_abs.relative_to(repo_abs)
        raise SandboxViolationError(
            f"[SANDBOX VIOLATION] Tentativa de escrita bloqueada no repositório: '{caminho_abs}'. "
            f"Escrita só é permitida em 'docs/' ou dentro do worktree isolado."
        )
    except ValueError:
        # Fora do repositório completamente
        raise SandboxViolationError(
            f"[SANDBOX VIOLATION] Tentativa de escrita bloqueada fora do repositório/sandbox: '{caminho_abs}'."
        )


class VSAWorktreeManager:
    """Gerenciador de Worktrees efêmeros para Virtual Slice Architecture (VSA)."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root).resolve()

    @contextlib.contextmanager
    def sessao_isolada(self, prefixo: str = "vsa-melhoria") -> Generator[Path, None, None]:
        """
        Cria um git worktree efêmero isolado em um diretório temporário paralelo,
        fornece o path durante a sessão e garante o expurgo completo no encerramento.
        """
        id_unico = uuid.uuid4().hex[:8]
        branch_name = f"vsa/{prefixo}-{id_unico}"
        worktree_path = self.repo_root.parent / f".wt-{prefixo}-{id_unico}"

        # Criar worktree
        cmd_add = [
            "git", "worktree", "add",
            "-b", branch_name,
            str(worktree_path),
            "HEAD",
        ]
        res = subprocess.run(
            cmd_add,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            raise RuntimeError(f"Falha ao criar Git Worktree isolado: {res.stderr or res.stdout}")

        try:
            yield worktree_path
        finally:
            # Limpeza determinística garantida
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(self.repo_root),
                    capture_output=True,
                    text=True,
                )
            except Exception:
                pass

            # Excluir branch efêmero
            try:
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=str(self.repo_root),
                    capture_output=True,
                    text=True,
                )
            except Exception:
                pass

            # Garantir remoção residual em disco caso git worktree remove tenha deixado algo
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
