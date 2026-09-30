# -*- coding: utf-8 -*-
"""Testes de rollback para aidd-spec (Ticket 8 / D14 / DoD 7)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import rollback as spec_rollback

def test_rollback_remove_arquivos(tmp_path):
    f1 = tmp_path / "temp1.json"
    f1.write_text("{}", encoding="utf-8")
    assert f1.exists()
    assert spec_rollback.limpar_artefatos_parciais([f1]) is True
    assert not f1.exists()
