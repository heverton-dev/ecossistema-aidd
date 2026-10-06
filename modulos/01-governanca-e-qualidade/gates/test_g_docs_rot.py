#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_docs_rot.py - Testes determinísticos do gate G_DOCS_ROT.
Valida aprovação com documentação íntegra e reprovação com links quebrados em árvore sintética.
"""

import os
import shutil
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_DOCS_ROT.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def test_g_docs_rot_passa_no_repositorio():
    """Valida que o repositório atual passa com exit 0 no G_DOCS_ROT."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"G_DOCS_ROT reprovou com saida:\n{proc.stdout}\n{proc.stderr}"
    assert "APROVADO" in proc.stdout


def test_g_docs_rot_detecta_link_quebrado(tmp_path):
    """Valida que G_DOCS_ROT reprova (exit 1) quando existe link relativo quebrado."""
    # Monta estrutura sintética
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_DOCS_ROT.py")

    fake_docs = tmp_path / "docs" / "protocolos"
    fake_docs.mkdir(parents=True)
    
    # Cria arquivo com link quebrado
    doc_com_link_quebrado = fake_docs / "GUIA.md"
    doc_com_link_quebrado.write_text(
        "# Guia\n\nVeja o [Documento Inexistente](arquivo_fantasma.md).",
        encoding="utf-8"
    )

    proc = rodar_gate(str(fake_gates / "G_DOCS_ROT.py"), cwd=str(tmp_path))
    assert proc.returncode == 1
    assert "Link quebrado" in proc.stdout
    assert "arquivo_fantasma.md" in proc.stdout


def test_g_docs_rot_detecta_plano_orfaos(tmp_path):
    """Valida que G_DOCS_ROT reprova (exit 1) quando existe plano fora dos buckets canônicos."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_DOCS_ROT.py")

    fake_planos = tmp_path / "docs" / "planos"
    fake_planos.mkdir(parents=True)
    # Cria pasta de plano solta
    (fake_planos / "PLAN-9999-solto").mkdir()

    proc = rodar_gate(str(fake_gates / "G_DOCS_ROT.py"), cwd=str(tmp_path))
    assert proc.returncode == 1
    assert "Diretório de plano solto/órfão" in proc.stdout
    assert "PLAN-9999-solto" in proc.stdout
