# -*- coding: utf-8 -*-
"""Testes de fallback e resiliência para aidd-spec (Ticket 5 / D11 / DoD 4)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import fallback as spec_fallback

def test_fallback_recupera_dados_parciais():
    texto_corrompido = """
## 1. Context & Explicit Non-Goals
Contexto recuperável.
## 3. Invariants & Business Rules
1. Invariante 1.
\x00\x00 Linha nula descartada.
"""
    dados, avisos = spec_fallback.extrair_spec_resiliente(texto_corrompido)
    assert "contexto" in dados["secoes_presentes"]
    assert len(dados["invariantes"]) == 1
    assert len(avisos) > 0
