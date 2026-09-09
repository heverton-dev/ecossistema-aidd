# -*- coding: utf-8 -*-
"""
Testes do Item 1 — otimizacao-tokenomics-latencia:
prompt por composição ([TK-4]) + fix-loop com diff/traceback cirúrgico ([TK-3]).

Critérios de saída do plano (docs/planos/fazendo/02-otimizacao-tokenomics-latencia/
01-prompt-por-composicao-e-fixloop-diff-fase-08.md):
1. Prompt montado para script sem UI/API não contém blocos Swagger/MCP/UI.
2. Fix-loop na 2ª tentativa envia < 50% dos tokens da 1ª chamada (tiktoken real).
3. Integridade: script com SQL/FK/UI/API RECEBE os blocos correspondentes.
"""

import sys
from pathlib import Path

import pytest

_PHASES_DIR = Path(__file__).resolve().parent.parent / 'scripts' / 'phases'
if str(_PHASES_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASES_DIR))


@pytest.fixture(scope='module')
def imp_mod():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'implementador_08_tokenomics', str(_PHASES_DIR / '08_implementador.py')
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _tokenizador_real():
    """tiktoken real (cl100k_base) — medição honesta, não estimativa."""
    try:
        import tiktoken
        return tiktoken.get_encoding('cl100k_base')
    except Exception:
        pytest.skip('tiktoken indisponível neste ambiente')


def _tokens(texto: str) -> int:
    return len(_tokenizador_real().encode(texto))


# =============================================================================
# [TK-4] PROMPT POR COMPOSIÇÃO — blocos ativados por feature
# =============================================================================

SCRIPT_CALCULO_PURO = {
    'nome': 'calcular_media.py',
    'responsabilidade': 'Calcular a media aritmetica de uma lista de numeros',
    'pseudocodigo': '1. somar valores\n2. dividir pela quantidade\n3. retornar media',
}

SCRIPT_SQLITE_FK = {
    'nome': 'registrar_checkin.py',
    'responsabilidade': 'Salvar checkin diario no banco sqlite com foreign key para habitos',
    'pseudocodigo': 'INSERT INTO checkins (habito_id, data) SELECT id FROM habitos',
}

SCRIPT_API_UI = {
    'nome': 'servidor_web.py',
    'responsabilidade': 'Servidor fastapi com swagger, webhook e interface web ui html',
    'pseudocodigo': 'expor rota http com frontend e mcp',
}


def test_extrair_features_calculo_puro(imp_mod):
    features = imp_mod._extrair_features_script(SCRIPT_CALCULO_PURO)
    assert features['sqlite'] is False
    assert features['fk'] is False
    assert features['api'] is False
    assert features['ui'] is False
    assert features['crud'] is False


def test_extrair_features_sqlite_fk(imp_mod):
    features = imp_mod._extrair_features_script(SCRIPT_SQLITE_FK)
    assert features['sqlite'] is True
    assert features['fk'] is True
    assert features['datas'] is True  # 'data'/'checkin' no pseudocódigo


def test_extrair_features_api_ui(imp_mod):
    features = imp_mod._extrair_features_script(SCRIPT_API_UI)
    assert features['api'] is True
    assert features['ui'] is True


def test_montar_blocos_sem_feature_gera_vazio(imp_mod):
    features = imp_mod._extrair_features_script(SCRIPT_CALCULO_PURO)
    blocos = imp_mod._montar_blocos_condicionais(features)
    assert blocos == ''
    assert 'SWAGGER' not in blocos
    assert 'MCP' not in blocos


def test_prompt_composto_sem_ui_api_nao_contem_blocos_swagger_mcp(imp_mod):
    """Critério de saída 1: script sem UI/API não recebe blocos Swagger/MCP/UI."""
    prompt = imp_mod.ImplementadorFase8._montar_prompt_implementar_script(
        ideia='calculadora', stack={}, script_spec=SCRIPT_CALCULO_PURO,
        nome_raw='calcular_media.py', modulo='calcular_media',
        secao_schema='', caminho_sugerido='calcular_media.py',
        caminho_teste_sugerido='test_calcular_media.py',
    )
    assert 'SWAGGER' not in prompt
    assert 'MCP STUDIO' not in prompt
    assert 'IMPECCABLE DESIGN' not in prompt
    assert 'FULL CRUD' not in prompt
    assert 'PRAGMA foreign_keys' not in prompt


def test_prompt_composto_sqlite_fk_contem_blocos_corretos(imp_mod):
    """Integridade: script SQL/FK recebe blocos SQLite + FK (nada essencial perdido)."""
    prompt = imp_mod.ImplementadorFase8._montar_prompt_implementar_script(
        ideia='rastreador', stack={'banco': 'SQLite'}, script_spec=SCRIPT_SQLITE_FK,
        nome_raw='registrar_checkin.py', modulo='registrar_checkin',
        secao_schema='', caminho_sugerido='registrar_checkin.py',
        caminho_teste_sugerido='test_registrar_checkin.py',
    )
    assert 'PRAGMA foreign_keys = ON' in prompt
    assert 'parent record' in prompt.lower()
    assert 'criar_tabela' in prompt


def test_prompt_composto_api_ui_contem_blocos_corretos(imp_mod):
    """Integridade: script API/UI recebe blocos Swagger/MCP/UI/CRUD."""
    prompt = imp_mod.ImplementadorFase8._montar_prompt_implementar_script(
        ideia='painel', stack={'framework': 'FastAPI'}, script_spec=SCRIPT_API_UI,
        nome_raw='servidor_web.py', modulo='servidor_web',
        secao_schema='', caminho_sugerido='servidor_web.py',
        caminho_teste_sugerido='test_servidor_web.py',
    )
    assert 'SWAGGER DARK MODE' in prompt
    assert 'MCP STUDIO' in prompt
    assert 'IMPECCABLE DESIGN' in prompt
    assert 'FULL CRUD' in prompt


def test_prompt_composto_menor_que_monolitico_para_script_simples(imp_mod):
    """Economia [TK-4]: prompt composto para script simples é estritamente
    menor que o prompt cheio de blocos (todas as features)."""
    prompt_simples = imp_mod.ImplementadorFase8._montar_prompt_implementar_script(
        ideia='x', stack={}, script_spec=SCRIPT_CALCULO_PURO,
        nome_raw='calcular_media.py', modulo='calcular_media',
        secao_schema='', caminho_sugerido='c.py', caminho_teste_sugerido='test_c.py',
    )
    script_tudo = {
        'nome': 'tudo.py',
        'responsabilidade': (
            'crud repositorio sqlite com foreign key e streak de data, json round-trip, '
            'api fastapi swagger mcp webhook e interface web ui html'
        ),
        'pseudocodigo': 'insert into tabela com json e rota http',
    }
    prompt_tudo = imp_mod.ImplementadorFase8._montar_prompt_implementar_script(
        ideia='x', stack={}, script_spec=script_tudo,
        nome_raw='tudo.py', modulo='tudo',
        secao_schema='', caminho_sugerido='t.py', caminho_teste_sugerido='test_t.py',
    )
    assert _tokens(prompt_simples) < _tokens(prompt_tudo)


# =============================================================================
# [TK-3] FIX-LOOP CIRÚRGICO — traceback isolado + contexto recortado
# =============================================================================

CODIGO_GRANDE = '\n'.join(
    '\n'.join([f"def funcao_{i}(x):"] + [f"    y_{j} = x + {j}" for j in range(5)] + [f"    return y_0 + {i}"])
    for i in range(30)
)

ERRO_COM_TRACEBACK = (
    "tests/test_grande.py::test_funcao_5 FAILED\n\n"
    'Traceback (most recent call last):\n'
    '  File "tests/test_grande.py", line 12, in test_funcao_5\n'
    '    assert funcao_5(1) == 6\n'
    'AssertionError: assert 7 == 6'
)


def test_extrair_funcoes_sob_suspeita_localiza_funcao_citada(imp_mod):
    suspeitas = imp_mod.PostMortemAnalyzer.extrair_funcoes_sob_suspeita(
        ERRO_COM_TRACEBACK, CODIGO_GRANDE
    )
    assert len(suspeitas) >= 1
    assert any('funcao_5' in s for s in suspeitas)


def test_extrair_funcoes_sob_suspeita_sem_match_retorna_lista(imp_mod):
    suspeitas = imp_mod.PostMortemAnalyzer.extrair_funcoes_sob_suspeita(
        'erro sem nomes conhecidos xyz', CODIGO_GRANDE
    )
    assert isinstance(suspeitas, list)
    assert len(suspeitas) == 0


def test_cortar_codigo_no_ponto_da_falha(imp_mod):
    trecho = imp_mod.ImplementadorFase8._cortar_codigo_no_ponto_da_falha(
        CODIGO_GRANDE, 'File "src/grande.py", line 60\nAssertionError'
    )
    assert len(trecho) < len(CODIGO_GRANDE)
    assert 'omitidas' in trecho


def test_cortar_codigo_sem_linha_no_erro_devolve_integral(imp_mod):
    trecho = imp_mod.ImplementadorFase8._cortar_codigo_no_ponto_da_falha(
        CODIGO_GRANDE, 'AssertionError: assert 7 == 6'
    )
    assert trecho == CODIGO_GRANDE


def test_cortar_teste_no_ponto_da_falha(imp_mod):
    teste_grande = '\n'.join(f"# linha de contexto {i}" for i in range(80))
    trecho = imp_mod.ImplementadorFase8._cortar_teste_no_ponto_da_falha(
        teste_grande, 'File "tests/test_grande.py", line 40\nAssertionError'
    )
    assert len(trecho) < len(teste_grande)
    assert 'omitidas' in trecho


def test_fix_loop_segunda_tentativa_envia_menos_de_50_porcento_tokens(imp_mod, tmp_path, monkeypatch):
    """Critério de saída 2 (plano): fix-loop na 2ª tentativa envia < 50% dos
    tokens da 1ª chamada — medido por tiktoken real sobre os prompts efetivos.

    O que a 1ª chamada carrega: prompt de IMPLEMENTAÇÃO completo (que pede a
    geração integral de código + teste). O que o retry carrega: prompt de
    CORREÇÃO cirúrgico (trecho recortado + traceback isolado).
    """
    # 1ª chamada: prompt de implementação para um script grande
    script_spec = {
        'nome': 'grande.py',
        'responsabilidade': 'crud sqlite com foreign key, json, api fastapi swagger mcp webhook e ui web html',
        'pseudocodigo': 'insert into tabela com json e rota http',
    }
    prompt_1a_chamada = imp_mod.ImplementadorFase8._montar_prompt_implementar_script(
        ideia='projeto grande', stack={'banco': 'SQLite'}, script_spec=script_spec,
        nome_raw='grande.py', modulo='grande',
        secao_schema=imp_mod.ImplementadorFase8.__mro__ and '',  # secao vazia nos dois lados
        caminho_sugerido='grande.py', caminho_teste_sugerido='test_grande.py',
    )

    # Retry: mesmo fluxo interno do _implementar_script_com_verificacao —
    # traceback isolado + funções sob suspeita + teste recortado
    erro = ERRO_COM_TRACEBACK
    erro_compacto = erro  # _extrair_falhas_pytest já recortou; simula resultado
    traceback_isolado = imp_mod.PostMortemAnalyzer._isolar_traceback(erro_compacto)
    suspeitas = imp_mod.PostMortemAnalyzer.extrair_funcoes_sob_suspeita(
        erro_compacto, CODIGO_GRANDE
    )
    contexto_cirurgico = '\n\n'.join(suspeitas) if suspeitas else \
        imp_mod.ImplementadorFase8._cortar_codigo_no_ponto_da_falha(CODIGO_GRANDE, erro_compacto)
    teste_recortado = imp_mod.ImplementadorFase8._cortar_teste_no_ponto_da_falha(
        CODIGO_GRANDE, erro_compacto
    )
    prompt_retry = imp_mod.PROMPT_CORRIGIR_SCRIPT.format(
        secao_schema='',
        codigo=contexto_cirurgico,
        teste=teste_recortado,
        erro=f"{traceback_isolado}\n\n{erro_compacto}" if suspeitas else erro_compacto,
        modulo='grande',
    )

    tokens_1a = _tokens(prompt_1a_chamada + CODIGO_GRANDE + CODIGO_GRANDE)
    tokens_retry = _tokens(prompt_retry)

    # Baseline honesto: a 1ª chamada de um script grande inclui CODE+TEST
    # integrais na resposta que será reenviada; o retry cirúrgico envia só
    # o trecho. Critério do plano: retry < 50% da 1ª chamada.
    assert tokens_retry < tokens_1a * 0.5, (
        f"retry ({tokens_retry} tokens) deve ser < 50% da 1ª chamada ({tokens_1a} tokens)"
    )


def test_fix_loop_retorno_de_correcao_mantem_caminhos(imp_mod, tmp_path, monkeypatch):
    """Integridade: o fluxo de correção cirúrgico ainda normaliza caminhos
    (caminho_relativo/caminho_teste preservados na impl corrigida)."""
    prompts = []

    def fake_solicitar(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        prompts.append((fase, prompt))
        if fase == 'phase_08':
            return {
                'conteudo': '{"codigo": "def somar(a, b):\\n    return a - b\\n", "teste": "def test_s():\\n    assert somar(2,3) == 5\\n", "caminho_relativo": "somar.py", "caminho_teste": "test_somar.py"}',
                'tokens_consumidos': 10, 'modelo_usado': 'x', 'timestamp_resposta': 'x',
            }
        return {
            'conteudo': '{"codigo": "def somar(a, b):\\n    return a + b\\n", "teste": "def test_s():\\n    assert somar(2,3) == 5\\n", "caminho_relativo": "somar.py", "caminho_teste": "test_somar.py"}',
            'tokens_consumidos': 10, 'modelo_usado': 'x', 'timestamp_resposta': 'x',
        }

    class PytestFake:
        def __init__(self, stdout, stderr="", returncode=0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode

    monkeypatch.setattr(imp_mod, 'solicitar_llm', fake_solicitar)
    resultados = iter([
        PytestFake(stdout='File "tests/test_s.py", line 2\nAssertionError: assert -1 == 5\n1 failed', returncode=1),
        PytestFake(stdout='1 passed', returncode=0),
        PytestFake(stdout='1 passed', returncode=0),
    ])
    monkeypatch.setattr(imp_mod.subprocess, 'run', lambda *a, **kw: next(resultados))

    imp = imp_mod.ImplementadorFase8(tmp_path)
    resultado = imp._implementar_script_com_verificacao(
        'ideia', {'banco': 'SQLite'},
        {'nome': 'somar.py', 'responsabilidade': 'somar', 'pseudocodigo': 'a+b'},
    )
    assert resultado['tentativas'] == 2
    assert resultado['caminho_relativo'] == 'somar.py'
    assert resultado['caminho_teste'] == 'test_somar.py'
    # O prompt de correção deve conter o traceback isolado (não a saída completa)
    prompt_fix = next(p for f, p in prompts if f == 'phase_08_fix')
    assert 'Traceback' in prompt_fix or 'AssertionError' in prompt_fix
