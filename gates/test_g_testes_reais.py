#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_testes_reais.py - Testes determinísticos do gate G_TESTES_REAIS.
Valida aprovação com suítes verdes e reprovação estrita (exit 1) quando
há testes falhando ou skips não autorizados.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_TESTES_REAIS.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def _criar_arvore_sintetica(tmp_path):
    """Cria uma estrutura de diretórios sintética com o gate copiado."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_TESTES_REAIS.py")

    fake_tools = tmp_path / "tools" / "aidd-forge"
    fake_tools.mkdir(parents=True)
    return fake_gates, fake_tools


def test_g_testes_reais_passa_com_sucesso_sintetico(tmp_path):
    """Valida que G_TESTES_REAIS aprova (exit 0) quando a suíte passa 100%."""
    fake_gates, fake_tools = _criar_arvore_sintetica(tmp_path)

    test_file = fake_tools / "test_ok.py"
    test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    env = os.environ.copy()
    env["AIDD_TESTES_REAIS_FERRAMENTAS"] = "aidd-forge"
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        [sys.executable, str(fake_gates / "G_TESTES_REAIS.py")],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    assert proc.returncode == 0, f"Falhou inesperadamente:\n{proc.stdout}\n{proc.stderr}"
    assert "APROVADO" in proc.stdout


def test_g_testes_reais_reprova_com_falha_de_teste(tmp_path):
    """Valida que G_TESTES_REAIS reprova com exit 1 quando há falha real de teste."""
    fake_gates, fake_tools = _criar_arvore_sintetica(tmp_path)

    test_file = fake_tools / "test_fail.py"
    test_file.write_text("def test_falha():\n    assert False, 'Falha induzida'\n", encoding="utf-8")

    env = os.environ.copy()
    env["AIDD_TESTES_REAIS_FERRAMENTAS"] = "aidd-forge"
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        [sys.executable, str(fake_gates / "G_TESTES_REAIS.py")],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "G_TESTES_REAIS REPROVADO" in proc.stdout
    assert "FALHOU" in proc.stdout


def test_g_testes_reais_reprova_com_skip_nao_autorizado(tmp_path):
    """Valida que G_TESTES_REAIS reprova com exit 1 quando há teste skipped sem autorização."""
    fake_gates, fake_tools = _criar_arvore_sintetica(tmp_path)

    test_file = fake_tools / "test_skip.py"
    test_file.write_text("import pytest\n@pytest.mark.skip(reason='Sem permissao')\ndef test_pulado():\n    pass\n", encoding="utf-8")

    env = os.environ.copy()
    env["AIDD_TESTES_REAIS_FERRAMENTAS"] = "aidd-forge"
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        [sys.executable, str(fake_gates / "G_TESTES_REAIS.py")],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "ORÇAMENTO ESTOURADO" in proc.stdout or "G_TESTES_REAIS REPROVADO" in proc.stdout
