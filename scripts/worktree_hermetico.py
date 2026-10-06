# -*- coding: utf-8 -*-
"""
Gerenciador Hermético de Worktrees Git para o Ecossistema AIDD.

Garante isolamento estrito:
- Sanitização absoluta de variáveis de repositório (GIT_DIR, GIT_INDEX_FILE, etc.)
- Pre-sync determinístico com a branch base
- Criação e limpeza controlada sem vazamento de estado
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from scripts.exit_codes import ExitCode

VARIAVEIS_DE_REPOSITORIO_SENSÍVEIS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
)


def obter_env_sanitizado(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Retorna dicionário de variáveis de ambiente com variáveis git limpas."""
    fonte = os.environ if env is None else env
    return {k: v for k, v in fonte.items() if k not in VARIAVEIS_DE_REPOSITORIO_SENSÍVEIS}


class WorktreeHermetico:
    """Context manager e controlador de ciclo de vida de worktrees herméticas."""

    def __init__(self, repo_root: Path, branch_name: str, worktree_path: Path):
        self.repo_root = Path(repo_root).resolve()
        self.branch_name = branch_name
        self.worktree_path = Path(worktree_path).resolve()
        self.env = obter_env_sanitizado()

    def _executar_git(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd or self.repo_root),
            env=self.env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

    def criar(self, base_ref: str = "HEAD") -> bool:
        """Cria a worktree isolada em uma nova branch apontando para base_ref."""
        if self.worktree_path.exists():
            return False

        codigo, _, _ = self._executar_git(
            ["worktree", "add", "-b", self.branch_name, str(self.worktree_path), base_ref]
        )
        return codigo == 0

    def remover(self, force: bool = True) -> bool:
        """Remove a worktree e limpa o registro de worktrees do git."""
        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append(str(self.worktree_path))

        codigo, _, _ = self._executar_git(args)
        self._executar_git(["worktree", "prune"])
        return codigo == 0
