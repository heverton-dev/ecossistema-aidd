# -*- coding: utf-8 -*-
"""
Testes reais da Phase 1 (Pesquisador de Referências).

Cobre: Referencia/Insight, os 3 pesquisadores (GitHub/HuggingFace/Replit),
ConsolidadorInsights, gates R1-R4, GeradorPhaseIndex e PesquisadorFase1.
Chamadas HTTP externas (requests.get/head) são mockadas — nenhum teste
depende de rede real.
"""

import json
import sys

import pytest


# =============================================================================
# HELPERS DE MOCK HTTP
# =============================================================================

class RespostaFake:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f'HTTP {self.status_code}')


ITEM_GITHUB_VALIDO = {
    'full_name': 'exemplo/projeto',
    'html_url': 'https://github.com/exemplo/projeto',
    'stargazers_count': 500,
    'forks_count': 100,
    'language': 'Python',
    'pushed_at': '2026-08-29T10:00:00Z',
    'license': {'name': 'MIT'},
    'description': 'Projeto de exemplo para testes',
}


# =============================================================================
# ESTRUTURAS BASE
# =============================================================================

def test_referencia_to_dict(pesquisador_01):
    ref = pesquisador_01.Referencia('nome', 'https://x.com', 'github', {'stars': 1})
    d = ref.to_dict()
    assert d['nome'] == 'nome'
    assert d['fonte'] == 'github'
    assert d['metadata'] == {'stars': 1}
    assert 'data_coletada' in d


def test_insight_to_dict(pesquisador_01):
    insight = pesquisador_01.Insight('stack_linguagem', 'Python', 3, ['github'])
    d = insight.to_dict()
    assert d == {
        'tipo': 'stack_linguagem',
        'descricao': 'Python',
        'frequencia': 3,
        'fontes': ['github'],
    }


def test_gate_to_dict(pesquisador_01):
    gate = pesquisador_01.Gate('R1', 'descricao', True, 'detalhes')
    assert gate.to_dict()['status'] == 'PASSOU'
    gate_falhou = pesquisador_01.Gate('R1', 'descricao', False, 'detalhes')
    assert gate_falhou.to_dict()['status'] == 'FALHOU'


# =============================================================================
# PESQUISADORGITHUB — zero fallback fictício
# =============================================================================

def test_pesquisador_github_sucesso(pesquisador_01, monkeypatch):
    monkeypatch.setattr(
        pesquisador_01.requests, 'get',
        lambda *a, **kw: RespostaFake(200, {'items': [ITEM_GITHUB_VALIDO]})
    )
    refs = pesquisador_01.PesquisadorGitHub.buscar('ideia')
    assert len(refs) == 1
    assert refs[0].fonte == 'github'
    assert refs[0].metadata['stars'] == 500


def test_pesquisador_github_language_null_nao_quebra(pesquisador_01, monkeypatch):
    """Achado com dados REAIS do GitHub (não fixture): repositórios sem
    linguagem dominante detectável retornam 'language': null (não ausente).
    .get('language', 'unknown') não pega esse caso — só cobre chave ausente,
    não valor None. Isso quebrava json.dumps(sort_keys=True) mais adiante
    (None não é comparável com str)."""
    item_sem_linguagem = dict(ITEM_GITHUB_VALIDO, language=None)
    monkeypatch.setattr(
        pesquisador_01.requests, 'get',
        lambda *a, **kw: RespostaFake(200, {'items': [item_sem_linguagem]})
    )
    refs = pesquisador_01.PesquisadorGitHub.buscar('ideia')
    assert refs[0].metadata['linguagens'] == 'unknown'


def test_pesquisador_github_filtra_poucas_stars(pesquisador_01, monkeypatch):
    item_poucas_stars = dict(ITEM_GITHUB_VALIDO, stargazers_count=10)
    monkeypatch.setattr(
        pesquisador_01.requests, 'get',
        lambda *a, **kw: RespostaFake(200, {'items': [item_poucas_stars]})
    )
    refs = pesquisador_01.PesquisadorGitHub.buscar('ideia')
    assert refs == []


def test_pesquisador_github_http_erro_retorna_vazio_sem_fake(pesquisador_01, monkeypatch):
    """HTTP != 200 nunca deve substituir por dado fictício (Zero Alucinação)."""
    monkeypatch.setattr(
        pesquisador_01.requests, 'get',
        lambda *a, **kw: RespostaFake(503, {})
    )
    refs = pesquisador_01.PesquisadorGitHub.buscar('ideia')
    assert refs == []


def test_pesquisador_github_excecao_retorna_vazio_sem_fake(pesquisador_01, monkeypatch):
    def levanta(*a, **kw):
        raise ConnectionError('rede indisponível')
    monkeypatch.setattr(pesquisador_01.requests, 'get', levanta)
    refs = pesquisador_01.PesquisadorGitHub.buscar('ideia')
    assert refs == []


def test_pesquisador_github_sem_dados_teste_hardcoded(pesquisador_01):
    """Não deve existir mais nenhum atributo de dados fictícios na classe."""
    assert not hasattr(pesquisador_01.PesquisadorGitHub, 'DADOS_TESTE')


# =============================================================================
# PESQUISADORHUGGINGFACE
# =============================================================================

def test_pesquisador_hf_sucesso(pesquisador_01, monkeypatch):
    item = {'modelId': 'org/modelo', 'downloads': 1000, 'likes': 50, 'tags': ['nlp'], 'library_name': 'transformers'}
    monkeypatch.setattr(
        pesquisador_01.requests, 'get',
        lambda *a, **kw: RespostaFake(200, [item])
    )
    refs = pesquisador_01.PesquisadorHuggingFace.buscar('ideia')
    assert len(refs) == 1
    assert refs[0].fonte == 'huggingface'
    assert refs[0].nome == 'org/modelo'


def test_pesquisador_hf_excecao_retorna_vazio(pesquisador_01, monkeypatch):
    def levanta(*a, **kw):
        raise ConnectionError('rede indisponível')
    monkeypatch.setattr(pesquisador_01.requests, 'get', levanta)
    assert pesquisador_01.PesquisadorHuggingFace.buscar('ideia') == []


# =============================================================================
# PESQUISADORREPLIT — stub honesto (sempre vazio, nunca fake)
# =============================================================================

def test_pesquisador_replit_sempre_vazio(pesquisador_01):
    assert pesquisador_01.PesquisadorReplit.buscar('qualquer ideia') == []


# =============================================================================
# CONSOLIDADORINSIGHTS
# =============================================================================

def test_consolidador_insights(pesquisador_01):
    refs = [
        pesquisador_01.Referencia('a', 'https://a.com', 'github', {'linguagens': 'Python'}),
        pesquisador_01.Referencia('b', 'https://b.com', 'github', {'linguagens': 'Python'}),
        pesquisador_01.Referencia('c', 'https://c.com', 'github', {'linguagens': 'JavaScript'}),
    ]
    insights = pesquisador_01.ConsolidadorInsights.analisar_referencias(refs)
    assert insights['total_insights'] >= 1
    assert insights['linguagens_comuns']['Python'] == 2


def test_consolidador_insights_vazio(pesquisador_01):
    insights = pesquisador_01.ConsolidadorInsights.analisar_referencias([])
    assert insights['total_insights'] == 0
    assert insights['linguagens_comuns'] == {}


# =============================================================================
# GATES R1-R4
# =============================================================================

def _ref_ok(pesquisador_01, dias_atras=1):
    from datetime import datetime, timedelta, timezone
    data = (datetime.now(timezone.utc) - timedelta(days=dias_atras)).isoformat().replace('+00:00', 'Z')
    return pesquisador_01.Referencia(
        'proj', 'https://github.com/x/y', 'github',
        {'linguagens': 'Python', 'ultimo_commit': data}
    )


def test_gate_r1_urls_validas(pesquisador_01, monkeypatch):
    monkeypatch.setattr(pesquisador_01.requests, 'head', lambda *a, **kw: RespostaFake(200))
    refs = [_ref_ok(pesquisador_01)]
    gate = pesquisador_01.ValidadorGates._gate_r1_urls_validas(refs)
    assert gate.passou is True


def test_gate_r1_url_invalida(pesquisador_01, monkeypatch):
    monkeypatch.setattr(pesquisador_01.requests, 'head', lambda *a, **kw: RespostaFake(404))
    refs = [_ref_ok(pesquisador_01)]
    gate = pesquisador_01.ValidadorGates._gate_r1_urls_validas(refs)
    assert gate.passou is False


def test_gate_r2_atividade_recente(pesquisador_01):
    refs = [_ref_ok(pesquisador_01, dias_atras=1) for _ in range(5)]
    gate = pesquisador_01.ValidadorGates._gate_r2_atividade_recente(refs)
    assert gate.passou is True


def test_gate_r2_atividade_antiga(pesquisador_01):
    refs = [_ref_ok(pesquisador_01, dias_atras=200) for _ in range(5)]
    gate = pesquisador_01.ValidadorGates._gate_r2_atividade_recente(refs)
    assert gate.passou is False


def test_gate_r3_estrutura_valida(pesquisador_01):
    refs = [_ref_ok(pesquisador_01)]
    gate = pesquisador_01.ValidadorGates._gate_r3_estrutura_valida(refs)
    assert gate.passou is True


def test_gate_r4_quantidade_minima(pesquisador_01):
    refs = [_ref_ok(pesquisador_01) for _ in range(5)]
    gate = pesquisador_01.ValidadorGates._gate_r4_quantidade_minima(refs)
    assert gate.passou is True

    poucas = [_ref_ok(pesquisador_01) for _ in range(2)]
    gate_falhou = pesquisador_01.ValidadorGates._gate_r4_quantidade_minima(poucas)
    assert gate_falhou.passou is False


def test_executar_todos_gates(pesquisador_01, monkeypatch):
    monkeypatch.setattr(pesquisador_01.requests, 'head', lambda *a, **kw: RespostaFake(200))
    refs = [_ref_ok(pesquisador_01) for _ in range(5)]
    gates, todos_passaram = pesquisador_01.ValidadorGates.executar_todos(refs)
    assert len(gates) == 4
    assert todos_passaram is True


# =============================================================================
# GERADORPHASEINDEX — sem métricas fictícias
# =============================================================================

def test_gerador_index_com_linguagem_none_nao_crasha(pesquisador_01, monkeypatch):
    """Regressão de integração: mistura de refs com/sem linguagem detectada
    não pode derrubar json.dumps(sort_keys=True) em GeradorPhaseIndex.gerar
    (reproduzido em execução real contra a API do GitHub)."""
    monkeypatch.setattr(pesquisador_01.requests, 'head', lambda *a, **kw: RespostaFake(200))
    refs = [_ref_ok(pesquisador_01) for _ in range(4)]
    # Injeta None diretamente (defesa em profundidade: mesmo que uma fonte
    # futura não normalize, o gerador de índice não pode crashar por isso)
    refs.append(pesquisador_01.Referencia('sem-lang', 'https://github.com/x/sem-lang', 'github', {'linguagens': None}))
    insights = pesquisador_01.ConsolidadorInsights.analisar_referencias(refs)
    matriz = pesquisador_01.PesquisadorFase1._montar_matriz_stacks(refs, insights)
    gates, passou = pesquisador_01.ValidadorGates.executar_todos(refs)

    index = pesquisador_01.GeradorPhaseIndex.gerar('ideia', refs, insights, matriz, gates, passou, 1.0)
    assert index is not None


def test_gerador_index_sem_campos_fake(pesquisador_01, monkeypatch):
    monkeypatch.setattr(pesquisador_01.requests, 'head', lambda *a, **kw: RespostaFake(200))
    refs = [_ref_ok(pesquisador_01) for _ in range(5)]
    insights = pesquisador_01.ConsolidadorInsights.analisar_referencias(refs)
    matriz = pesquisador_01.PesquisadorFase1._montar_matriz_stacks(refs, insights)
    gates, passou = pesquisador_01.ValidadorGates.executar_todos(refs)

    index = pesquisador_01.GeradorPhaseIndex.gerar('ideia', refs, insights, matriz, gates, passou, 1.23)

    assert 'economizados_vs_ingenue' not in index['tokens']
    assert index['validacoes']['total_checks'] == 4
    assert index['validacoes']['passou'] == sum(1 for g in gates if g.passou)

    saida_github = index['saidas_estruturadas']['referencias_github']
    saida_hf = index['saidas_estruturadas']['referencias_huggingface']
    # Hashes de saídas diferentes não podem ser iguais (bug corrigido: eram o mesmo checksum global)
    assert saida_github['hash'] != saida_hf['hash']
    assert saida_github['tamanho_bytes'] > 0


# =============================================================================
# PESQUISADORFASE1 — orquestrador completo
# =============================================================================

def test_executar_fluxo_completo(tmp_path, pesquisador_01, monkeypatch):
    monkeypatch.setattr(
        pesquisador_01.requests, 'get',
        lambda url, **kw: RespostaFake(200, {'items': [ITEM_GITHUB_VALIDO]}) if 'github' in url else RespostaFake(200, [])
    )
    monkeypatch.setattr(pesquisador_01.requests, 'head', lambda *a, **kw: RespostaFake(200))

    # Gate R4 exige >= 5 referências: gera 5 itens distintos do GitHub
    itens = [dict(ITEM_GITHUB_VALIDO, full_name=f'exemplo/projeto{i}', html_url=f'https://github.com/exemplo/projeto{i}') for i in range(5)]
    monkeypatch.setattr(
        pesquisador_01.requests, 'get',
        lambda url, **kw: RespostaFake(200, {'items': itens}) if 'github' in url else RespostaFake(200, [])
    )

    pesquisador = pesquisador_01.PesquisadorFase1(tmp_path / 'cache')
    index = pesquisador.executar('sistema de gestão')

    assert index is not None
    assert index['status'] == 'COMPLETO'
    assert (tmp_path / 'cache' / '_phase_01_index.json').exists()
    assert (tmp_path / 'cache' / 'data' / 'referencias_github.json').exists()
    assert (tmp_path / 'cache' / 'data' / 'insights_phase1.json').exists()
    assert (tmp_path / 'cache' / 'data' / 'matriz_stacks.json').exists()


def test_executar_falha_gates(tmp_path, pesquisador_01, monkeypatch):
    """Menos de 5 referências => gate R4 falha => executar() retorna None."""
    monkeypatch.setattr(
        pesquisador_01.requests, 'get',
        lambda url, **kw: RespostaFake(200, {'items': [ITEM_GITHUB_VALIDO]}) if 'github' in url else RespostaFake(200, [])
    )
    monkeypatch.setattr(pesquisador_01.requests, 'head', lambda *a, **kw: RespostaFake(200))

    pesquisador = pesquisador_01.PesquisadorFase1(tmp_path / 'cache')
    resultado = pesquisador.executar('ideia qualquer')
    assert resultado is None


# =============================================================================
# MAIN (CLI)
# =============================================================================

def test_main_sucesso(tmp_path, pesquisador_01, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['01_pesquisador.py', 'minha ideia', '--cache-dir', str(tmp_path / 'cache')]
    )
    monkeypatch.setattr(
        pesquisador_01.PesquisadorFase1, 'executar',
        lambda self, ideia: {'status': 'COMPLETO'}
    )
    with pytest.raises(SystemExit) as exc:
        pesquisador_01.main()
    assert exc.value.code == 0


def test_main_falha(tmp_path, pesquisador_01, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['01_pesquisador.py', 'minha ideia', '--cache-dir', str(tmp_path / 'cache')]
    )
    monkeypatch.setattr(
        pesquisador_01.PesquisadorFase1, 'executar',
        lambda self, ideia: None
    )
    with pytest.raises(SystemExit) as exc:
        pesquisador_01.main()
    assert exc.value.code == 1
