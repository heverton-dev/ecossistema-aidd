# -*- coding: utf-8 -*-
"""Testes de isolamento para aidd-spec (Ticket 2 / D3 / DoD 2)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import isolamento as spec_isolamento

def test_isolamento_permite_docs_e_secoes():
    manager = spec_isolamento.SpecWorktreeManager(Path.cwd())
    assert manager.validar_caminho_escrita(Path.cwd() / "docs" / "specs" / "spec.md") is True
    assert manager.validar_caminho_escrita(Path.cwd() / "secoes" / "spec.json") is True

def test_isolamento_bloqueia_fora_de_diretorio_autorizado():
    manager = spec_isolamento.SpecWorktreeManager(Path.cwd())
    with pytest.raises(spec_isolamento.SandboxViolationError):
        manager.validar_caminho_escrita(Path.cwd() / "src" / "perigo.py")
