# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD FORGE — WORKTREE SANDBOXING & AUTO-ROLLBACK ENGINE
=============================================================================
Instancia um Git Worktree efemero para injetar e auditar componentes em
sandbox isolado, garantindo merge atomico apenas se os gates passarem (exit 0)
e destruicao imediata do ambiente caso qualquer validacao falhe.
"""

import os
import shutil
import subprocess
from typing import Optional, Tuple


class WorktreeSandbox:
    """Gerencia execucoes de injeção isoladas em worktrees efemeros."""

    def __init__(self, root_repo: str, sandbox_name: str):
        self.root_repo = root_repo
        self.sandbox_name = sandbox_name
        self.worktree_path = os.path.join(root_repo, f"wt-sandbox-{sandbox_name}")

    def create(self) -> Tuple[bool, str]:
        """Cria um worktree isolado a partir da branch corrente."""
        cmd = ["git", "worktree", "add", "-b", f"branch-{self.sandbox_name}", self.worktree_path, "HEAD"]
        res = subprocess.run(cmd, cwd=self.root_repo, capture_output=True, text=True)
        if res.returncode != 0:
            return False, res.stderr
        return True, self.worktree_path

    def cleanup(self) -> None:
        """Remove o worktree e a branch temporaria associada."""
        if os.path.exists(self.worktree_path):
            subprocess.run(["git", "worktree", "remove", "--force", self.worktree_path], cwd=self.root_repo, capture_output=True)
            if os.path.exists(self.worktree_path):
                shutil.rmtree(self.worktree_path, ignore_errors=True)
        subprocess.run(["git", "branch", "-D", f"branch-{self.sandbox_name}"], cwd=self.root_repo, capture_output=True)

    def execute_and_validate(self, injection_fn) -> Tuple[bool, str]:
        """Executa a injecao no sandbox e valida com gates antes de liberar."""
        ok, err = self.create()
        if not ok:
            return False, f"Falha ao instanciar worktree sandbox: {err}"

        try:
            inj_ok = injection_fn(self.worktree_path)
            if not inj_ok:
                self.cleanup()
                return False, "Injecao abortada na sandbox."

            # Validar gates dentro do sandbox
            res = subprocess.run(["python", "ecossistema.py", "audit"], cwd=self.worktree_path, capture_output=True, text=True)
            if res.returncode != 0:
                self.cleanup()
                return False, f"Quality gates falharam no sandbox:\n{res.stderr or res.stdout}"

            # Se aprovado, merge atomico
            subprocess.run(["git", "merge", f"branch-{self.sandbox_name}"], cwd=self.root_repo, capture_output=True)
            self.cleanup()
            return True, "Injecao validada e commitada com sucesso via sandbox."
        except Exception as e:
            self.cleanup()
            return False, f"Erro inesperado no sandbox: {str(e)}"
