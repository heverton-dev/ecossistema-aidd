# -*- coding: utf-8 -*-
"""Testes de isolamento para aidd-grill (Ticket 2 / D3 / DoD 2)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-grill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import isolamento as grill_isolamento

def test_isolamento_permite_docs_e_secoes():
    manager = grill_isolamento.GrillWorktreeManager(Path.cwd())
    assert manager.validar_caminho_escrita(Path.cwd() / "docs" / "specs" / "grill.json") is True
    assert manager.validar_caminho_escrita(Path.cwd() / "secoes" / "grill.json") is True

def test_isolamento_bloqueia_fora_de_diretorio_autorizado():
    manager = grill_isolamento.GrillWorktreeManager(Path.cwd())
    with pytest.raises(grill_isolamento.SandboxViolationError):
        manager.validar_caminho_escrita(Path.cwd() / "src" / "perigo.py")
