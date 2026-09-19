#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_zero_headless.py - Testes determinísticos do gate G_ZERO_HEADLESS.
Valida aprovação em repositório íntegro e reprovação (exit 1) quando a
condição protegida é violada.
"""

import os
import shutil
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_ZERO_HEADLESS.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def test_g_zero_headless_passa_no_repositorio():
    """Valida que o repositório atual passa com exit 0 no G_ZERO_HEADLESS."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"G_ZERO_HEADLESS reprovou com saida:\n{proc.stdout}\n{proc.stderr}"
    assert "APROVADO" in proc.stdout


def test_g_zero_headless_reprova_sem_interactive_true(tmp_path):
    """Valida que G_ZERO_HEADLESS reprova (exit 1) quando interactive: bool = True está ausente."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_ZERO_HEADLESS.py")

    fake_engine_dir = tmp_path / "componentes" / "compartilhado" / "skills" / "orca-plan-orchestrator" / "scripts"
    fake_engine_dir.mkdir(parents=True)
    fake_engine = fake_engine_dir / "orchestrator_engine.py"
    fake_engine.write_text("def run(interactive: bool = False):\n    pass\n", encoding="utf-8")

    fake_eco = tmp_path / "ecossistema.py"
    fake_eco.write_text("--dangerously-force-headless\n", encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_ZERO_HEADLESS.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "orchestrator_engine.py deve ter interactive: bool = True" in proc.stdout


def test_g_zero_headless_reprova_sem_flag_headless_no_ecossistema(tmp_path):
    """Valida que G_ZERO_HEADLESS reprova (exit 1) quando a flag headless está ausente no ecossistema.py."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_ZERO_HEADLESS.py")

    fake_engine_dir = tmp_path / "componentes" / "compartilhado" / "skills" / "orca-plan-orchestrator" / "scripts"
    fake_engine_dir.mkdir(parents=True)
    fake_engine = fake_engine_dir / "orchestrator_engine.py"
    fake_engine.write_text("def run(interactive: bool = True):\n    pass\n", encoding="utf-8")

    fake_eco = tmp_path / "ecossistema.py"
    fake_eco.write_text("# ecossistema sem a flag obrigatoria\n", encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_ZERO_HEADLESS.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "ecossistema.py deve declarar a opcao --dangerously-force-headless" in proc.stdout
