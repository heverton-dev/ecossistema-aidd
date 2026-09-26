# -*- coding: utf-8 -*-
"""
Regressão (25/09/2026): dentro do hook de pre-commit o git exporta GIT_DIR /
GIT_INDEX_FILE. O passo de telemetria (`python ecossistema.py status --testes
--write`, scripts/manutencao/gerar_status_testes.py) rodava o pytest de cada
ferramenta herdando essas variáveis; os testes que fazem `git commit` num
tmp_path gravaram 9 commits de lixo ("leak", "clean", "broken", "feat: inicial"...)
na branch real audit/evolucao-skills-pocock-ciclo-01.

O teste roda o pytest de verdade numa ferramenta falsa com GIT_DIR apontando
para um repositório isca e confere que (a) o subprocesso não herda as variáveis
e (b) a isca não ganha commit.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "manutencao"))
import gerar_status_testes  # noqa: E402

TESTE_DA_FERRAMENTA = '''
import os, subprocess
def test_commit_em_tmp(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "leak"],
                   cwd=tmp_path, check=True)
    assert "GIT_DIR" not in os.environ
    assert "GIT_INDEX_FILE" not in os.environ
'''


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True).stdout.strip()


def test_telemetria_nao_vaza_git_do_hook(tmp_path, monkeypatch):
    isca = tmp_path / "isca"
    isca.mkdir()
    _git(isca, "init", "-q")
    (isca / "r.txt").write_text("r")
    _git(isca, "add", "-A")
    _git(isca, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    antes = _git(isca, "rev-list", "--count", "HEAD")

    raiz = tmp_path / "raiz"
    ferramenta = raiz / "tools" / "ferramenta-falsa"
    ferramenta.mkdir(parents=True)
    (ferramenta / "test_commit.py").write_text(TESTE_DA_FERRAMENTA, encoding="utf-8")

    monkeypatch.setattr(gerar_status_testes, "ROOT_DIR", str(raiz))
    monkeypatch.setenv("GIT_DIR", str(isca / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(isca / ".git" / "index"))

    resultado = gerar_status_testes._rodar_pytest("ferramenta-falsa")

    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_INDEX_FILE")
    assert resultado["status"] == "ok", resultado
    assert resultado["passed"] == 1
    assert _git(isca, "rev-list", "--count", "HEAD") == antes, "teste da ferramenta commitou no repositório do hook"
