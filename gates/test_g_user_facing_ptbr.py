#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prova que G_USER_FACING_PTBR morde (Lei #13) — ISSUE-USA-0004."""

import os
import shutil
from pathlib import Path

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_USER_FACING_PTBR.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def _montar(tmp_path, readme: str, com_perfil: bool = True):
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_USER_FACING_PTBR.py")
    (tmp_path / "README.md").write_text(readme, encoding="utf-8")
    (tmp_path / "GEMINI.md").write_text("Forma da Resposta (Rule 10)\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    perfil = 'parser.add_argument("--perfil", choices=["leigo", "tecnico"])\n# leigo\n' if com_perfil else "parser.add_argument('--json')\n"
    (tmp_path / "scripts" / "preflight_host.py").write_text(perfil, encoding="utf-8")


def test_g_user_facing_ptbr_passa_no_repositorio():
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"reprovou:\n{proc.stdout}\n{proc.stderr}"


def test_g_user_facing_ptbr_failing_path_jargao_cru(tmp_path):
    """Jargão sem tradução em README => exit 1 (Lei #13)."""
    _montar(tmp_path, "# App\n\nOs quality gates e o drift do worktree estao verdes.\n")
    proc = rodar_gate(str(tmp_path / "gates" / "G_USER_FACING_PTBR.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "G_USER_FACING_PTBR" in proc.stdout


def test_g_user_facing_ptbr_failing_path_sem_perfil(tmp_path):
    """preflight sem --perfil leigo => exit 1 (Lei #13)."""
    _montar(tmp_path, "# App\n\nTudo pronto.\n", com_perfil=False)
    proc = rodar_gate(str(tmp_path / "gates" / "G_USER_FACING_PTBR.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "perfil" in proc.stdout.lower()


def test_g_user_facing_ptbr_aceita_traducao(tmp_path):
    """Jargão com tradução na mesma linha não reprova."""
    _montar(
        tmp_path,
        "# App\n\nQuality gate (portão de qualidade) aprovado.\nVSA (Arquitetura por Fatias Verticais) ok.\n",
    )
    proc = rodar_gate(str(tmp_path / "gates" / "G_USER_FACING_PTBR.py"), cwd=str(tmp_path))
    assert proc.returncode == 0, proc.stdout
