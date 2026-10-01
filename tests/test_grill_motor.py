# -*- coding: utf-8 -*-
"""Testes de validação de recomendações e justificativas para aidd-grill (Ticket 4 / D8 / DoD 3)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-grill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import motor as grill_motor

def test_motor_aprova_recomendacao_com_justificativa():
    valido, msg = grill_motor.validar_justificativa_recomendacao("Opção A, porque garante integridade referencial.")
    assert valido is True
    assert msg == ""

def test_motor_rejeita_recomendacao_sem_justificativa():
    valido, msg = grill_motor.validar_justificativa_recomendacao("Opção A.")
    assert valido is False
    assert "falta de justificativa" in msg

def test_motor_valida_perguntas_socromaticas():
    perguntas = [
        {"numero": 1, "titulo": "P1", "recomendacao": "A, pois é mais rápido."},
        {"numero": 2, "titulo": "P2", "recomendacao": "B, devido ao menor custo."}
    ]
    resumo, erros = grill_motor.validar_perguntas_socromaticas(perguntas)
    assert not erros
    assert resumo["total_validadas"] == 2
    assert len(resumo["premissas_consolidadas"]) == 2
