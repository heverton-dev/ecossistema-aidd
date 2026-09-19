#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_harness_compat.py - Testes determinísticos do gate G_HARNESS_COMPAT.
Valida aprovação quando artefatos multi-harness estão íntegros e sincronizados
e reprovação estrita (exit 1) sob drift, ausência de ponteiro ou gates não documentados.
"""

import os
import shutil
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_HARNESS_COMPAT.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def test_g_harness_compat_passa_no_repositorio():
    """Valida que o repositório atual passa com exit 0 no G_HARNESS_COMPAT."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"Reprovou inesperadamente:\n{proc.stdout}\n{proc.stderr}"
    assert "APROVADO" in proc.stdout


def test_g_harness_compat_reprova_ponteiro_quebrado(tmp_path):
    """Valida que G_HARNESS_COMPAT reprova (exit 1) quando arquivo ponteiro não referencia AGENTS.md."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_HARNESS_COMPAT.py")

    fake_scripts = tmp_path / "scripts"
    fake_scripts.mkdir()
    (fake_scripts / "gestor_componentes.py").write_text(
        "class Relatorio:\n"
        "    total_componentes = 1\n"
        "    modificados = []\n"
        "    divergentes = []\n"
        "    orfaos = []\n"
        "    boms = []\n"
        "def verify_detallado():\n"
        "    return Relatorio()\n",
        encoding="utf-8"
    )

    # Cria ponteiro quebrado
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "CLAUDE.md").write_text("Arquivo sem referencia ao agents", encoding="utf-8")

    fake_cursor = tmp_path / ".cursor" / "rules"
    fake_cursor.mkdir(parents=True)
    (fake_cursor / "aidd.md").write_text("Referencia AGENTS.md", encoding="utf-8")

    (tmp_path / "AGENTS.md").write_text("# Regras\ngates/G_HARNESS_COMPAT.py\n", encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_HARNESS_COMPAT.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "Arquivo-ponteiro .claude/CLAUDE.md existe mas não referencia AGENTS.md" in proc.stdout


def test_g_harness_compat_reprova_gate_nao_documentado(tmp_path):
    """Valida que G_HARNESS_COMPAT reprova (exit 1) quando existe gate em disco não documentado."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_HARNESS_COMPAT.py")
    (fake_gates / "G_FANTASMA.py").write_text("# gate nao documentado", encoding="utf-8")

    fake_scripts = tmp_path / "scripts"
    fake_scripts.mkdir()
    (fake_scripts / "gestor_componentes.py").write_text(
        "class Relatorio:\n"
        "    total_componentes = 1\n"
        "    modificados = []\n"
        "    divergentes = []\n"
        "    orfaos = []\n"
        "    boms = []\n"
        "def verify_detallado():\n"
        "    return Relatorio()\n",
        encoding="utf-8"
    )

    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "CLAUDE.md").write_text("Ver AGENTS.md", encoding="utf-8")

    fake_cursor = tmp_path / ".cursor" / "rules"
    fake_cursor.mkdir(parents=True)
    (fake_cursor / "aidd.md").write_text("Ver AGENTS.md", encoding="utf-8")

    # Documenta apenas G_HARNESS_COMPAT.py, omitindo G_FANTASMA.py
    (tmp_path / "AGENTS.md").write_text("# Regras\ngates/G_HARNESS_COMPAT.py\n", encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_HARNESS_COMPAT.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "Gate(s) em disco mas não documentado(s)" in proc.stdout
    assert "G_FANTASMA.py" in proc.stdout
