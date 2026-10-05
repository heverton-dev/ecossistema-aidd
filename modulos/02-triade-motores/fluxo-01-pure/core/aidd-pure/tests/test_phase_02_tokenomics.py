# -*- coding: utf-8 -*-
"""
Testes do Item 2 — otimizacao-tokenomics-latencia:
orçador de contexto no handoff Fase 1 → Fase 2 [TK-1].

Critérios de saída do plano (docs/planos/fazendo/02-otimizacao-tokenomics-latencia/
02-orcador-de-contexto-handoff-fase-01-para-02.md):
1. Handoff para a Fase 2 consome <= 5.000 tokens mesmo com 30+ referências brutas.
2. Teste comprovando integridade dos campos essenciais após a poda.
3. Cabeçalho informativo: total avaliado vs incluído.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_PHASES_DIR = Path(__file__).resolve().parent.parent / 'scripts' / 'phases'
if str(_PHASES_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASES_DIR))


@pytest.fixture(scope='module')
def mod2():
    spec = importlib.util.spec_from_file_location(
        'analisador_02_tokenomics', str(_PHASES_DIR / '02_analisador.py')
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _contar_tokens(texto: str) -> int:
    """Mesma medição do módulo (tiktoken real quando disponível)."""
    try:
        import tiktoken
        return len(tiktoken.get_encoding('cl100k_base').encode(texto))
    except Exception:
        return max(len(texto.split()), len(texto) // 4, 1)


def _ref_bruta(i: int, inflar: bool = True) -> dict:
    """Referência realista no formato da Fase 1, com metadados inflados."""
    ref = {
        'nome': f'owner/projeto-similar-{i}',
        'url': f'https://github.com/owner/projeto-similar-{i}',
        'fonte': 'github',
        'metadata': {
            'stars': 100 + i * 37,
            'forks': 10 + i,
            'linguagens': 'Python',
            'ultimo_commit': '2026-09-01T12:00:00+00:00',
            'licenca': 'MIT',
            'descricao': f'Descricao util do projeto similar numero {i} para analise da ideia.',
        },
    }
    if inflar:
        # Metadados inflados que NÃO podem chegar ao prompt da Fase 2
        ref['metadata']['tags'] = [f'tag-{j}' for j in range(40)]
        ref['metadata']['commits_por_mes'] = list(range(120))
        ref['metadata']['arvore_arquivos'] = [f'src/modulo_{j}/arquivo_{j}.py' for j in range(200)]
        ref['metadata']['readme_integral'] = 'x' * 8000
    return ref


def _payload_30_refs() -> list:
    return [_ref_bruta(i) for i in range(30)]


# =============================================================================
# CRITÉRIO 1: teto de tokens respeitado com 30+ referências brutas
# =============================================================================

def test_handoff_30_referencias_respeita_teto_5000_tokens(mod2):
    """Critério de saída 1: <= 5.000 tokens com 30 refs grandes na entrada."""
    payload = _payload_30_refs()
    handoff = mod2.montar_handoff_referencias(payload, mod2.TETO_TOKENS_HANDOFF_FASE2)
    tokens = _contar_tokens(handoff)
    assert tokens <= mod2.TETO_TOKENS_HANDOFF_FASE2, (
        f'handoff com {tokens} tokens excede o teto de {mod2.TETO_TOKENS_HANDOFF_FASE2}'
    )
    # Economia real: o dump bruto seria muito maior
    dump_bruto = json.dumps(payload, indent=2, ensure_ascii=False)
    assert tokens < _contar_tokens(dump_bruto) * 0.5, (
        'handoff podado deve ser < 50% do dump bruto (economia [TK-1])'
    )


def test_handoff_respeita_teto_customizado_baixo(mod2):
    payload = _payload_30_refs()
    handoff = mod2.montar_handoff_referencias(payload, max_tokens=800)
    assert _contar_tokens(handoff) <= 800


def test_handoff_lista_vazia_e_entradas_invalidas(mod2):
    assert mod2.montar_handoff_referencias([]) == '{}'
    assert mod2.montar_handoff_referencias(None) == '{}'
    assert mod2.montar_handoff_referencias('nao-lista') == '{}'


def test_handoff_payload_legado_dict_sem_lista(mod2):
    """Payload legado (ex.: insights_phase1.json ou {'ref': 'x'}) não explode."""
    handoff = mod2.montar_handoff_referencias({'ref': 'x'})
    assert _contar_tokens(handoff) <= mod2.TETO_TOKENS_HANDOFF_FASE2
    handoff_insights = mod2.montar_handoff_referencias({
        'total_insights': 3,
        'insights': [{'tipo': 'stack', 'descricao': 'python sqlite', 'frequencia': 5, 'fontes': ['a']}],
        'linguagens_comuns': {'Python': 8},
    })
    parsed = json.loads(handoff_insights)
    assert parsed['total_insights'] == 3


# =============================================================================
# CRITÉRIO 2: integridade dos campos essenciais após a poda
# =============================================================================

def test_integridade_campos_essenciais_preservados(mod2):
    """Critério de saída 2: título/resumo/URL/dados-chave sobrevivem à poda."""
    ref = _ref_bruta(7, inflar=False)
    handoff = mod2.montar_handoff_referencias([ref])
    parsed = json.loads(handoff)
    refs_out = parsed['referencias']
    assert len(refs_out) == 1
    out = refs_out[0]
    assert out['nome'] == 'owner/projeto-similar-7'
    assert out['url'] == 'https://github.com/owner/projeto-similar-7'
    assert out['fonte'] == 'github'
    assert 'Descricao util' in out['descricao']
    assert out['stars'] == 100 + 7 * 37


def test_metadados_inflados_descartados(mod2):
    ref = _ref_brata = _ref_bruta(1, inflar=True)
    handoff = mod2.montar_handoff_referencias([ref])
    parsed = json.loads(handoff)
    out = parsed['referencias'][0]
    serial = json.dumps(out)
    assert 'readme_integral' not in serial
    assert 'arvore_arquivos' not in serial
    assert 'commits_por_mes' not in serial


def test_descricao_longa_truncada_com_elipse(mod2):
    ref = _ref_bruta(2, inflar=False)
    ref['metadata']['descricao'] = 'z' * 500
    handoff = mod2.montar_handoff_referencias([ref])
    out = json.loads(handoff)['referencias'][0]
    assert out['descricao'].endswith('...')
    assert len(out['descricao']) <= 200


# =============================================================================
# CRITÉRIO 3: cabeçalho de auditoria + determinismo do top-k
# =============================================================================

def test_cabecalho_total_avaliado_vs_incluido(mod2):
    payload = _payload_30_refs()
    handoff = mod2.montar_handoff_referencias(payload)
    parsed = json.loads(handoff)
    cab = parsed['_handoff']
    assert cab['handoff_fase1_fase2'] is True
    assert cab['referencias_avaliadas'] == 30
    assert 0 < cab['referencias_incluidas'] <= 30
    assert cab['poda_aplicada'] is True


def test_top_k_ordenado_por_score_estrelas(mod2):
    """Determinismo: ref com mais estrelas entra primeiro (score desc)."""
    ref_poucas = _ref_bruta(0, inflar=False)
    ref_poucas['metadata']['stars'] = 100
    ref_muitas = _ref_bruta(1, inflar=False)
    ref_muitas['metadata']['stars'] = 99999
    handoff = mod2.montar_handoff_referencias([ref_poucas, ref_muitas])
    out = json.loads(handoff)['referencias']
    assert out[0]['nome'] == 'owner/projeto-similar-1'


def test_integracao_analisador_usa_orcador(mod2, monkeypatch):
    """Integração: _analisar_ideia_com_llm injeta o handoff podado no prompt."""
    capturados = {}

    def fake_solicitar(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        capturados['prompt'] = prompt
        return {
            'conteudo': json.dumps({'objetivo': 'x', 'publico_alvo': 'y',
                                    'funcionalidades': ['f'], 'referencias_utilizadas': ['r']}),
            'tokens_consumidos': 10, 'modelo_usado': 't', 'timestamp_resposta': 'x',
        }

    monkeypatch.setattr(mod2, 'solicitar_llm', fake_solicitar)
    analisador = mod2.AnalisadorFase2(Path(_PHASES_DIR) / '..' / '_cache_fake_item2')
    resultado = analisador._analisar_ideia_com_llm('ideia teste', _payload_30_refs())
    assert resultado is not None
    prompt = capturados['prompt']
    assert '_handoff' in prompt          # cabeçalho do orçador presente
    assert 'readme_integral' not in prompt  # metadado inflado NÃO vazou
    assert 'arvore_arquivos' not in prompt
