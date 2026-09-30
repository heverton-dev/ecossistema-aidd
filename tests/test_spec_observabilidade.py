# -*- coding: utf-8 -*-
"""Testes de observabilidade para aidd-spec (Ticket 6 / D12 / DoD 5)."""

import pytest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "skills" / "aidd-spec" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import observabilidade as spec_observabilidade

def test_rastreador_spec_calcula_metricas():
    rastreador = spec_observabilidade.RastreadorSpec()
    secoes = {
        "contratos": "- interface User { id: string; }",
        "modos_falha": "- Erro 500 no banco"
    }
    resumo_motor = {
        "total_invariantes": 3,
        "total_criterios_binarios": 4
    }
    metricas = rastreador.analisar_especificacao(secoes, resumo_motor)
    assert metricas["total_invariantes"] == 3
    assert metricas["total_criterios_binarios"] == 4
    assert metricas["interfaces_contratos_detectados"] >= 1
    assert "tempo_processamento_ms" in metricas
    assert "gerado_em" in metricas
