#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ticket 9 (ciclo-03 VSA): G_SEGREDOS só LÊ a baseline.

Antes, rodar o hook duas vezes regravava .secrets.baseline (números de linha
atualizados + sanitização do filtro) e o pre-commit reprovava com "files were
modified by this hook". Agora o gate é idempotente: a baseline e o git status
ficam intactos; atualizar a baseline é um comando explícito e separado
(scripts/atualizar_baseline_segredos.py).
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

GATES_DIR = Path(__file__).resolve().parent
RAIZ_REAL = next(p.parent for p in GATES_DIR.parents if p.name == "modulos")
GATE = GATES_DIR / "G_SEGREDOS.py"
ESCOPO = GATES_DIR / "_escopo_commit.py"
ATUALIZAR = RAIZ_REAL / "scripts" / "atualizar_baseline_segredos.py"
GATES_REL = Path("modulos") / "04-nucleo-compartilhado" / "gates"

# Montada em runtime: o literal inteiro seria achado real do próprio G_SEGREDOS.
SEGREDO_AWS = "AKIA" + "IOSFODNN7EXAMPLE"

VARIAVEIS_DO_HOOK = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                     "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX")


def _env(modo):
    env = {k: v for k, v in os.environ.items() if k not in VARIAVEIS_DO_HOOK}
    env["AIDD_GATES_MODO"] = modo
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _git(raiz, *args):
    return subprocess.run(["git", "-c", "user.email=t@e.com", "-c", "user.name=T", "-c", "commit.gpgsign=false",
                           *args], cwd=str(raiz), check=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=_env("rapido"))


def _rodar(cmd, raiz, modo):
    return subprocess.run([sys.executable, *cmd], cwd=str(raiz), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=_env(modo))


@pytest.fixture
def repo(tmp_path):
    """Repo sintético com um segredo catalogado na baseline e linhas já deslocadas."""
    raiz = tmp_path / "repo"
    (raiz / GATES_REL).mkdir(parents=True)
    shutil.copyfile(GATE, raiz / GATES_REL / "G_SEGREDOS.py")
    shutil.copyfile(ESCOPO, raiz / GATES_REL / "_escopo_commit.py")
    (raiz / "config.py").write_text(f'chave = "{SEGREDO_AWS}"\n', encoding="utf-8")
    (raiz / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    _git(raiz, "init", "-q")
    _git(raiz, "add", "-A")
    scan = _rodar(["-m", "detect_secrets", "scan", "config.py"], raiz, "rapido")
    assert scan.returncode == 0, scan.stderr
    (raiz / ".secrets.baseline").write_text(scan.stdout, encoding="utf-8")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "base")
    # Desloca o segredo 2 linhas para baixo: o detect-secrets passa a querer
    # regravar line_number na baseline.
    (raiz / "config.py").write_text(f'# a\n# b\nchave = "{SEGREDO_AWS}"\n', encoding="utf-8")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "desloca linhas")
    return raiz


@pytest.mark.parametrize("modo", ["completo", "rapido"])
def test_gate_duas_vezes_nao_altera_baseline_nem_git_status(repo, modo):
    if modo == "rapido":
        (repo / "config.py").write_text(f'# a\n# b\n# c\nchave = "{SEGREDO_AWS}"\n', encoding="utf-8")
        _git(repo, "add", "config.py")
    antes = (repo / ".secrets.baseline").read_bytes()
    status_antes = _git(repo, "status", "--porcelain").stdout

    for _ in range(2):
        proc = _rodar([str(repo / GATES_REL / "G_SEGREDOS.py")], repo, modo)
        assert proc.returncode == 0, proc.stdout + proc.stderr

    assert (repo / ".secrets.baseline").read_bytes() == antes, "gate regravou a baseline"
    assert _git(repo, "status", "--porcelain").stdout == status_antes


def test_segredo_novo_continua_reprovando_sem_tocar_a_baseline(repo):
    valor_gh = "ghp_" + "".join(["1234567890", "abcdefghij", "klmnopqrst", "uvwxyz"])
    (repo / "outro.py").write_text(f'token = "{valor_gh}"\n', encoding="utf-8")
    _git(repo, "add", "outro.py")
    antes = (repo / ".secrets.baseline").read_bytes()
    proc = _rodar([str(repo / GATES_REL / "G_SEGREDOS.py")], repo, "rapido")
    assert proc.returncode == 1, proc.stdout
    assert (repo / ".secrets.baseline").read_bytes() == antes


def test_comando_explicito_atualiza_a_baseline(repo):
    antes = (repo / ".secrets.baseline").read_text(encoding="utf-8")
    assert '"line_number": 1' in antes
    proc = _rodar([str(ATUALIZAR), "--raiz", str(repo)], repo, "rapido")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    depois = (repo / ".secrets.baseline").read_text(encoding="utf-8")
    assert '"line_number": 3' in depois and '"line_number": 1' not in depois
    # Segunda execução não muda mais nada (idempotente).
    _rodar([str(ATUALIZAR), "--raiz", str(repo)], repo, "rapido")
    assert (repo / ".secrets.baseline").read_text(encoding="utf-8") == depois


def test_comando_explicito_aguenta_repo_grande_no_windows(repo):
    """Achado 07/10: o comando passava cada arquivo rastreado na linha de comando e,
    no repo real, estourava o limite do Windows (WinError 206, ~32 mil caracteres)."""
    pasta = repo / ("pasta_com_nome_bem_comprido_para_simular_o_repo_real_" * 2)
    pasta.mkdir()
    for i in range(400):
        (pasta / f"arquivo_numero_{i:04d}_com_nome_longo_igual_aos_do_ecossistema.txt").write_text(
            "nada\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "muitos arquivos")
    proc = _rodar([str(ATUALIZAR), "--raiz", str(repo)], repo, "rapido")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    depois = (repo / ".secrets.baseline").read_text(encoding="utf-8")
    assert '"line_number": 3' in depois, "segredo catalogado sumiu da baseline"
