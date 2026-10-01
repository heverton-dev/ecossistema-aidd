# -*- coding: utf-8 -*-
"""Testes unitários de CLI para aidd-grill (Ticket 1 / D2 / DoD 1)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-grill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import cli as grill_cli

RODADA_TESTE = """
### 1. Pergunta teste?
- (A) Opcao 1
- (B) Opcao 2
**Recomendado:** Opção 1, porque resolve o problema de imediato.
"""

def test_cli_validar_sucesso(tmp_path):
    arq = tmp_path / "grill.md"
    arq.write_text(RODADA_TESTE, encoding="utf-8")
    assert grill_cli.main(["validar", "--arquivo", str(arq)]) == 0

def test_cli_validar_arquivo_inexistente(tmp_path):
    arq = tmp_path / "nao_existe.md"
    assert grill_cli.main(["validar", "--arquivo", str(arq)]) == 1

def test_cli_exportar_sucesso(tmp_path):
    arq = tmp_path / "grill.md"
    arq.write_text(RODADA_TESTE, encoding="utf-8")
    out = Path.cwd() / "docs" / "specs" / "teste_grill_export.json"
    try:
        ret = grill_cli.main(["exportar", "--arquivo", str(arq), "--output", str(out)])
        assert ret == 0
        assert out.exists()
    finally:
        out.unlink(missing_ok=True)
