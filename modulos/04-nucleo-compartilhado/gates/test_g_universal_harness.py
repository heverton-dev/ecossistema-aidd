#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_universal_harness.py - Testes determinísticos do gate G_UNIVERSAL_HARNESS.
Valida aprovação com paridade universal e reprovação estrita (exit 1) quando
há ausência de artefatos ou inconsistência entre harnesses.
"""

import json
import os
import shutil
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_UNIVERSAL_HARNESS.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def test_g_universal_harness_passa_no_repositorio():
    """Valida que o repositório atual passa com exit 0 no G_UNIVERSAL_HARNESS."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"Reprovou inesperadamente:\n{proc.stdout}\n{proc.stderr}"
    assert "APROVADO" in proc.stdout


def test_g_universal_harness_reprova_quando_skill_falta_em_harness(tmp_path):
    """Valida que G_UNIVERSAL_HARNESS reprova (exit 1) quando uma skill não está em todos os harnesses."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_UNIVERSAL_HARNESS.py")

    manifesto = {
        "harnesses_suportados": {
            "claude-code": {"prefixo_pasta": ".claude"},
            "opencode": {"prefixo_pasta": ".opencode"}
        }
    }
    (fake_gates / "manifesto_harnesses.json").write_text(json.dumps(manifesto), encoding="utf-8")
    (fake_gates / "dependencias_externas.json").write_text(json.dumps({"mcps": {}}), encoding="utf-8")

    fake_scripts = tmp_path / "scripts"
    fake_scripts.mkdir()
    (fake_scripts / "gestor_componentes.py").write_text("IGNORAR_DIRS = set()\n", encoding="utf-8")
    (fake_scripts / "gestor_dependencias.py").write_text(
        "DESTINOS_MCP = {}\ndef carregar_manifesto():\n    return {'mcps': {}}\n",
        encoding="utf-8"
    )

    fake_skills = tmp_path / "componentes" / "compartilhado" / "skills" / "skill-teste"
    fake_skills.mkdir(parents=True)
    (fake_skills / "SKILL.md").write_text("# Skill", encoding="utf-8")

    # Presente apenas no claude-code, ausente no opencode
    claude_dest = tmp_path / ".claude" / "skills" / "skill-teste"
    claude_dest.mkdir(parents=True)
    (claude_dest / "SKILL.md").write_text("# Skill", encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_UNIVERSAL_HARNESS.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "[SKILL AUSENTE]" in proc.stdout
    assert "opencode" in proc.stdout


def test_g_universal_harness_reprova_hook_sintaxe_invalida(tmp_path):
    """Valida que G_UNIVERSAL_HARNESS reprova (exit 1) quando há hook Python com sintaxe inválida."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_UNIVERSAL_HARNESS.py")

    manifesto = {"harnesses_suportados": {}}
    (fake_gates / "manifesto_harnesses.json").write_text(json.dumps(manifesto), encoding="utf-8")
    (fake_gates / "dependencias_externas.json").write_text(json.dumps({"mcps": {}}), encoding="utf-8")

    fake_scripts = tmp_path / "scripts"
    fake_scripts.mkdir()
    (fake_scripts / "gestor_componentes.py").write_text("IGNORAR_DIRS = set()\n", encoding="utf-8")
    (fake_scripts / "gestor_dependencias.py").write_text(
        "DESTINOS_MCP = {}\ndef carregar_manifesto():\n    return {'mcps': {}}\n",
        encoding="utf-8"
    )

    fake_hooks = tmp_path / "componentes" / "compartilhado" / "hooks"
    fake_hooks.mkdir(parents=True)
    (fake_hooks / "broken_hook.py").write_text("def broken( syntax error here !!!", encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_UNIVERSAL_HARNESS.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "[HOOK SINTAXE INVALIDA]" in proc.stdout
