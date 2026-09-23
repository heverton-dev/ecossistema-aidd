# -*- coding: utf-8 -*-
"""
Teste de Observabilidade e Frugalidade (Ticket 5 / D12).
Exige instrumentação de orçamento de tokens, tempo de execução e persistência de log padronizado.
"""

import os
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))


def test_rastreador_observabilidade_gera_metricas(tmp_path):
    """Garante cálculo e registro de tokens e tempo em log padronizado."""
    from observabilidade import MetricasExecucao, registrar_observabilidade

    metricas = MetricasExecucao(
        etapa="analise-melhoria",
        tokens_entrada=120,
        tokens_saida=350,
        duracao_segundos=1.45,
        status="SUCESSO"
    )

    log_dir = tmp_path / "secoes"
    log_file = registrar_observabilidade(metricas, log_dir=log_dir)

    assert log_file.exists()
    conteudo = log_file.read_text(encoding="utf-8")
    assert "tokens_entrada: 120" in conteudo or "120" in conteudo
    assert "tokens_saida: 350" in conteudo or "350" in conteudo
    assert "SUCESSO" in conteudo
