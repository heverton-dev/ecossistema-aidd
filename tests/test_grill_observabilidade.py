# -*- coding: utf-8 -*-
"""Testes de observabilidade para aidd-grill (Ticket 6 / D12 / DoD 5)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-grill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import observabilidade as grill_observabilidade

def test_rastreador_grill_calcula_metricas():
    rastreador = grill_observabilidade.RastreadorGrill()
    perguntas = [
        {"numero": 1, "opcoes": ["A", "B"]},
        {"numero": 2, "opcoes": ["A", "B", "C"]}
    ]
    resumo_motor = {
        "total_validadas": 2,
        "premissas_consolidadas": [{"id": 1}, {"id": 2}]
    }
    metricas = rastreador.analisar_rodada(perguntas, resumo_motor)
    assert metricas["total_perguntas"] == 2
    assert metricas["total_opcoes_mapeadas"] == 5
    assert metricas["perguntas_com_recomendacao_justificada"] == 2
    assert metricas["premissas_consolidadas"] == 2
    assert "tempo_processamento_ms" in metricas
    assert "gerado_em" in metricas
