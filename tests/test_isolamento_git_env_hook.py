# -*- coding: utf-8 -*-
"""
Regressão (2026-09-24): testes rodados dentro do pre-commit de uma worktree herdavam
GIT_DIR absoluto do hook e seus 'git init'/'git commit' em tmp_path gravavam na branch
real. O conftest.py da raiz remove essas variáveis antes da suíte.

Prova: roda um pytest filho com GIT_DIR apontando para um repositório "real" e confirma
que o commit do teste filho não aparece nele.
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def test_git_dir_do_hook_nao_vaza_para_repos_temporarios_dos_testes(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    _git(real, "init", "-q", "-b", "main")
    _git(real, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base")
    antes = _git(real, "rev-parse", "HEAD")

    filho = ROOT_DIR / "tests" / "_tmp_teste_filho_git_env.py"
    filho.write_text(textwrap.dedent("""
        import subprocess
        def test_commit_em_tmp(tmp_path):
            (tmp_path / "a.txt").write_text("x")
            subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
            subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "Commit teste"],
                           cwd=tmp_path, check=True)
    """), encoding="utf-8")
    try:
        env = dict(os.environ, GIT_DIR=str(real / ".git"), GIT_WORK_TREE=str(real))
        res = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=", str(filho)],
                             cwd=ROOT_DIR, env=env, capture_output=True, text=True)
    finally:
        filho.unlink(missing_ok=True)

    assert res.returncode == 0, res.stdout + res.stderr
    assert _git(real, "rev-parse", "HEAD") == antes
