# -*- coding: utf-8 -*-
"""Ticket 2 (ciclo-03 VSA): G_COPIA_UNICA_VSA acusa cópia dupla (aviso=0, bloqueio=1)."""

import os
import subprocess
import sys
from pathlib import Path

GATE = Path(__file__).resolve().parent / "G_COPIA_UNICA_VSA.py"


def _gravar(raiz: Path, rel: str, conteudo: str = "x = 1\n") -> None:
    caminho = raiz / rel
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8", newline="\n")


def _repo(tmp_path: Path, arquivos: list[str]) -> Path:
    raiz = tmp_path / "repo"
    for rel in arquivos:
        _gravar(raiz, rel)
    subprocess.run(["git", "init", "-q"], cwd=raiz, check=True)
    subprocess.run(["git", "add", "-A"], cwd=raiz, check=True)
    return raiz


def _rodar(raiz: Path, modo: str | None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_INDEX_FILE", "AIDD_COPIA_UNICA_MODO")}
    if modo is not None:
        env["AIDD_COPIA_UNICA_MODO"] = modo
    return subprocess.run(
        [sys.executable, str(GATE), "--raiz", str(raiz)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
    )


DUPLICADO = [
    "tools/aidd-ops/a.py",
    "modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/a.py",
    "gates/G_X.py",
    "modulos/04-nucleo-compartilhado/gates/G_X.py",
    "componentes/compartilhado/skills/aidd-tdd/SKILL.md",
    "modulos/01-governanca-e-qualidade/skills/aidd-tdd/SKILL.md",
]


def test_acusa_ferramenta_gate_e_skill_duplicados_em_aviso(tmp_path):
    proc = _rodar(_repo(tmp_path, DUPLICADO), "aviso")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "aidd-ops" in proc.stdout
    assert "G_X.py" in proc.stdout
    assert "aidd-tdd" in proc.stdout
    assert "3 violação(ões)" in proc.stdout


def test_bloqueio_reprova_com_exit_1(tmp_path):
    proc = _rodar(_repo(tmp_path, DUPLICADO), "bloqueio")
    assert proc.returncode == 1, proc.stdout + proc.stderr


def test_padrao_e_aviso(tmp_path):
    proc = _rodar(_repo(tmp_path, DUPLICADO), None)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "aviso" in proc.stdout


def test_moldes_de_projeto_do_almoxarifado_nao_contam(tmp_path):
    raiz = _repo(tmp_path, [
        "modulos/04-nucleo-compartilhado/gates/G_Y.py",
        "modulos/01-governanca-e-qualidade/core/aidd-forge/aidd_forge/templates/gates/G_Y.py",
    ])
    proc = _rodar(raiz, "bloqueio")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_copia_unica_passa_em_bloqueio(tmp_path):
    raiz = _repo(tmp_path, [
        "modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/a.py",
        "modulos/04-nucleo-compartilhado/gates/G_X.py",
        "componentes/compartilhado/skills/aidd-tdd/SKILL.md",
    ])
    proc = _rodar(raiz, "bloqueio")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_modo_invalido_sai_com_1(tmp_path):
    proc = _rodar(_repo(tmp_path, ["gates/G_Z.py"]), "talvez")
    assert proc.returncode == 1


def test_saida_so_binaria_sem_exit_codes():
    fonte = GATE.read_text(encoding="utf-8")
    assert "exit_codes" not in fonte
