# -*- coding: utf-8 -*-
"""Testes de parser canônico para aidd-spec (Ticket 3 / D4 / DoD 3)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import parser as spec_parser

def test_parser_captura_5_secoes_com_sucesso():
    texto = """
# Spec
## 1. Context & Explicit Non-Goals
Contexto aqui.
## 2. Contracts & Typed Interfaces
Contratos aqui.
## 3. Invariants & Business Rules
Invariantes aqui.
## 4. Binary Acceptance Criteria
Critérios aqui.
## 5. Failure & Degradation Modes
Modos de falha aqui.
"""
    secoes, erros = spec_parser.parsear_especificacao_markdown(texto)
    assert not erros
    assert len(secoes) == 5
    assert "contexto" in secoes
    assert "contratos" in secoes
    assert "invariantes" in secoes
    assert "criterios_binarios" in secoes
    assert "modos_falha" in secoes

def test_parser_rejeita_spec_incompleta():
    texto = """
# Spec
## 1. Context & Explicit Non-Goals
Contexto apenas.
"""
    secoes, erros = spec_parser.parsear_especificacao_markdown(texto)
    assert len(erros) >= 4
    assert not secoes
