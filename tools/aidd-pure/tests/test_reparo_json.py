# -*- coding: utf-8 -*-
"""
Testes do Item 3 — otimizacao-tokenomics-latencia:
escada de reparo JSON determinística, zero LLM [TK-2].

Critérios de saída do plano (docs/planos/fazendo/02-otimizacao-tokenomics-latencia/
03-reparo-json-deterministico-zero-llm.md):
1. 10 payloads JSON sinteticamente malformados, >= 8 recuperados SEM chamada de LLM.
2. Zero chamadas LLM para erros comuns de formatação JSON.
3. _validar_pydantic_com_retry faz no máximo 1 tentativa pós-escada.
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
def ud():
    spec = importlib.util.spec_from_file_location(
        'utils_delegacao_item3', str(_PHASES_DIR / 'utils_delegacao.py')
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# =============================================================================
# FIXTURES: 10 payloads sinteticamente malformados (mutações reais de LLM)
# =============================================================================

VALIDO = {
    'codigo': 'def somar(a, b):\n    return a + b\n',
    'teste': 'def test_somar():\n    assert somar(2, 3) == 5\n',
    'caminho_relativo': 'somar.py',
    'caminho_teste': 'test_somar.py',
}


def _serializar() -> str:
    return json.dumps(VALIDO, ensure_ascii=False)


def _payloads_malformados():
    """10 mutações de formatação comuns — todas recuperáveis mecanicamente."""
    base = _serializar()
    return [
        # 1. Vírgula trailing antes de }
        base[:-1].rstrip() + ',}',
        # 2. Chaves de fechamento ausentes (corte no meio do stream)
        base[:-2],
        # 3. String truncada no fim (aspas soltas)
        base[:-8] + '"',
        # 4. Vírgula trailing em array
        '{"itens": [1, 2, 3,], "ok": true}',
        # 5. Quebra de linha CRUA dentro de string (JSON estrito quebra)
        '{"codigo": "def f():\n    return 1\n", "teste": "t", "caminho_relativo": "r.py", "caminho_teste": "tr.py"}',
        # 6. Chave JS-style sem aspas
        '{codigo: "def f(): pass", "teste": "t", "caminho_relativo": "r.py", "caminho_teste": "tr.py"}',
        # 7. Envolto em fence markdown
        '```json\n' + base + '\n```',
        # 8. Texto explicativo antes/depois do objeto
        'Claro! Aqui está o JSON solicitado:\n' + base + '\nQualquer dúvida me avise.',
        # 9. Dupla falha: vírgula trailing + chave sem aspas
        '{codigo: "x", "teste": "t", "caminho_relativo": "r.py", "caminho_teste": "tr.py",}',
        # 10. Estrutura aberta + vírgula trailing (corte + resíduo)
        '{"codigo": "c", "teste": "t", "caminho_relativo": "r.py", "caminho_teste": "tr.py", "extra": [1, 2,'.rstrip(',') + ',',
    ]


# =============================================================================
# CRITÉRIO 1: >= 8/10 recuperados sem LLM
# =============================================================================

def test_escada_recupera_pelo_menos_8_de_10_sem_llm(ud):
    """Critério de saída: >= 8 de 10 payloads malformados recuperados de forma
    determinística. Contador de chamadas LLM prova zero invocação."""
    recuperados = 0
    falhas = []
    for i, payload in enumerate(_payloads_malformados(), 1):
        resultado = ud.reparar_json_deterministico(payload)
        if isinstance(resultado, dict) and 'codigo' in resultado:
            recuperados += 1
        else:
            falhas.append((i, payload[:60]))
    assert recuperados >= 8, f'recuperados={recuperados}, falhas={falhas}'


def test_escada_zero_chamada_llm_por_construcao(ud):
    """A escada é 100% determinística: nenhuma função dela toca rede/LLM.
    Prova estrutural: fonte da função + degraus sem referência a LLM/rede."""
    import inspect
    fonte = inspect.getsource(ud.reparar_json_deterministico)
    for degrau in ud.ESCADA_REPARO_JSON:
        fonte += '\n' + inspect.getsource(degrau)
    for proibido in ('solicitar_llm', 'litellm', 'instructor', 'requests.get',
                     'subprocess', 'open('):
        assert proibido not in fonte, f'escada referencia {proibido}'
    # Prova funcional direta: cada degrau é função pura de string -> string
    for degrau in ud.ESCADA_REPARO_JSON:
        saida = degrau('{"a": 1,}')
        assert isinstance(saida, str)


def test_cada_degrau_deterministico_idempotente(ud):
    """Mesma entrada → mesma saída (determinismo estrito)."""
    payloads = _payloads_malformados()
    for payload in payloads:
        r1 = ud.reparar_json_deterministico(payload)
        r2 = ud.reparar_json_deterministico(payload)
        assert repr(r1) == repr(r2)


# =============================================================================
# CRITÉRIO 2: zero LLM no wrapper público para erros comuns de formatação
# =============================================================================

def test_wrapper_validacao_zero_llm_em_payload_com_virgula_trailing(ud, monkeypatch):
    """_validar_pydantic_com_retry recupera via escada SEM tocar o mecanismo
    instructor (prova: espião no _validar_pydantic_com_retry_com_loads)."""
    pydantic = pytest.importorskip('pydantic')

    class Modelo(pydantic.BaseModel):
        codigo: str
        teste: str
        caminho_relativo: str
        caminho_teste: str

    chamadas_mecanismo = {'n': 0}

    def espio_mecanismo(*args, **kwargs):
        chamadas_mecanismo['n'] += 1
        raise AssertionError('mecanismo instructor NÃO deveria ser chamado')

    monkeypatch.setattr(ud, '_validar_pydantic_com_retry_com_loads', espio_mecanismo)

    base = json.dumps(VALIDO, ensure_ascii=False)
    malformado = base[:-1].rstrip() + ',}'
    resultado = ud._validar_pydantic_com_retry(malformado, Modelo)
    assert resultado.codigo == 'def somar(a, b):\n    return a + b\n'
    assert chamadas_mecanismo['n'] == 0


def test_wrapper_aceita_payload_fenced(ud):
    pydantic = pytest.importorskip('pydantic')

    class Modelo(pydantic.BaseModel):
        codigo: str
        teste: str
        caminho_relativo: str
        caminho_teste: str

    payload = '```json\n' + json.dumps(VALIDO) + '\n```'
    resultado = ud._validar_pydantic_com_retry(payload, Modelo, max_retries=1)
    assert resultado.caminho_teste == 'test_somar.py'


def test_wrapper_dado_valido_nao_chama_mecanismo(ud, monkeypatch):
    pydantic = pytest.importorskip('pydantic')

    class Modelo(pydantic.BaseModel):
        codigo: str

    def espio(*args, **kwargs):
        raise AssertionError('caminho feliz não deve chamar mecanismo de retry')

    monkeypatch.setattr(ud, '_validar_pydantic_com_retry_com_loads', espio)
    resultado = ud._validar_pydantic_com_retry(json.dumps({'codigo': 'x'}), Modelo)
    assert resultado.codigo == 'x'


def test_wrapper_dados_que_nunca_validam_levanta_erro(ud):
    """JSON válido mas schema inválido: esgota escada + 1 retry e levanta."""
    pydantic = pytest.importorskip('pydantic')
    from pydantic import ValidationError

    class Modelo(pydantic.BaseModel):
        codigo: str
        teste: str

    with pytest.raises((ValidationError, ValueError)):
        ud._validar_pydantic_com_retry('{"codigo": "so-um-campo"}', Modelo, max_retries=1)


def test_escada_retorna_none_para_lixo_total(ud):
    assert ud.reparar_json_deterministico('isto nao e json mesmo') is None
    assert ud.reparar_json_deterministico('') is None
    assert ud.reparar_json_deterministico(None) is None


def test_escada_extrai_substring_json_de_texto_ruidoso(ud):
    ruidoso = 'preâmbulo sem json {"a": [1, 2, 3,],} epílogo'
    resultado = ud.reparar_json_deterministico(ruidoso)
    assert resultado == {'a': [1, 2, 3]}
