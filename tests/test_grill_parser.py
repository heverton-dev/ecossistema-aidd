# -*- coding: utf-8 -*-
"""Testes de parser canônico para aidd-grill (Ticket 3 / D4 / DoD 3)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-grill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import parser as grill_parser

def test_parser_captura_perguntas_e_recomendacao():
    texto = """
# Rodada 1
### 1. Pergunta A?
- (A) Opcao 1
- (B) Opcao 2
**Recomendado:** Opcao 1, porque simplifica o fluxo.

### 2. Pergunta B?
**Recomendado:** Opcao 2, pois economiza memoria.
"""
    perguntas, erros = grill_parser.parsear_rodada_socratica(texto)
    assert not erros
    assert len(perguntas) == 2
    assert perguntas[0]["numero"] == 1
    assert perguntas[1]["numero"] == 2
    assert "simplifica" in perguntas[0]["recomendacao"]

def test_parser_rejeita_rodada_sem_perguntas():
    texto = "# Apenas texto sem perguntas numeradas"
    perguntas, erros = grill_parser.parsear_rodada_socratica(texto)
    assert not perguntas
    assert len(erros) > 0
