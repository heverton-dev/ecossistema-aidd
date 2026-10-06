#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_componente_agnostico.py - Testes determinísticos do gate G_COMPONENTE_AGNOSTICO.
Valida aprovação com cobertura total de componentes e reprovação estrita (exit 1)
sob divergência de distribuição multi-harness.
"""

import json
import os
import shutil
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_COMPONENTE_AGNOSTICO.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def test_g_componente_agnostico_passa_no_repositorio():
    """Valida que o repositório atual passa com exit 0 no G_COMPONENTE_AGNOSTICO."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"Reprovou inesperadamente:\n{proc.stdout}\n{proc.stderr}"
    assert "APROVADO" in proc.stdout


def test_g_componente_agnostico_reprova_sob_problemas_de_distribuicao(tmp_path):
    """Valida que G_COMPONENTE_AGNOSTICO reprova (exit 1) quando gestor_componentes relata problemas."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_COMPONENTE_AGNOSTICO.py")

    manifesto = {
        "tipos_componente": {
            "skill": {"pasta_fonte": "skills"}
        },
        "escopos": ["compartilhado"]
    }
    (fake_gates / "manifesto_harnesses.json").write_text(json.dumps(manifesto), encoding="utf-8")

    fake_scripts = tmp_path / "scripts"
    fake_scripts.mkdir()
    # Simula gestor_componentes relatando inconsistência real
    (fake_scripts / "gestor_componentes.py").write_text(
        "def carregar_manifesto():\n"
        "    return {'tipos_componente': {'skill': {'pasta_fonte': 'skills'}}, 'escopos': ['compartilhado']}\n"
        "def verify(tipo='todos', ferramenta=None):\n"
        "    return 1, ['Skill [aidd-teste] ausente no harness .claude']\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(fake_gates / "G_COMPONENTE_AGNOSTICO.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "Quality Gate REPROVADO" in proc.stdout
    assert "Skill [aidd-teste] ausente no harness .claude" in proc.stdout
