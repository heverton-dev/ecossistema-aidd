#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DE PROVA QUE MORDE: test_g_disciplina_teste_ferramenta.py
=============================================================================
Validação estrita em runtime (Lei #13 / ISSUE-0023):
  1. Caminho feliz:
     - Changeset sem alterações sob tools/ passa com exit 0.
     - Changeset com ferramenta sob tools/ E relatório atualizado passa com exit 0.
  2. Cenário de reprovação deliberada (exit 1):
     - Changeset que toca tools/<ferramenta>/ sem relatório em docs/teste-end-to-end/
       é sumariamente bloqueado com exit 1.
"""

import os
import subprocess
import sys
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES_DIR = os.path.join(ROOT_DIR, "gates")
GATE_SCRIPT = os.path.join(GATES_DIR, "G_DISCIPLINA_TESTE_FERRAMENTA.py")


def test_aprova_quando_nenhuma_ferramenta_tocada():
    """Valida que alterações fora de tools/ (ex: docs/, gates/) passam sem exigir relatório."""
    res = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--files", "gates/G_SAIDA_BINARIA.py", "README.md"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0
    assert "SUCESSO" in res.stdout
    assert "Nenhuma ferramenta em tools/ alterada" in res.stdout


def test_aprova_quando_ferramenta_tocada_com_relatorio_atualizado():
    """Valida aprovação quando ferramenta sob tools/ é acompanhada de relatório de teste."""
    arquivos = [
        "tools/aidd-generator/scripts/core/detector.py",
        "docs/teste-end-to-end/relatorio-teste-end-to-end.md",
    ]
    res = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--files"] + arquivos,
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0
    assert "SUCESSO" in res.stdout
    assert "com relatório atualizado" in res.stdout


def test_reprova_quando_ferramenta_tocada_sem_relatorio():
    """Prova que o portão morde (Lei #13): alteração em tools/ sem relatório causa exit 1."""
    arquivos = [
        "tools/aidd-generator/scripts/core/detector.py",
        "tools/aidd-generator/templates/server.py",
    ]
    res = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--files"] + arquivos,
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 1, f"Deveria ter reprovado com exit 1, retornou {res.returncode}"
    assert "FALHA" in res.stdout
    assert "Ferramenta(s) alterada(s) sem atualização de relatório" in res.stdout
    assert "aidd-generator" in res.stdout
    assert "Lei #9" in res.stdout
