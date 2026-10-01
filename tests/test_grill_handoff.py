# -*- coding: utf-8 -*-
"""Testes de handoff assinado para aidd-grill (Ticket 8 / D15 / DoD 8)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-grill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import handoff as grill_handoff

def test_handoff_gera_e_valida_assinatura(tmp_path):
    saida = tmp_path / "handoff_grill.json"
    perguntas = [{"numero": 1, "titulo": "P1"}]
    resumo = {"total_validadas": 1, "premissas_consolidadas": [{"id": 1}]}

    sucesso = grill_handoff.gerar_handoff_grill(perguntas, resumo, saida)
    assert sucesso is True
    assert saida.exists()
    assert grill_handoff.verificar_handoff_grill(saida) is True

def test_handoff_rejeita_tampering(tmp_path):
    saida = tmp_path / "handoff_grill_alterado.json"
    perguntas = [{"numero": 1, "titulo": "P1"}]
    resumo = {"total_validadas": 1, "premissas_consolidadas": [{"id": 1}]}

    grill_handoff.gerar_handoff_grill(perguntas, resumo, saida)

    # Adulteração maliciosa do payload
    conteudo = saida.read_text(encoding="utf-8")
    adulterado = conteudo.replace('"total_perguntas": 1', '"total_perguntas": 99')
    saida.write_text(adulterado, encoding="utf-8")

    assert grill_handoff.verificar_handoff_grill(saida) is False
