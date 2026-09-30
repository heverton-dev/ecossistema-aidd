# -*- coding: utf-8 -*-
"""Testes de handoff assinado para aidd-spec (Ticket 8 / D15 / DoD 8)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import handoff as spec_handoff

def test_handoff_gera_e_valida_assinatura(tmp_path):
    saida = tmp_path / "handoff_spec.json"
    secoes = {"contexto": "...", "invariantes": "..."}
    resumo = {"total_invariantes": 2, "total_criterios_binarios": 3}
    
    sucesso = spec_handoff.gerar_handoff_spec(secoes, resumo, saida)
    assert sucesso is True
    assert saida.exists()
    assert spec_handoff.verificar_handoff_spec(saida) is True

def test_handoff_rejeita_tampering(tmp_path):
    saida = tmp_path / "handoff_alterado.json"
    secoes = {"contexto": "..."}
    resumo = {"total_invariantes": 1, "total_criterios_binarios": 1}
    
    spec_handoff.gerar_handoff_spec(secoes, resumo, saida)
    
    # Adulteração maliciosa do payload
    conteudo = saida.read_text(encoding="utf-8")
    adulterado = conteudo.replace('"total_invariantes": 1', '"total_invariantes": 99')
    saida.write_text(adulterado, encoding="utf-8")

    assert spec_handoff.verificar_handoff_spec(saida) is False
