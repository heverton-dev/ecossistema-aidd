# -*- coding: utf-8 -*-
"""
Testes reais da Phase 2 (Analisador de Ideia) — Correção 5/5.

Cobre: gates A1-A4, AnalisadorFase2 (init, executar, _analisar_ideia_com_llm,
_gerar_index) e main(). A chamada LLM externa é mockada (protocolo delegado).
"""

import json
import sys
from pathlib import Path

import pytest


# =============================================================================
# HELPERS
# =============================================================================

def resposta_llm(conteudo, tokens=123):
    """Resposta estruturada no formato do protocolo delegado."""
    return {
        'conteudo': conteudo,
        'tokens_consumidos': tokens,
        'modelo_usado': 'teste',
        'timestamp_resposta': '2026-08-30T00:00:00Z',
    }


def fake_solicitar_llm_sucesso(analise):
    """Retorna uma função que simula solicitar_llm devolvendo JSON válido."""
    def _fake(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        return resposta_llm(json.dumps(analise, ensure_ascii=False))
    return _fake


# =============================================================================
# GATE (estrutura base)
# =============================================================================

def test_gate_to_dict(analisador_02):
    gate = analisador_02.Gate('A1', 'descricao', True, 'detalhes')
    assert gate.to_dict() == {
        'gate_id': 'A1',
        'descricao': 'descricao',
        'status': 'PASSOU',
        'detalhes': 'detalhes',
    }

    gate_falhou = analisador_02.Gate('A1', 'descricao', False, 'detalhes')
    assert gate_falhou.to_dict()['status'] == 'FALHOU'


# =============================================================================
# GATES A1-A4
# =============================================================================

def test_gate_a1_schema_valido(analisador_02, analise_valida):
    gate = analisador_02.ValidadorGatesPhase2._gate_a1_schema_valido(analise_valida)
    assert gate.passou is True
    assert '4/4' in gate.detalhes

    incompleta = {'objetivo': 'x'}
    gate_falhou = analisador_02.ValidadorGatesPhase2._gate_a1_schema_valido(incompleta)
    assert gate_falhou.passou is False

    gate_tipo_invalido = analisador_02.ValidadorGatesPhase2._gate_a1_schema_valido(None)
    assert gate_tipo_invalido.passou is False
    assert gate_tipo_invalido.detalhes == "Schema inválido"


def test_gate_a2_zero_alucinacao(analisador_02, analise_valida):
    gate = analisador_02.ValidadorGatesPhase2._gate_a2_zero_alucinacao(analise_valida)
    assert gate.passou is True
    assert '2 referências' in gate.detalhes

    sem_refs = dict(analise_valida, referencias_utilizadas=[])
    gate_falhou = analisador_02.ValidadorGatesPhase2._gate_a2_zero_alucinacao(sem_refs)
    assert gate_falhou.passou is False
    assert '0 referências' in gate_falhou.detalhes

    refs_none = dict(analise_valida, referencias_utilizadas=None)
    gate_falhou_none = analisador_02.ValidadorGatesPhase2._gate_a2_zero_alucinacao(refs_none)
    assert gate_falhou_none.passou is False
    assert '0 referências' in gate_falhou_none.detalhes

    sem_campo = {k: v for k, v in analise_valida.items() if k != 'referencias_utilizadas'}
    gate_falhou_sem_campo = analisador_02.ValidadorGatesPhase2._gate_a2_zero_alucinacao(sem_campo)
    assert gate_falhou_sem_campo.passou is False


def test_gate_a3_dados_completo(analisador_02, analise_valida):
    gate = analisador_02.ValidadorGatesPhase2._gate_a3_dados_completo(analise_valida)
    assert gate.passou is True
    assert '5/5' in gate.detalhes

    esparsa = {'objetivo': 'x', 'publico_alvo': 'y'}
    gate_falhou = analisador_02.ValidadorGatesPhase2._gate_a3_dados_completo(esparsa)
    assert gate_falhou.passou is False


def test_gate_a4_qualidade_linguagem(analisador_02, analise_valida):
    gate = analisador_02.ValidadorGatesPhase2._gate_a4_qualidade_linguagem(analise_valida)
    assert gate.passou is True

    curta = dict(analise_valida, objetivo='curto')
    gate_falhou = analisador_02.ValidadorGatesPhase2._gate_a4_qualidade_linguagem(curta)
    assert gate_falhou.passou is False


def test_executar_todos_gates_passam(analisador_02, analise_valida):
    gates, todos_passaram = analisador_02.ValidadorGatesPhase2.executar_todos(analise_valida)
    assert len(gates) == 4
    assert todos_passaram is True
    assert all(g.passou for g in gates)


def test_executar_todos_gates_falham(analisador_02):
    analise_ruim = {'objetivo': 'x'}
    gates, todos_passaram = analisador_02.ValidadorGatesPhase2.executar_todos(analise_ruim)
    assert todos_passaram is False
    assert any(not g.passou for g in gates)


# =============================================================================
# ANALISADORFASE2
# =============================================================================

def test_analisador_init(tmp_path, analisador_02):
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    assert (tmp_path / 'cache').exists()
    assert analisador.modelo_final  # modelo detectado ou override
    assert analisador.modelo_nome_amigavel


def test_analisar_ideia_com_llm_sucesso(tmp_path, analisador_02, analise_valida, monkeypatch):
    monkeypatch.setattr(analisador_02, 'solicitar_llm', fake_solicitar_llm_sucesso(analise_valida))
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    resultado = analisador._analisar_ideia_com_llm('ideia', {'ref': 'x'})
    assert resultado is not None
    assert resultado['objetivo'] == analise_valida['objetivo']
    assert resultado['_tokens_reais_consumidos'] == 123
    assert resultado['_modelo_usado'] == 'teste'


def test_analisar_ideia_com_llm_json_invalido(tmp_path, analisador_02, monkeypatch):
    monkeypatch.setattr(
        analisador_02, 'solicitar_llm',
        lambda prompt, contexto, fase, modelo=None, timeout_delegacao=30: resposta_llm('não é json')
    )
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    assert analisador._analisar_ideia_com_llm('ideia', {}) is None


def test_analisar_ideia_com_llm_erro_processamento(tmp_path, analisador_02, monkeypatch):
    monkeypatch.setattr(
        analisador_02, 'solicitar_llm',
        lambda prompt, contexto, fase, modelo=None, timeout_delegacao=30: resposta_llm(12345)
    )
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    assert analisador._analisar_ideia_com_llm('ideia', {}) is None


def test_analisar_ideia_com_llm_sem_resposta(tmp_path, analisador_02, monkeypatch):
    monkeypatch.setattr(
        analisador_02, 'solicitar_llm',
        lambda prompt, contexto, fase, modelo=None, timeout_delegacao=30: None
    )
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    assert analisador._analisar_ideia_com_llm('ideia', {}) is None


def test_gerar_index(analisador_02, analise_valida):
    gates, _ = analisador_02.ValidadorGatesPhase2.executar_todos(analise_valida)
    index = analisador_02.AnalisadorFase2(Path('.'))._gerar_index(analise_valida, gates, 1.5)
    assert index['fase_id'] == 'phase_02_analysis'
    assert index['status'] == 'COMPLETO'
    assert index['tokens']['consumidos'] is None  # sem _tokens_reais_consumidos
    assert index['resume_info']['pode_prosseguir'] is True
    assert len(index['gates_executados']) == 4


def test_executar_sucesso(tmp_path, analisador_02, analise_valida, monkeypatch):
    monkeypatch.setattr(analisador_02, 'solicitar_llm', fake_solicitar_llm_sucesso(analise_valida))
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    index = analisador.executar('Sistema de vídeos YouTube', {'refs': []})

    assert index is not None
    assert index['status'] == 'COMPLETO'
    assert index['tokens']['consumidos'] == 123
    assert (tmp_path / 'cache' / '_phase_02_index.json').exists()
    assert (tmp_path / 'cache' / 'data' / 'analise_phase2.json').exists()


def test_executar_llm_falha(tmp_path, analisador_02, monkeypatch):
    monkeypatch.setattr(
        analisador_02, 'solicitar_llm',
        lambda prompt, contexto, fase, modelo=None, timeout_delegacao=30: None
    )
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    assert analisador.executar('ideia', {}) is None


def test_analisar_ideia_com_llm_sem_referencias_nao_fabrica_strings(tmp_path, analisador_02, analise_valida, monkeypatch):
    """Garante que quando o LLM e a Fase 1 não fornecem referências, nenhuma string falsa é fabricada."""
    analise_sem_refs = dict(analise_valida)
    analise_sem_refs.pop('referencias_utilizadas', None)

    monkeypatch.setattr(analisador_02, 'solicitar_llm', fake_solicitar_llm_sucesso(analise_sem_refs))
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    resultado = analisador._analisar_ideia_com_llm('ideia', {})

    assert resultado is not None
    assert resultado.get('referencias_utilizadas') == []
    assert 'Referência da Fase 1' not in resultado.get('referencias_utilizadas', [])


def test_analisar_ideia_com_llm_recupera_apenas_reais_quando_disponiveis(tmp_path, analisador_02, analise_valida, monkeypatch):
    """Garante que apenas referências reais da Fase 1 são aproveitadas se o LLM omitir o campo."""
    analise_sem_refs = dict(analise_valida)
    analise_sem_refs.pop('referencias_utilizadas', None)

    monkeypatch.setattr(analisador_02, 'solicitar_llm', fake_solicitar_llm_sucesso(analise_sem_refs))
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    refs_reais = {'referencias': [{'titulo': 'Repo Real A'}, {'url': 'https://github.com/real/b'}]}
    resultado = analisador._analisar_ideia_com_llm('ideia', refs_reais)

    assert resultado is not None
    assert resultado.get('referencias_utilizadas') == ['Repo Real A', 'https://github.com/real/b']


def test_executar_reprova_quando_llm_nao_cita_referencias_e_sem_refs_reais(tmp_path, analisador_02, analise_valida, monkeypatch):
    """Garante que executar() retorna None (falha) quando não há referências reais, reprovando no Gate A2 honestamente."""
    analise_sem_refs = dict(analise_valida)
    analise_sem_refs.pop('referencias_utilizadas', None)

    monkeypatch.setattr(analisador_02, 'solicitar_llm', fake_solicitar_llm_sucesso(analise_sem_refs))
    analisador = analisador_02.AnalisadorFase2(tmp_path / 'cache')
    resultado = analisador.executar('ideia', {})
    assert resultado is None


# =============================================================================
# MAIN (CLI)
# =============================================================================

def test_main_sucesso(tmp_path, analisador_02, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['02_analisador.py', 'minha ideia', '--cache-dir', str(tmp_path / 'cache')]
    )
    monkeypatch.setattr(
        analisador_02.AnalisadorFase2, 'executar',
        lambda self, ideia, refs: {'status': 'COMPLETO'}
    )
    with pytest.raises(SystemExit) as exc:
        analisador_02.main()
    assert exc.value.code == 0


def test_main_falha(tmp_path, analisador_02, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['02_analisador.py', 'minha ideia', '--cache-dir', str(tmp_path / 'cache')]
    )
    monkeypatch.setattr(
        analisador_02.AnalisadorFase2, 'executar',
        lambda self, ideia, refs: None
    )
    with pytest.raises(SystemExit) as exc:
        analisador_02.main()
    assert exc.value.code == 1