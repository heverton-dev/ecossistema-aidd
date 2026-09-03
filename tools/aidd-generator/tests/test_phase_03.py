# -*- coding: utf-8 -*-
"""
Testes reais da Phase 3 (Designer AIDD) — Correção 5/5.

Cobre: gates D1-D3, DesignerFase3 (init, executar, _executar_subagentes_com_llm,
_consolidar_design, _gerar_index) e main(). As 5 chamadas LLM (subagentes)
são mockadas via protocolo delegado.
"""

import json
import sys
from pathlib import Path

import pytest


# =============================================================================
# HELPERS
# =============================================================================

def resposta_subagente(fase):
    """JSON de resposta por subagente da Phase 3."""
    if 'arquiteto_camadas' in fase:
        return {'camadas': [
            {'numero': i, 'nome': f'Camada {i}', 'responsabilidade': 'r', 'artefatos': ['a.py']}
            for i in range(1, 6)
        ]}
    if 'engenheiro_scripts' in fase:
        return {'scripts': [
            {'camada': 2, 'nome': 'coleta.py', 'responsabilidade': 'r',
             'pseudocodigo': '1. x', 'determinismo_percentual': 100, 'teste': 'assert'}
        ]}
    if 'especialista_tokens' in fase:
        return {'fases': [], 'total_tokens': 60000,
                'tokens_economia_vs_ingenue': 440000, 'percentual_determinismo': 88}
    if 'arquiteto_ferramentas' in fase:
        return {'ferramentas': [
            {'nome': 'skill-x', 'tipo': 'Skill', 'proposito': 'p',
             'escopo': 'GLOBAL', 'justificativa': 'j'}
        ]}
    if 'especialista_gates' in fase:
        return {'gates': [
            {'gate_id': 'G0', 'descricao': 'd', 'checklist': ['c'],
             'criterio_sucesso': 's', 'retorno': 'exit 0'}
        ]}
    raise AssertionError(f'Subagente desconhecido: {fase}')


def fake_solicitar_llm_sucesso(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
    conteudo = json.dumps(resposta_subagente(fase), ensure_ascii=False)
    return {'conteudo': conteudo, 'tokens_consumidos': 100, 'modelo_usado': 'teste'}


def fake_solicitar_llm_falha(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
    if 'especialista_gates' in fase:
        raise RuntimeError('Subagente falhou')
    return fake_solicitar_llm_sucesso(prompt, contexto, fase, modelo, timeout_delegacao)


# =============================================================================
# GATE (estrutura base)
# =============================================================================

def test_gate_to_dict(designer_03):
    gate = designer_03.Gate('D1', 'descricao', True, 'detalhes')
    assert gate.to_dict()['status'] == 'PASSOU'
    assert designer_03.Gate('D1', 'descricao', False, 'detalhes').to_dict()['status'] == 'FALHOU'


# =============================================================================
# GATES D1-D3
# =============================================================================

def test_gate_d1_camadas_aidd(designer_03, design_valido):
    gate = designer_03.ValidadorGatesPhase3._gate_d1_camadas_aidd(design_valido)
    assert gate.passou is True
    assert '5/5' in gate.detalhes

    incompleto = {'design': {'camadas': [{'numero': 1}]}}
    gate_falhou = designer_03.ValidadorGatesPhase3._gate_d1_camadas_aidd(incompleto)
    assert gate_falhou.passou is False


def test_gate_d2_scripts_viavel(designer_03, design_valido):
    gate = designer_03.ValidadorGatesPhase3._gate_d2_scripts_viavel(design_valido)
    assert gate.passou is True

    sem_scripts = {'design': {'scripts': []}}
    gate_falhou = designer_03.ValidadorGatesPhase3._gate_d2_scripts_viavel(sem_scripts)
    assert gate_falhou.passou is False


def test_gate_d3_economia_tokens(designer_03, design_valido):
    gate = designer_03.ValidadorGatesPhase3._gate_d3_economia_tokens(design_valido)
    assert gate.passou is True
    assert '88%' in gate.detalhes

    # Teste de fronteira: 65% exato passa
    piso_65 = {'design': {'tokens': {'percentual_determinismo': 65}}}
    gate_piso = designer_03.ValidadorGatesPhase3._gate_d3_economia_tokens(piso_65)
    assert gate_piso.passou is True

    # Teste de proporção real 4/6 fases (66.7%) passa
    arquitetural_66_7 = {'design': {'tokens': {'percentual_determinismo': 66.7}}}
    gate_arq = designer_03.ValidadorGatesPhase3._gate_d3_economia_tokens(arquitetural_66_7)
    assert gate_arq.passou is True

    # Teste de string com '%'
    com_string = {'design': {'tokens': {'percentual_determinismo': '67%'}}}
    gate_string = designer_03.ValidadorGatesPhase3._gate_d3_economia_tokens(com_string)
    assert gate_string.passou is True

    # Teste abaixo do threshold de 65% falha
    abaixo_limiar = {'design': {'tokens': {'percentual_determinismo': 64.9}}}
    gate_abaixo = designer_03.ValidadorGatesPhase3._gate_d3_economia_tokens(abaixo_limiar)
    assert gate_abaixo.passou is False

    baixo = {'design': {'tokens': {'percentual_determinismo': 50}}}
    gate_falhou = designer_03.ValidadorGatesPhase3._gate_d3_economia_tokens(baixo)
    assert gate_falhou.passou is False


def test_executar_todos_gates_passam(designer_03, design_valido):
    gates, todos_passaram = designer_03.ValidadorGatesPhase3.executar_todos(design_valido)
    assert len(gates) == 3
    assert todos_passaram is True


def test_executar_todos_gates_falham(designer_03):
    design_ruim = {'design': {'camadas': [], 'scripts': [], 'tokens': {'percentual_determinismo': 10}}}
    gates, todos_passaram = designer_03.ValidadorGatesPhase3.executar_todos(design_ruim)
    assert todos_passaram is False


# =============================================================================
# DESIGNERFASE3
# =============================================================================

def test_designer_init(tmp_path, designer_03):
    designer = designer_03.DesignerFase3(tmp_path / 'cache')
    assert (tmp_path / 'cache').exists()
    assert designer.modelo_final
    assert designer._tokens_reais_totais is None


def test_consolidar_design(designer_03):
    resultados = {
        'arquiteto_camadas': {'camadas': [1, 2, 3, 4, 5]},
        'engenheiro_scripts': {'scripts': ['s1']},
        'especialista_tokens': {'percentual_determinismo': 88},
        'arquiteto_ferramentas': {'ferramentas': ['f1']},
        'especialista_gates': {'gates': ['g1']},
    }
    consolidado = designer_03.DesignerFase3(Path('.'))._consolidar_design(resultados)
    assert consolidado['design']['camadas'] == [1, 2, 3, 4, 5]
    assert consolidado['design']['scripts'] == ['s1']
    assert consolidado['design']['tokens']['percentual_determinismo'] == 88
    assert consolidado['design']['ferramentas'] == ['f1']
    assert consolidado['design']['gates'] == ['g1']


def test_executar_subagentes_com_llm_sucesso(tmp_path, designer_03, monkeypatch):
    monkeypatch.setattr(designer_03, 'solicitar_llm', fake_solicitar_llm_sucesso)
    designer = designer_03.DesignerFase3(tmp_path / 'cache')
    resultados = designer._executar_subagentes_com_llm('ideia')

    assert resultados is not None
    assert set(resultados.keys()) == {
        'arquiteto_camadas', 'engenheiro_scripts', 'especialista_tokens',
        'arquiteto_ferramentas', 'especialista_gates',
    }
    assert designer._tokens_reais_totais == 500  # 5 subagentes × 100 tokens


def test_executar_subagentes_com_llm_falha(tmp_path, designer_03, monkeypatch):
    monkeypatch.setattr(designer_03, 'solicitar_llm', fake_solicitar_llm_falha)
    designer = designer_03.DesignerFase3(tmp_path / 'cache')
    assert designer._executar_subagentes_com_llm('ideia') is None


def test_gerar_index(designer_03, design_valido):
    gates, _ = designer_03.ValidadorGatesPhase3.executar_todos(design_valido)
    designer = designer_03.DesignerFase3(Path('.'))
    designer._tokens_reais_totais = 500
    index = designer._gerar_index(design_valido, gates, 2.0)

    assert index['fase_id'] == 'phase_03_design'
    assert index['status'] == 'COMPLETO'
    assert index['tokens']['consumidos'] == 500
    assert index['processamento']['subagentes_executados'] == 5
    assert index['processamento']['camadas_definidas'] == 5
    assert index['resume_info']['pode_prosseguir'] is True


def test_executar_sucesso(tmp_path, designer_03, monkeypatch):
    monkeypatch.setattr(designer_03, 'solicitar_llm', fake_solicitar_llm_sucesso)
    designer = designer_03.DesignerFase3(tmp_path / 'cache')
    index = designer.executar('Sistema de vídeos YouTube', {})

    assert index is not None
    assert index['status'] == 'COMPLETO'
    assert index['tokens']['consumidos'] == 500
    assert (tmp_path / 'cache' / '_phase_03_index.json').exists()
    assert (tmp_path / 'cache' / 'data' / 'design_aidd_phase3.json').exists()


def test_executar_subagentes_falham(tmp_path, designer_03, monkeypatch):
    monkeypatch.setattr(designer_03, 'solicitar_llm', fake_solicitar_llm_falha)
    designer = designer_03.DesignerFase3(tmp_path / 'cache')
    assert designer.executar('ideia', {}) is None


def test_executar_gates_falham(tmp_path, designer_03, monkeypatch):
    def fake_ruim(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        # Estrutura válida por subagente, mas conteúdo vazio/insuficiente
        if 'arquiteto_camadas' in fase:
            conteudo = {'camadas': []}
        elif 'engenheiro_scripts' in fase:
            conteudo = {'scripts': []}
        elif 'especialista_tokens' in fase:
            conteudo = {'fases': [], 'total_tokens': 0,
                        'tokens_economia_vs_ingenue': 0, 'percentual_determinismo': 10}
        elif 'arquiteto_ferramentas' in fase:
            conteudo = {'ferramentas': []}
        else:
            conteudo = {'gates': []}
        return {'conteudo': json.dumps(conteudo, ensure_ascii=False),
                'tokens_consumidos': 10, 'modelo_usado': 'teste'}

    monkeypatch.setattr(designer_03, 'solicitar_llm', fake_ruim)
    designer = designer_03.DesignerFase3(tmp_path / 'cache')
    assert designer.executar('ideia', {}) is None


# =============================================================================
# MAIN (CLI)
# =============================================================================

def test_main_sucesso(tmp_path, designer_03, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['03_designer.py', 'minha ideia', '--cache-dir', str(tmp_path / 'cache')]
    )
    monkeypatch.setattr(
        designer_03.DesignerFase3, 'executar',
        lambda self, ideia, analise: {'status': 'COMPLETO'}
    )
    with pytest.raises(SystemExit) as exc:
        designer_03.main()
    assert exc.value.code == 0


def test_main_falha(tmp_path, designer_03, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['03_designer.py', 'minha ideia', '--cache-dir', str(tmp_path / 'cache')]
    )
    monkeypatch.setattr(
        designer_03.DesignerFase3, 'executar',
        lambda self, ideia, analise: None
    )
    with pytest.raises(SystemExit) as exc:
        designer_03.main()
    assert exc.value.code == 1