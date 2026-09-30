# -*- coding: utf-8 -*-
"""Testes de validação de regras e critérios binários para aidd-spec (Ticket 4 / D8 / DoD 3)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import motor as spec_motor

def test_motor_aprova_criterios_mecanicos():
    criterios_texto = """
- Retorna exit code 0 ao executar comando.
- Endpoint responde com status 200.
- Execução de pytest tests/test_app.py deve passar.
"""
    crits, erros = spec_motor.extrair_criterios_binarios(criterios_texto)
    assert not erros
    assert len(crits) == 3

def test_motor_rejeita_criterios_subjetivos():
    criterios_texto = """
- O sistema deve ser rápido e a interface bonita.
"""
    crits, erros = spec_motor.extrair_criterios_binarios(criterios_texto)
    assert len(erros) > 0
    assert any("subjetivo" in e or "não verificável" in e for e in erros)

def test_motor_extrai_invariantes_numeradas():
    invariantes_texto = """
1. Token nunca expira antes de 1 hora.
2. Senha tem no mínimo 8 caracteres.
"""
    invars = spec_motor.extrair_invariantes(invariantes_texto)
    assert len(invars) == 2
