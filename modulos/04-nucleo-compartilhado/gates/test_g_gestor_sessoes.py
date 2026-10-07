# -*- coding: utf-8 -*-
"""Prova que G_GESTOR_SESSOES morde (Lei #13)."""

import os
import shutil
import sys
from pathlib import Path

from _gate_test_utils import rodar_gate

GATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_GESTOR_SESSOES.py")
from pathlib import Path as _Path
ROOT_DIR = str(next((p.parent for p in _Path(__file__).resolve().parents if p.name == "modulos"), _Path(__file__).resolve().parent.parent))  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)


def test_g_gestor_sessoes_passa_no_repositorio():
    """Caminho nominal no repositório ativo deve retornar exit 0."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"reprovou:\n{proc.stdout}\n{proc.stderr}"


def test_g_gestor_sessoes_morde_se_script_ausente(tmp_path):
    """Repo sintético sem scripts/gestor_sessoes.py deve retornar exit 1 (Lei #13)."""
    gates_dir = tmp_path / "modulos" / "04-nucleo-compartilhado" / "gates"
    gates_dir.mkdir(parents=True)
    shutil.copy2(GATE_PATH, gates_dir / "G_GESTOR_SESSOES.py")

    proc = rodar_gate(str(gates_dir / "G_GESTOR_SESSOES.py"), cwd=str(tmp_path))
    assert proc.returncode == 1
    assert "REPROVADO" in proc.stdout or "não encontrado" in proc.stdout


def test_g_gestor_sessoes_morde_se_funcao_faltar(tmp_path):
    """Repo sintético com script incompleto deve retornar exit 1 (Lei #13)."""
    gates_dir = tmp_path / "modulos" / "04-nucleo-compartilhado" / "gates"
    gates_dir.mkdir(parents=True)
    shutil.copy2(GATE_PATH, gates_dir / "G_GESTOR_SESSOES.py")

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "gestor_sessoes.py").write_text(
        "# Script inválido sem funções obrigatórias\ndef foo(): pass\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(gates_dir / "G_GESTOR_SESSOES.py"), cwd=str(tmp_path))
    assert proc.returncode == 1
    assert "REPROVADO" in proc.stdout
