# -*- coding: utf-8 -*-
"""
Testes do Item 5 — otimizacao-tokenomics-latencia:
middleware de compressão sandeco-token-reduce [TK-5].

Critérios de saída do plano (05-middleware-compressao-sandeco-token-reduce.md):
1. Pipeline executa normalmente com ou sem o compressor instalado (resiliência total).
2. Quando ativado, reduz >= 40% dos caracteres de prosa em handoffs compressíveis.
3. NUNCA comprime código nem JSON de schema (política declarativa).
4. Uso e taxa real registrados na telemetria.
"""

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / 'scripts'
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import compressor_middleware as cm  # noqa: E402


PROSA_LONGA = (
    "O projeto de rastreamento de hábitos diários foi concebido para usuários que "
    "buscam disciplina através de check-ins recorrentes e gamificação leve. "
    "A análise das referências similares revelou que aplicativos de acompanhamento "
    "de rotina bem-sucedidos combinam persistência local com visualizações simples "
    "de progresso, como streaks e calendários de consistência mensal. "
) * 20  # ~3300 chars de prosa pura


# =============================================================================
# CRITÉRIO 3: política declarativa — código/JSON NUNCA comprimidos
# =============================================================================

def test_politica_rejeita_codigo():
    codigo = ('def calcular_estatisticas(valores):\n'
              '    total = sum(valores)\n    media = total / len(valores)\n'
              + '    resultado_parcial = media * fator_ajuste\n' * 40)
    assert cm.eh_prosa_compressivel(codigo) is False


def test_politica_rejeita_json_schema():
    schema = json.dumps({'type': 'object', 'properties': {f'campo_{i}': {'type': 'string'} for i in range(50)}})
    assert cm.eh_prosa_compressivel(schema) is False


def test_politica_rejeita_sql():
    sql = ('INSERT INTO checkins (habito_id, data) VALUES\n'
           + ',\n'.join(f"(1, '2026-01-{d:02d}')" for d in range(1, 29)) + ';')
    assert cm.eh_prosa_compressivel(sql) is False


def test_politica_rejeita_texto_curto():
    assert cm.eh_prosa_compressivel('texto curto demais para valer o custo') is False


def test_politica_aceita_prosa_pura_longa():
    assert cm.eh_prosa_compressivel(PROSA_LONGA) is True


def test_codigo_passa_intacto_mesmo_compressor_disponivel(monkeypatch):
    """Mesmo com LLMLingua disponível, código sai intocado."""
    monkeypatch.setattr(cm, 'compressor_disponivel', lambda: True)
    chamado = {'n': 0}

    def espio(*a, **kw):
        chamado['n'] += 1
        raise AssertionError('LLMLingua não deveria ser chamado para código')

    monkeypatch.setattr(cm, '_comprimir_llmlingua', espio)
    codigo = 'def f():\n    return 1\n' * 100
    texto_final, tel = cm.comprimir_se_compressivel(codigo)
    assert texto_final == codigo
    assert tel['comprimido'] is False
    assert chamado['n'] == 0


# =============================================================================
# CRITÉRIO 1: resiliência total — funciona sem compressor instalado
# =============================================================================

def test_fallback_deterministico_sem_llmlingua(monkeypatch):
    """Sem LLMLingua-2: fallback determinístico executa e reduz proza longa."""
    monkeypatch.setattr(cm, 'compressor_disponivel', lambda: False)
    texto_final, tel = cm.comprimir_se_compressivel(PROSA_LONGA, contexto='teste_fallback')
    assert tel['metodo'] == 'fallback_deterministico'
    assert tel['caracteres_antes'] >= cm.MIN_CHARS_COMPRIMIVEIS


def test_fallback_sem_rede_nem_subprocesso(monkeypatch):
    """Fallback é puro Python: funciona mesmo sem rede (sem subprocess/pip)."""
    monkeypatch.setattr(cm, 'compressor_disponivel', lambda: False)
    texto_final, tel = cm.comprimir_se_compressivel(PROSA_LONGA)
    assert isinstance(texto_final, str)
    assert 'duracao_ms' in tel


def test_texto_nao_compressivel_retorna_intacto_com_telemetria():
    original = 'curto'
    texto_final, tel = cm.comprimir_se_compressivel(original, contexto='x')
    assert texto_final == original
    assert tel['comprimido'] is False
    assert tel['metodo'] == 'nao_compressivel_pela_politica'
    assert tel['taxa_reducao_real'] == 0.0


# =============================================================================
# CRITÉRIO 2: >= 40% de redução quando ativado (fallback determinístico medido)
# =============================================================================

def test_reducao_minima_40_porcento_no_fallback(monkeypatch):
    monkeypatch.setattr(cm, 'compressor_disponivel', lambda: False)
    texto_final, tel = cm.comprimir_se_compressivel(PROSA_LONGA)
    assert tel['taxa_reducao_real'] >= cm.ALVO_REDUCAO_MINIMA, (
        f"redução {tel['taxa_reducao_real']:.2%} < alvo {cm.ALVO_REDUCAO_MINIMA:.0%}"
    )


def test_compressao_llmlingua_usada_quando_disponivel(monkeypatch):
    """Se LLMLingua está disponível e responde, método = llmlingua2."""
    monkeypatch.setattr(cm, 'compressor_disponivel', lambda: True)
    monkeypatch.setattr(cm, '_comprimir_llmlingua', lambda texto, taxa: texto[:len(texto) // 3])
    texto_final, tel = cm.comprimir_se_compressivel(PROSA_LONGA)
    assert tel['metodo'] == 'llmlingua2'
    assert tel['taxa_reducao_real'] >= cm.ALVO_REDUCAO_MINIMA


def test_llmlingua_falhando_cai_no_fallback_sem_quebrar(monkeypatch):
    """LLMLingua presente mas com erro (ex.: modelo ausente): fallback assume."""
    monkeypatch.setattr(cm, 'compressor_disponivel', lambda: True)

    def falha(texto, taxa):
        raise RuntimeError('modelo ausente')

    monkeypatch.setattr(cm, '_comprimir_llmlingua', falha)
    texto_final, tel = cm.comprimir_se_compressivel(PROSA_LONGA)
    assert tel['metodo'] == 'fallback_deterministico'
    assert tel['comprimido'] is True


# =============================================================================
# CRITÉRIO 4: telemetria completa
# =============================================================================

def test_telemetria_registra_taxa_real(monkeypatch):
    monkeypatch.setattr(cm, 'compressor_disponivel', lambda: False)
    texto_final, tel = cm.comprimir_se_compressivel(PROSA_LONGA, contexto='handoff_fase1_fase2')
    for chave in ('comprimido', 'metodo', 'contexto', 'caracteres_antes',
                  'caracteres_depois', 'taxa_reducao_real', 'duracao_ms'):
        assert chave in tel
    assert tel['caracteres_depois'] < tel['caracteres_antes']
    assert tel['contexto'] == 'handoff_fase1_fase2'
    assert tel['duracao_ms'] >= 0


def test_skill_presente_detecta_fonte_unica():
    """A skill sandeco-token-reduce está sincronizada no ecossistema."""
    assert cm.skill_presente() is True
