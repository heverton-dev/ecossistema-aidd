# -*- coding: utf-8 -*-
"""
Testes reais da Phase 7 (Analisador Crítico Automático) — Correção 5/5.

Cobre: coleta de dados, cálculo de score (bom/ruim/vazio/det-string),
pontos fortes/fracos, requisitos críticos, roadmap, investimento,
relatório markdown, artefatos em disco, executar() e main().
Fase 100% determinística — sem mocks de LLM.
"""

import json
import sys
from pathlib import Path

import pytest

from conftest import _escrever_index_phase


# =============================================================================
# INICIALIZAÇÃO E COLETA
# =============================================================================

def test_init(analisador_07, tmp_path):
    analisador = analisador_07.AnalisadorCriticoAutomatico(tmp_path)
    assert analisador.pasta_projeto == tmp_path
    assert analisador.cache_path == tmp_path / '.aidd' / 'cache'


def test_coletar_dados_phases_completo(analisador_07, projeto_bom):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom)
    dados = analisador._coletar_dados_phases()
    assert set(dados.keys()) == {f'phase_{i}' for i in range(1, 7)}
    assert all(d['status'] == 'COMPLETO' for d in dados.values())


def test_coletar_dados_phases_vazio(analisador_07, projeto_vazio):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_vazio)
    assert analisador._coletar_dados_phases() == {}


# =============================================================================
# SCORE
# =============================================================================

def test_score_projeto_bom(analisador_07, projeto_bom):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom)
    score = analisador._calcular_score(analisador._coletar_dados_phases())

    assert score['total'] == 100
    assert score['por_dimensao']['completude_pipeline'] == 100
    assert score['por_dimensao']['qualidade_gates'] == 100
    assert score['por_dimensao']['determinismo'] == 100
    assert score['por_dimensao']['validacoes'] == 100
    assert 'economia_tokens' not in score['por_dimensao']
    assert score['por_dimensao']['documentacao'] == 100
    assert score['por_dimensao']['rastreabilidade'] == 100
    assert score['classificacao'] == 'TRANSCENDENTE'


def test_score_projeto_ruim(analisador_07, projeto_ruim):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_ruim)
    score = analisador._calcular_score(analisador._coletar_dados_phases())

    assert score['total'] == 37
    assert score['por_dimensao']['completude_pipeline'] == 33
    assert score['por_dimensao']['qualidade_gates'] == 85
    assert score['por_dimensao']['determinismo'] == 21
    assert score['por_dimensao']['validacoes'] == 33
    assert score['por_dimensao']['documentacao'] == 0
    assert score['classificacao'] == 'Básico'


def test_score_projeto_vazio(analisador_07, projeto_vazio):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_vazio)
    score = analisador._calcular_score({})

    assert score['total'] == 5
    assert score['por_dimensao']['validacoes'] == 50  # sem dados → neutro
    assert score['classificacao'] == 'Começando'


def test_score_determinismo_como_string(analisador_07):
    dados = {
        'phase_1': {'status': 'COMPLETO', 'tokens': {'percentual_determinismo': '100%'}},
    }
    analisador = analisador_07.AnalisadorCriticoAutomatico(Path('.'))
    score = analisador._calcular_score(dados)
    # 1 phase completa de 6 → 16; det '100%' → média sobre 6 phases (5 ausentes = 0) → 16
    assert score['por_dimensao']['completude_pipeline'] == 16
    assert score['por_dimensao']['determinismo'] == 16


def test_score_range_minimo(analisador_07):
    analisador = analisador_07.AnalisadorCriticoAutomatico(Path('.'))
    score = analisador._calcular_score({})
    assert 1 <= score['total'] <= 100


# =============================================================================
# PONTOS FORTES / FRACOS
# =============================================================================

def test_pontos_fortes_projeto_bom(analisador_07, projeto_bom):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom)
    fortes = analisador._identificar_pontos_fortes(analisador._coletar_dados_phases())

    assert any('Pipeline completo' in f for f in fortes)
    assert any('gates mecânicos' in f for f in fortes)
    assert any('determinismo' in f for f in fortes)
    assert any('validações sem falhas' in f for f in fortes)
    assert any('formatos' in f for f in fortes)


def test_pontos_fortes_projeto_vazio(analisador_07, projeto_vazio):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_vazio)
    fortes = analisador._identificar_pontos_fortes({})
    assert fortes == ['✅ Projeto iniciado — dados coletados com sucesso']


def test_pontos_fracos_projeto_ruim(analisador_07, projeto_ruim):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_ruim)
    fracos = analisador._identificar_pontos_fracos(analisador._coletar_dados_phases())

    assert any('Phases incompletas' in f for f in fracos)
    assert any('Gate' in f and 'falhou' in f for f in fracos)
    assert any('determinismo baixo' in f for f in fracos)
    assert any('validações falharam' in f for f in fracos)
    assert any('Sem documentação' in f for f in fracos)
    assert any('intervenção manual' in f for f in fracos)


def test_pontos_fracos_projeto_bom(analisador_07, projeto_bom):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom)
    fracos = analisador._identificar_pontos_fracos(analisador._coletar_dados_phases())
    # 12 gates no projeto bom → acima do mínimo de 10; sem falhas
    assert not any('falhou' in f for f in fracos)


# =============================================================================
# REQUISITOS CRÍTICOS
# =============================================================================

def test_requisitos_projeto_ruim(analisador_07, projeto_ruim):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_ruim)
    requisitos = analisador._listar_requisitos_criticos(analisador._coletar_dados_phases())

    assert any('Completar phases' in r['nome'] for r in requisitos)
    assert any('Corrigir gates' in r['nome'] for r in requisitos)
    assert any('Aumentar determinismo' in r['nome'] for r in requisitos)
    assert any('Gerar documentação' in r['nome'] for r in requisitos)
    assert any('Expandir cobertura de gates' in r['nome'] for r in requisitos)
    assert any('Resolver validações' in r['nome'] for r in requisitos)


def test_requisitos_projeto_bom(analisador_07, projeto_bom):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom)
    requisitos = analisador._listar_requisitos_criticos(analisador._coletar_dados_phases())
    assert any('Nenhum requisito crítico' in r['nome'] for r in requisitos)


# =============================================================================
# ROADMAP E INVESTIMENTO
# =============================================================================

def test_gerar_roadmap(analisador_07):
    analisador = analisador_07.AnalisadorCriticoAutomatico(Path('.'))
    roadmap = analisador._gerar_roadmap({'total': 40})
    assert roadmap['score_atual'] == 40
    assert len(roadmap['fases']) == 4  # todas as fases têm target > 40
    assert roadmap['fases'][-1]['target_score'] == 100
    assert roadmap['fases'][-1]['versao'] == 'v6.0'


def test_gerar_roadmap_filtra_fases_atingidas(analisador_07):
    """Score 80 deve filtrar v3.0 (target 75) — já atingido."""
    analisador = analisador_07.AnalisadorCriticoAutomatico(Path('.'))
    roadmap = analisador._gerar_roadmap({'total': 80})
    assert len(roadmap['fases']) == 3
    assert all(f['target_score'] > 80 for f in roadmap['fases'])
    assert roadmap['fases'][0]['versao'] == 'v4.0'


def test_gerar_roadmap_score_maximo(analisador_07):
    """Score 100 deve retornar roadmap vazio."""
    analisador = analisador_07.AnalisadorCriticoAutomatico(Path('.'))
    roadmap = analisador._gerar_roadmap({'total': 100})
    assert len(roadmap['fases']) == 0


def test_calcular_investimento(analisador_07):
    analisador = analisador_07.AnalisadorCriticoAutomatico(Path('.'))
    roadmap = analisador._gerar_roadmap({'total': 40})
    investimento = analisador._calcular_investimento(roadmap)

    assert investimento['total_horas'] == 590  # 250+150+140+50
    assert investimento['engenheiros_necessarios'] == 3  # 590 // 160
    assert investimento['custo_total'] == 88  # 590*150 // 1000
    assert investimento['timeline_meses'] == 8  # 3+2+2+1
    # Premissas explícitas (estimativa, não medição)
    assert investimento['premissas']['custo_por_hora_usd'] == 150
    assert investimento['premissas']['horas_por_semana'] == 40
    assert 'Estimativa' in investimento['premissas']['nota']


def test_calcular_investimento_score_maximo(analisador_07):
    """Score 100 → roadmap vazio → investimento zero."""
    analisador = analisador_07.AnalisadorCriticoAutomatico(Path('.'))
    roadmap = analisador._gerar_roadmap({'total': 100})
    investimento = analisador._calcular_investimento(roadmap)
    assert investimento['total_horas'] == 0
    assert investimento['custo_total'] == 0


# =============================================================================
# RELATÓRIO E ARTEFATOS
# =============================================================================

def test_gerar_relatorio_markdown(analisador_07, projeto_bom):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom)
    dados = analisador._coletar_dados_phases()
    relatorio = analisador._gerar_relatorio_markdown({
        'score': analisador._calcular_score(dados),
        'pontos_fortes': analisador._identificar_pontos_fortes(dados),
        'pontos_fracos': analisador._identificar_pontos_fracos(dados),
        'requisitos': analisador._listar_requisitos_criticos(dados),
        'roadmap': analisador._gerar_roadmap(analisador._calcular_score(dados)),
        'investimento': analisador._calcular_investimento(analisador._gerar_roadmap({'total': 40})),
    })

    assert 'AUTO-CRÍTICA' in relatorio
    assert '## 🎯 Score Atual' in relatorio
    assert '## ✅ Pontos Fortes' in relatorio
    assert '## ⚠️ Pontos a Melhorar' in relatorio
    assert '## 🔴 Requisitos Críticos' in relatorio
    assert '## 🚀 Roadmap para 100/100' in relatorio
    assert '## 💰 Investimento Necessário' in relatorio
    assert 'Lei Fundamental' in relatorio


def test_salvar_artefatos(analisador_07, projeto_bom):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom)
    analisador._salvar_artefatos({
        'relatorio': '# Relatório de teste',
        'score': {'total': 99},
        'pontos_fortes': ['a'],
        'pontos_fracos': ['b'],
        'roadmap': {'fases': [1, 2, 3, 4]},
    })

    assert (projeto_bom / 'AVALIACAO-AUTO-CRITICA.md').exists()
    assert (projeto_bom / '.aidd' / 'ROADMAP-EVOLUCAO.md').exists()
    index_path = projeto_bom / '.aidd' / 'cache' / '_phase_07_index.json'
    assert index_path.exists()

    index = json.loads(index_path.read_text(encoding='utf-8'))
    assert index['fase_id'] == 'phase_07_auto_critique'
    assert index['status'] == 'COMPLETO'
    assert index['processamento']['score_calculado'] == 99
    assert index['tokens']['percentual_determinismo'] == 100


# =============================================================================
# EXECUTAR (END-TO-END)
# =============================================================================

def test_executar_projeto_bom(analisador_07, projeto_bom):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom)
    resultado = analisador.executar()

    assert resultado['status'] == 'COMPLETO'
    assert resultado['score'] == 100
    assert resultado['artefatos'] == ['AVALIACAO-AUTO-CRITICA.md', '.aidd/ROADMAP-EVOLUCAO.md']
    assert (projeto_bom / 'AVALIACAO-AUTO-CRITICA.md').exists()
    assert (projeto_bom / '.aidd' / 'cache' / '_phase_07_index.json').exists()


def test_executar_projeto_vazio(analisador_07, projeto_vazio):
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_vazio)
    resultado = analisador.executar()
    assert resultado['status'] == 'COMPLETO'
    assert resultado['score'] == 5


# =============================================================================
# FASE 8 AWARENESS (reorder doc/auditoria)
# =============================================================================

def test_coletar_dados_inclui_fase8(analisador_07, projeto_bom_com_fase8):
    """Quando phase_8 existe, _coletar_dados_phases deve incluí-la."""
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom_com_fase8)
    dados = analisador._coletar_dados_phases()
    assert 'phase_8' in dados
    assert dados['phase_8']['fase_id'] == 'phase_08_implementacao'
    assert dados['phase_8']['status'] == 'COMPLETO'


def test_score_com_fase8_completude_reflete_7_fases(analisador_07, projeto_bom_com_fase8):
    """Com phase_8, completude usa denominador 7 (não 6)."""
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom_com_fase8)
    dados = analisador._coletar_dados_phases()
    score = analisador._calcular_score(dados)
    # 7/7 phases completas → 100
    assert score['por_dimensao']['completude_pipeline'] == 100


def test_score_com_fase8_gates_incluem_i1_i4(analisador_07, projeto_bom_com_fase8):
    """Gates da phase_8 (I1-I4) devem ser incluídos no cálculo de qualidade."""
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom_com_fase8)
    dados = analisador._coletar_dados_phases()
    score = analisador._calcular_score(dados)
    # 18 gates (phases 1-6) + 4 gates (phase 8) = 22, todos PASSOU
    assert score['por_dimensao']['qualidade_gates'] == 100


def test_score_com_fase8_rastreabilidade_reflete_total(analisador_07, projeto_bom_com_fase8):
    """Rastreabilidade com phase_8 usa denominador 7."""
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom_com_fase8)
    dados = analisador._coletar_dados_phases()
    score = analisador._calcular_score(dados)
    # 7 fases com gates / 7 total = 100%
    assert score['por_dimensao']['rastreabilidade'] == 100


def test_pontos_fortes_com_fase8_inclui_codigo_funcional(analisador_07, projeto_bom_com_fase8):
    """Pontos fortes devem mencionar código funcional quando phase_8 completa."""
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom_com_fase8)
    dados = analisador._coletar_dados_phases()
    fortes = analisador._identificar_pontos_fortes(dados)
    assert any('Código funcional' in f for f in fortes)
    assert any('5 script(s)' in f for f in fortes)


def test_pontos_fracos_com_fase8_gate_falho(analisador_07, tmp_path):
    """Se gate da phase_8 falhar, deve aparecer nos pontos fracos."""
    cache = tmp_path / '.aidd' / 'cache'
    for i in range(1, 7):
        _escrever_index_phase(cache, i)
    _escrever_index_phase(cache, 7)
    _escrever_index_phase(
        cache, 8,
        fase_id='phase_08_implementacao',
        tokens={'consumidos': 5000, 'percentual_determinismo': 0},
        gates_executados=[
            {'gate_id': 'I3_testes_passam', 'descricao': '100% testes passam', 'status': 'FALHOU', 'detalhes': '11/20'},
        ],
    )
    analisador = analisador_07.AnalisadorCriticoAutomatico(tmp_path)
    dados = analisador._coletar_dados_phases()
    fracos = analisador._identificar_pontos_fracos(dados)
    assert any('I3_testes_passam' in f for f in fracos)


def test_requisitos_com_fase8_inclui_gates_falhos(analisador_07, tmp_path):
    """Requisitos críticos devem incluir gates da phase_8 que falharam."""
    cache = tmp_path / '.aidd' / 'cache'
    for i in range(1, 7):
        _escrever_index_phase(cache, i)
    _escrever_index_phase(cache, 7)
    _escrever_index_phase(
        cache, 8,
        fase_id='phase_08_implementacao',
        tokens={'consumidos': 5000, 'percentual_determinismo': 0},
        gates_executados=[
            {'gate_id': 'I3_testes_passam', 'descricao': '100% testes passam', 'status': 'FALHOU', 'detalhes': '11/20'},
        ],
    )
    analisador = analisador_07.AnalisadorCriticoAutomatico(tmp_path)
    dados = analisador._coletar_dados_phases()
    requisitos = analisador._listar_requisitos_criticos(dados)
    assert any('I3_testes_passam' in r['nome'] for r in requisitos)


def test_executar_projeto_bom_com_fase8(analisador_07, projeto_bom_com_fase8):
    """executar() deve rodar com sucesso e incluir dados da phase_8 no score."""
    analisador = analisador_07.AnalisadorCriticoAutomatico(projeto_bom_com_fase8)
    resultado = analisador.executar()
    assert resultado['status'] == 'COMPLETO'
    assert resultado['score'] == 100


# =============================================================================
# MAIN (CLI)
# =============================================================================

def test_main_sucesso(analisador_07, projeto_bom, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['07_analisador.py', str(projeto_bom)])
    monkeypatch.setattr(
        analisador_07.AnalisadorCriticoAutomatico, 'executar',
        lambda self: {'status': 'COMPLETO'}
    )
    with pytest.raises(SystemExit) as exc:
        analisador_07.main()
    assert exc.value.code == 0


def test_main_projeto_inexistente(analisador_07, tmp_path, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['07_analisador.py', str(tmp_path / 'nao-existe')])
    with pytest.raises(SystemExit) as exc:
        analisador_07.main()
    assert exc.value.code == 1


def test_main_falha(analisador_07, projeto_bom, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['07_analisador.py', str(projeto_bom)])
    monkeypatch.setattr(
        analisador_07.AnalisadorCriticoAutomatico, 'executar',
        lambda self: {'status': 'FALHOU'}
    )
    with pytest.raises(SystemExit) as exc:
        analisador_07.main()
    assert exc.value.code == 1