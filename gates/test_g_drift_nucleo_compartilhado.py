#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_drift_nucleo_compartilhado.py - Testes determinísticos do gate G_DRIFT_NUCLEO_COMPARTILHADO.
Valida aprovação quando não há divergência silenciosa e reprovação estrita (exit 1) sob drift
não catalogado ou arquivos ausentes do baseline.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_DRIFT_NUCLEO_COMPARTILHADO.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def test_g_drift_nucleo_compartilhado_passa_no_repositorio():
    """Valida que o repositório atual passa com exit 0 no G_DRIFT_NUCLEO_COMPARTILHADO."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"Reprovou inesperadamente:\n{proc.stdout}\n{proc.stderr}"
    assert "APROVADO" in proc.stdout


def test_g_drift_nucleo_compartilhado_reprova_drift_nao_documentado(tmp_path):
    """Valida que G_DRIFT_NUCLEO_COMPARTILHADO reprova (exit 1) quando arquivos idênticos divergem."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_DRIFT_NUCLEO_COMPARTILHADO.py")

    dir_a = tmp_path / "tools" / "aidd-master" / "src" / "core"
    dir_b = tmp_path / "tools" / "aidd-enterprise" / "src" / "core"
    dir_a.mkdir(parents=True)
    dir_b.mkdir(parents=True)

    # Cria arquivo divergente
    (dir_a / "comum.py").write_text("# versao A\n", encoding="utf-8")
    (dir_b / "comum.py").write_text("# versao B divergente\n", encoding="utf-8")

    # Baseline espera idêntico
    baseline = {
        "arquivos": {
            "src/core": {
                "comum.py": {
                    "esperado_identico": True
                }
            }
        }
    }
    (fake_gates / "baseline_nucleo_compartilhado.json").write_text(json.dumps(baseline), encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_DRIFT_NUCLEO_COMPARTILHADO.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "drift nao documentado" in proc.stdout


def test_g_drift_nucleo_compartilhado_reprova_arquivo_nao_catalogado(tmp_path):
    """Valida que G_DRIFT_NUCLEO_COMPARTILHADO reprova (exit 1) quando arquivo novo não está no baseline."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_DRIFT_NUCLEO_COMPARTILHADO.py")

    dir_a = tmp_path / "tools" / "aidd-master" / "src" / "core"
    dir_b = tmp_path / "tools" / "aidd-enterprise" / "src" / "core"
    dir_a.mkdir(parents=True)
    dir_b.mkdir(parents=True)

    (dir_a / "novo.py").write_text("# arquivo novo\n", encoding="utf-8")
    (dir_b / "novo.py").write_text("# arquivo novo\n", encoding="utf-8")

    baseline = {"arquivos": {"src/core": {}}}
    (fake_gates / "baseline_nucleo_compartilhado.json").write_text(json.dumps(baseline), encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_DRIFT_NUCLEO_COMPARTILHADO.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "ausente do baseline" in proc.stdout
