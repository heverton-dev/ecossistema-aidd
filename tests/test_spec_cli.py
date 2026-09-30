# -*- coding: utf-8 -*-
"""Testes unitários de CLI para aidd-spec (Ticket 1 / D2 / DoD 1)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import cli as spec_cli

SPEC_TESTE = """
## 1. Context & Explicit Non-Goals
- Objetivo do teste.
## 2. Contracts & Typed Interfaces
- Interface A.
## 3. Invariants & Business Rules
1. Invariante 1.
## 4. Binary Acceptance Criteria
- Comando retorna exit code 0.
## 5. Failure & Degradation Modes
- Retorna status 500.
"""

def test_cli_validar_sucesso(tmp_path):
    arq = tmp_path / "spec.md"
    arq.write_text(SPEC_TESTE, encoding="utf-8")
    assert spec_cli.main(["validar", "--arquivo", str(arq)]) == 0

def test_cli_validar_arquivo_inexistente(tmp_path):
    arq = tmp_path / "nao_existe.md"
    assert spec_cli.main(["validar", "--arquivo", str(arq)]) == 1

def test_cli_exportar_sucesso(tmp_path):
    arq = tmp_path / "spec.md"
    arq.write_text(SPEC_TESTE, encoding="utf-8")
    out = Path.cwd() / "docs" / "specs" / "teste_export.json"
    try:
        ret = spec_cli.main(["exportar", "--arquivo", str(arq), "--output", str(out)])
        assert ret == 0
        assert out.exists()
    finally:
        out.unlink(missing_ok=True)
