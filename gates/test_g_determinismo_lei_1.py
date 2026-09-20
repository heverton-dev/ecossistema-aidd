#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DE PROVA QUE MORDE: test_g_determinismo_lei_1.py
=============================================================================
Validação estrita em runtime (Lei #13 / ISSUE-0020):
  1. Caminho feliz: suíte de gates atual é 100% determinística (exit 0).
  2. Cenário de reprovação deliberada: injeção de script sintético em gates/
     importando SDK de LLM bloqueado (openai/anthropic) causa exit 1 imediato.
"""

import os
import subprocess
import sys
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES_DIR = os.path.join(ROOT_DIR, "gates")
GATE_SCRIPT = os.path.join(GATES_DIR, "G_DETERMINISMO_LEI_1.py")


def test_aprova_gates_determinismo_conformes():
    """Valida caminho feliz: todos os arquivos em gates/ passam sem uso de LLM."""
    res = subprocess.run(
        [sys.executable, GATE_SCRIPT],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0, f"Gate reprovou indevidamente: {res.stdout}\n{res.stderr}"
    assert "SUCESSO" in res.stdout
    assert "LIMITE METROLÓGICO" in res.stdout


def test_reprova_quando_llm_sdk_injetado_em_gates():
    """Prova que o portão morde (Lei #13): injeção de import openai/anthropic em gates/ deve retornar exit 1."""
    synthetic_gate_file = os.path.join(GATES_DIR, "G_SYNTHETIC_LLM_TRAP.py")
    try:
        with open(synthetic_gate_file, "w", encoding="utf-8") as f:
            f.write("# Injeção sintética para testar reprovação da Lei #1\n")
            f.write("import openai\n")
            f.write("def dummy():\n    pass\n")

        res = subprocess.run(
            [sys.executable, GATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            encoding="utf-8",
            errors="replace",
        )
        assert res.returncode == 1, f"Gate deveria ter falhado (exit 1), mas retornou {res.returncode}: {res.stdout}"
        assert "G_SYNTHETIC_LLM_TRAP.py" in res.stdout
        assert "Importação de SDK de LLM proibido" in res.stdout
    finally:
        if os.path.exists(synthetic_gate_file):
            os.remove(synthetic_gate_file)


def test_reprova_quando_import_from_llm_sdk_injetado():
    """Prova que o portão morde com 'from anthropic import Anthropic' (exit 1)."""
    synthetic_gate_file = os.path.join(GATES_DIR, "G_SYNTHETIC_ANTHROPIC_TRAP.py")
    try:
        with open(synthetic_gate_file, "w", encoding="utf-8") as f:
            f.write("# Injeção sintética from anthropic\n")
            f.write("from anthropic import Anthropic\n")
            f.write("def dummy():\n    pass\n")

        res = subprocess.run(
            [sys.executable, GATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            encoding="utf-8",
            errors="replace",
        )
        assert res.returncode == 1, f"Gate deveria ter falhado (exit 1), mas retornou {res.returncode}"
        assert "G_SYNTHETIC_ANTHROPIC_TRAP.py" in res.stdout
    finally:
        if os.path.exists(synthetic_gate_file):
            os.remove(synthetic_gate_file)
