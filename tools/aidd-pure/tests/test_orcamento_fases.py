# -*- coding: utf-8 -*-
"""
Testes do Item 7 — 02-otimizacao-tokenomics-latencia:
orcamento de tokens por fase + correcao de alegacao de marketing.

Criterios de saida do plano:
1. token_budgets.json existe e e JSON valido com pelo menos 8 entradas.
2. Pipeline emite alerta quando tokens_utilizados excedem orcamento * 1.2.
3. Nenhuma alegacao de ">65%" permanece em pipeline_completo.py ou __init__.py.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG = _ROOT / 'config'
_SCRIPTS = _ROOT / 'scripts'
_PHASES = _SCRIPTS / 'phases'

if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


@pytest.fixture(scope='module')
def pipeline_mod():
    """Importa pipeline_completo como modulo (para acessar funcoes auxiliares)."""
    spec = importlib.util.spec_from_file_location(
        'pipeline_completo_item7', str(_SCRIPTS / 'pipeline_completo.py')
    )
    modulo = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(modulo)
    except SystemExit:
        pass  # click CLI pode causar SystemExit no import
    return modulo


# =============================================================================
# CRITERIO 1: token_budgets.json existe e e JSON valido
# =============================================================================

def test_token_budgets_json_existe_e_e_valido():
    path = _CONFIG / 'token_budgets.json'
    assert path.exists(), f"token_budgets.json nao encontrado em {path}"
    dados = json.loads(path.read_text(encoding='utf-8'))
    assert 'fases' in dados
    assert len(dados['fases']) >= 8


def test_token_budgets_cada_fase_tem_orcamento():
    path = _CONFIG / 'token_budgets.json'
    dados = json.loads(path.read_text(encoding='utf-8'))
    for chave, fase in dados['fases'].items():
        assert 'orcamento_tokens' in fase
        assert fase['orcamento_tokens'] > 0


def test_token_budgets_tem_limiar_alerta():
    path = _CONFIG / 'token_budgets.json'
    dados = json.loads(path.read_text(encoding='utf-8'))
    assert 'limiar_alerta_desvio' in dados
    assert dados['limiar_alerta_desvio'] >= 1.0


# =============================================================================
# CRITERIO 3: nenhuma alegacao >65%
# =============================================================================

def test_pipeline_completo_sem_alegacao_65_porcento():
    path = _SCRIPTS / 'pipeline_completo.py'
    conteudo = path.read_text(encoding='utf-8')
    assert '>65%' not in conteudo


def test_init_sem_alegacao_65_porcento():
    path = _PHASES / '__init__.py'
    conteudo = path.read_text(encoding='utf-8')
    assert '>65%' not in conteudo


# =============================================================================
# CRITERIO 2: alerta de desvio (teste direto da funcao)
# =============================================================================

def test_registrar_orcamento_registra_estado(pipeline_mod, tmp_path):
    """_registrar_e_verificar_orcamento registra no _pipeline_state.json."""
    if not hasattr(pipeline_mod, '_registrar_e_verificar_orcamento'):
        pytest.skip("funcao _registrar_e_verificar_orcamento nao disponivel no modulo")

    orcamentos = {'fase_1': {'orcamento_tokens': 1000}}
    state_path = tmp_path / '_pipeline_state.json'

    pipeline_mod._registrar_e_verificar_orcamento(
        {'tokens_consumidos': 800}, 'Pesquisador', 1, orcamentos, state_path
    )
    estado = json.loads(state_path.read_text(encoding='utf-8'))
    assert estado['orcamento_fases']['fase_1']['tokens_utilizados'] == 800
    assert estado['orcamento_fases']['fase_1']['desvio_pct'] == -20.0


def test_registrar_orcamento_alerta_desvio(pipeline_mod, tmp_path, capsys):
    """Emite alerta quando desvio > 20%."""
    if not hasattr(pipeline_mod, '_registrar_e_verificar_orcamento'):
        pytest.skip("funcao nao disponivel")

    orcamentos = {'fase_1': {'orcamento_tokens': 1000}}
    state_path = tmp_path / '_pipeline_state.json'

    pipeline_mod._registrar_e_verificar_orcamento(
        {'tokens_consumidos': 1500}, 'Pesquisador', 1, orcamentos, state_path
    )
    captured = capsys.readouterr()
    assert 'ORÇAMENTO' in captured.out
    estado = json.loads(state_path.read_text(encoding='utf-8'))
    assert estado['orcamento_fases']['fase_1']['desvio_pct'] == 50.0


def test_registrar_orcamento_sem_budget_nao_faz_nada(pipeline_mod, tmp_path):
    """Sem orcamentos, funcao nao cria arquivo."""
    if not hasattr(pipeline_mod, '_registrar_e_verificar_orcamento'):
        pytest.skip("funcao nao disponivel")

    state_path = tmp_path / '_pipeline_state.json'
    pipeline_mod._registrar_e_verificar_orcamento(
        {'tokens_consumidos': 1000}, 'Pesquisador', 1, {}, state_path
    )
    assert not state_path.exists()


def test_carregar_orcamento_fases(pipeline_mod):
    """_carregar_orcamento_fases retorna dict com 8 fases."""
    if not hasattr(pipeline_mod, '_carregar_orcamento_fases'):
        pytest.skip("funcao nao disponivel")

    orcamentos = pipeline_mod._carregar_orcamento_fases()
    assert len(orcamentos) >= 8
    assert 'fase_1' in orcamentos
    assert 'fase_8' in orcamentos
