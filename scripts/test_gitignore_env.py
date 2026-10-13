"""Ticket 1 (ETAPA_03): o .gitignore versionado deve ignorar .env (segredos) e manter .env.example rastreado.

Usa um repositorio git temporario com o .gitignore real da raiz; nao depende do
.git/info/exclude local de quem roda.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def repo_tmp(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    shutil.copy(RAIZ / ".gitignore", tmp_path / ".gitignore")
    for nome in (".env", ".env.local", ".env.example"):
        (tmp_path / nome).write_text("X=1\n", encoding="utf-8")
    return tmp_path


def _ignorado(repo, nome):
    return subprocess.run(["git", "check-ignore", "-q", nome], cwd=repo).returncode == 0


def test_env_e_ignorado(repo_tmp):
    assert _ignorado(repo_tmp, ".env")


def test_variantes_env_sao_ignoradas(repo_tmp):
    assert _ignorado(repo_tmp, ".env.local")


def test_env_example_continua_rastreavel(repo_tmp):
    assert not _ignorado(repo_tmp, ".env.example")
