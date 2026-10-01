# -*- coding: utf-8 -*-
"""Testes de fallback headless para aidd-grill (Ticket 5 / D11 / DoD 4)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-grill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import fallback as grill_fallback

def test_fallback_sintetiza_premissas_headless():
    texto = """
### 1. Banco de dados para a aplicação?
- (A) Postgres
- (B) SQLite
**Recomendado:** Opção B, porque opera sem infraestrutura externa.
"""
    bloco, premissas, avisos = grill_fallback.sintetizar_premissas_headless(texto)
    assert "### Consolidated Assumptions" in bloco
    assert len(premissas) == 1
    assert premissas[0]["numero"] == 1
    assert "infraestrutura externa" in premissas[0]["premissa_assumida"]
