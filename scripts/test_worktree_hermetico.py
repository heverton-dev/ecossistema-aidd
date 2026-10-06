# -*- coding: utf-8 -*-
"""
Testes unitários determinísticos do gerenciador hermético de worktrees.
"""

import os
from pathlib import Path

from scripts.worktree_hermetico import (
    VARIAVEIS_DE_REPOSITORIO_SENSÍVEIS,
    WorktreeHermetico,
    obter_env_sanitizado,
)


def test_obter_env_sanitizado_remove_variaveis_git():
    sujo = {
        "PATH": "C:\\bin",
        "GIT_DIR": ".git",
        "GIT_INDEX_FILE": ".git/index",
        "PYTHONPATH": "scripts",
    }
    limpo = obter_env_sanitizado(sujo)
    assert "GIT_DIR" not in limpo
    assert "GIT_INDEX_FILE" not in limpo
    assert limpo["PATH"] == "C:\\bin"
    assert limpo["PYTHONPATH"] == "scripts"


def test_worktree_hermetico_fluxo_completo(tmp_path):
    repo_falso = tmp_path / "repo"
    repo_falso.mkdir()
    wt_path = tmp_path / "wt"

    wt = WorktreeHermetico(repo_root=repo_falso, branch_name="teste-branch", worktree_path=wt_path)
    assert wt.repo_root == repo_falso.resolve()
    assert wt.branch_name == "teste-branch"
    assert wt.worktree_path == wt_path.resolve()
    for var in VARIAVEIS_DE_REPOSITORIO_SENSÍVEIS:
        assert var not in wt.env
