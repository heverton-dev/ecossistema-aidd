# -*- coding: utf-8 -*-
"""
Testes abrangentes da Sprint 06: Micro-Tasks AST + Result Monad + PostMortem.

Cobre:
- Result Monad (Ok/Err, unwrap, map, flat_map, encadeamento)
- MicroTask dataclass e decomposição AST
- PostMortemAnalyzer (5-Porquês, isolamento de traceback, classificação)
- Integração com ImplementadorFase8 (_chamar_llm_result, auto-cura)
- Pipeline completo com micro-tasks
"""

import json
import sys
import ast
from pathlib import Path

import pytest


# =============================================================================
# FIXTURES E HELPERS
# =============================================================================

def resposta_llm(conteudo_dict, tokens=100):
    return {
        'conteudo': json.dumps(conteudo_dict, ensure_ascii=False),
        'tokens_consumidos': tokens,
        'modelo_usado': 'teste',
        'timestamp_resposta': '2026-08-30T00:00:00Z',
    }


IMPL_VALIDA = {
    'codigo': 'def somar(a, b):\n    return a + b\n',
    'teste': 'from pacote.somar import somar\n\ndef test_somar():\n    assert somar(2, 3) == 5\n',
    'caminho_relativo': 'pacote/somar.py',
    'caminho_teste': 'test_somar.py',
}

IMPL_MULTI_FUNCOES = {
    'codigo': (
        'def calcular_soma(a, b):\n'
        '    return a + b\n'
        '\n'
        'def calcular_produto(a, b):\n'
        '    return a * b\n'
        '\n'
        'def validar_positivo(n):\n'
        '    if n <= 0:\n'
        '        raise ValueError("deve ser positivo")\n'
        '    return True\n'
    ),
    'teste': (
        'from pacote.calc import calcular_soma, calcular_produto, validar_positivo\n'
        '\n'
        'def test_soma():\n'
        '    assert calcular_soma(2, 3) == 5\n'
        '\n'
        'def test_produto():\n'
        '    assert calcular_produto(3, 4) == 12\n'
        '\n'
        'def test_positivo():\n'
        '    assert validar_positivo(5) is True\n'
    ),
    'caminho_relativo': 'pacote/calc.py',
    'caminho_teste': 'test_calc.py',
}

IMPL_COM_CLASSE = {
    'codigo': (
        'class Calculadora:\n'
        '    def __init__(self):\n'
        '        self.historico = []\n'
        '\n'
        '    def somar(self, a, b):\n'
        '        resultado = a + b\n'
        '        self.historico.append(resultado)\n'
        '        return resultado\n'
        '\n'
        '    def obter_ultimo(self):\n'
        '        return self.historico[-1] if self.historico else None\n'
    ),
    'teste': (
        'from pacote.calc import Calculadora\n'
        '\n'
        'def test_somar():\n'
        '    c = Calculadora()\n'
        '    assert c.somar(2, 3) == 5\n'
    ),
    'caminho_relativo': 'pacote/calc.py',
    'caminho_teste': 'test_calc.py',
}

DESIGN_COM_1_SCRIPT = {
    'design': {
        'scripts': [
            {'nome': 'somar.py', 'responsabilidade': 'somar dois numeros', 'pseudocodigo': '1. retornar a+b'}
        ]
    }
}

ANALISE_COM_STACK = {
    'stack_recomendado': {'linguagem': 'Python 3.11+', 'framework': 'None', 'banco': 'None'}
}


class PytestFake:
    """Simula subprocess.CompletedProcess para as chamadas de pytest real."""
    def __init__(self, passaram=1, falharam=0, returncode=0, extra_saida=''):
        saida = f"{passaram} passed" if falharam == 0 else f"{passaram} passed, {falharam} failed"
        self.stdout = f"{extra_saida}\n{saida}\n" if extra_saida else f"{saida}\n"
        self.stderr = ''
        self.returncode = returncode


# =============================================================================
# RESULT MONAD
# =============================================================================

class TestResultMonad:
    """Testes do Result Monad — Ok/Err, unwrap, map, flat_map."""

    def test_ok_cria_result_sucesso(self, implementador_08):
        r = implementador_08.Result.ok(42)
        assert r.is_ok() is True
        assert r.is_err() is False
        assert r.unwrap() == 42

    def test_fail_cria_result_erro(self, implementador_08):
        r = implementador_08.Result.fail("erro qualquer")
        assert r.is_ok() is False
        assert r.is_err() is True
        assert r._error == "erro qualquer"

    def test_unwrap_em_err_levanta_runtime_error(self, implementador_08):
        r = implementador_08.Result.fail("falhou")
        with pytest.raises(RuntimeError, match="Called unwrap.*Err"):
            r.unwrap()

    def test_unwrap_or_retorna_default_em_err(self, implementador_08):
        r = implementador_08.Result.fail("erro")
        assert r.unwrap_or(99) == 99

    def test_unwrap_or_retorna_valor_em_ok(self, implementador_08):
        r = implementador_08.Result.ok(42)
        assert r.unwrap_or(99) == 42

    def test_map_transforma_valor_ok(self, implementador_08):
        r = implementador_08.Result.ok(10)
        r2 = r.map(lambda x: x * 2)
        assert r2.is_ok() is True
        assert r2.unwrap() == 20

    def test_map_propaga_erro(self, implementador_08):
        r = implementador_08.Result.fail("erro")
        r2 = r.map(lambda x: x * 2)
        assert r2.is_err() is True
        assert r2._error == "erro"

    def test_map_com_excecao_retorna_err(self, implementador_08):
        r = implementador_08.Result.ok("abc")
        r2 = r.map(lambda x: int(x))  # ValueError
        assert r2.is_err() is True
        assert "invalid literal" in r2._error

    def test_flat_map_encadeia_result(self, implementador_08):
        r = implementador_08.Result.ok(10)
        r2 = r.flat_map(lambda x: implementador_08.Result.ok(x + 5))
        assert r2.is_ok() is True
        assert r2.unwrap() == 15

    def test_flat_map_propaga_erro(self, implementador_08):
        r = implementador_08.Result.fail("erro original")
        r2 = r.flat_map(lambda x: implementador_08.Result.ok(x + 5))
        assert r2.is_err() is True
        assert r2._error == "erro original"

    def test_flat_map_com_excecao_retorna_err(self, implementador_08):
        r = implementador_08.Result.ok(10)
        def fn_que_falha(x):
            raise ValueError("boom")
        r2 = r.flat_map(fn_que_falha)
        assert r2.is_err() is True
        assert "boom" in r2._error

    def test_ok_sem_valor(self, implementador_08):
        r = implementador_08.Result.ok()
        assert r.is_ok() is True
        assert r.unwrap() is None

    def test_repr_ok(self, implementador_08):
        r = implementador_08.Result.ok(42)
        assert "Ok(42)" in repr(r)

    def test_repr_err(self, implementador_08):
        r = implementador_08.Result.fail("boom")
        assert "Err('boom')" in repr(r)

    def test_eq_ok_iguais(self, implementador_08):
        assert implementador_08.Result.ok(1) == implementador_08.Result.ok(1)

    def test_eq_ok_diferentes(self, implementador_08):
        assert implementador_08.Result.ok(1) != implementador_08.Result.ok(2)

    def test_eq_err_iguais(self, implementador_08):
        assert implementador_08.Result.fail("a") == implementador_08.Result.fail("a")

    def test_eq_err_diferentes(self, implementador_08):
        assert implementador_08.Result.fail("a") != implementador_08.Result.fail("b")

    def test_eq_ok_vs_err(self, implementador_08):
        assert implementador_08.Result.ok(1) != implementador_08.Result.fail("1")

    def test_eq_com_tipo_diferente(self, implementador_08):
        assert implementador_08.Result.ok(1).__eq__("not a result") is NotImplemented

    def test_encadeamento_pipeline(self, implementador_08):
        """Simula pipeline: parse → validar → transformar."""
        def parse_json(s):
            return json.loads(s)

        def validar(d):
            if 'nome' not in d:
                return implementador_08.Result.fail("campo 'nome' obrigatório")
            return implementador_08.Result.ok(d)

        def transformar(d):
            return {'nome_upper': d['nome'].upper()}

        # Pipeline com sucesso
        r = (implementador_08.Result.ok('{"nome": "teste"}')
             .map(parse_json)
             .flat_map(validar)
             .map(transformar))
        assert r.is_ok() is True
        assert r.unwrap()['nome_upper'] == 'TESTE'

        # Pipeline com falha na validação
        r2 = (implementador_08.Result.ok('{}')
              .map(parse_json)
              .flat_map(validar)
              .map(transformar))
        assert r2.is_err() is True
        assert "nome" in r2._error


# =============================================================================
# MICRO-TASK AST
# =============================================================================

class TestMicroTaskAST:
    """Testes de decomposição de script em MicroTasks via AST."""

    def test_microtask_dataclass(self, implementador_08):
        mt = implementador_08.MicroTask(
            nome_funcao='somar',
            assinatura='somar(a, b)',
            responsabilidade='somar dois números'
        )
        assert mt.nome_funcao == 'somar'
        assert mt.assinatura == 'somar(a, b)'
        assert mt.dependencias == []
        assert mt.codigo_gerado is None
        assert mt.tentativas == 0
        assert mt.falhou is False

    def test_decompor_funcoes_simples(self, implementador_08):
        microtasks = implementador_08.decompor_script_em_microtasks(
            IMPL_MULTI_FUNCOES['codigo'], IMPL_MULTI_FUNCOES['teste']
        )
        nomes = [mt.nome_funcao for mt in microtasks]
        assert 'calcular_soma' in nomes
        assert 'calcular_produto' in nomes
        assert 'validar_positivo' in nomes
        assert len(microtasks) == 3

    def test_decompor_com_classe(self, implementador_08):
        microtasks = implementador_08.decompor_script_em_microtasks(
            IMPL_COM_CLASSE['codigo'], IMPL_COM_CLASSE['teste']
        )
        nomes = [mt.nome_funcao for mt in microtasks]
        assert 'Calculadora.somar' in nomes
        assert 'Calculadora.obter_ultimo' in nomes
        # __init__ deve ser excluído
        assert not any('__init__' in n for n in nomes)

    def test_decompor_funcao_unica(self, implementador_08):
        microtasks = implementador_08.decompor_script_em_microtasks(
            IMPL_VALIDA['codigo'], IMPL_VALIDA['teste']
        )
        assert len(microtasks) == 1
        assert microtasks[0].nome_funcao == 'somar'
        assert microtasks[0].assinatura == 'somar(a, b)'

    def test_decompor_codigo_vazio(self, implementador_08):
        microtasks = implementador_08.decompor_script_em_microtasks('', '')
        assert microtasks == []

    def test_decompor_syntax_error(self, implementador_08):
        microtasks = implementador_08.decompor_script_em_microtasks(
            'def f(:\n    pass', ''
        )
        assert microtasks == []

    def test_decompor_apenas_classes_sem_metodos(self, implementador_08):
        microtasks = implementador_08.decompor_script_em_microtasks(
            'class Vazio:\n    pass\n', ''
        )
        assert microtasks == []

    def test_decompor_ignora_metodos_magicos(self, implementador_08):
        codigo = (
            'class Repo:\n'
            '    def __init__(self):\n'
            '        self.data = {}\n'
            '    def __str__(self):\n'
            '        return "Repo"\n'
            '    def salvar(self, item):\n'
            '        self.data[item] = True\n'
        )
        microtasks = implementador_08.decompor_script_em_microtasks(codigo, '')
        nomes = [mt.nome_funcao for mt in microtasks]
        assert 'Repo.salvar' in nomes
        assert len(microtasks) == 1

    def test_decompor_assinatura_sem_args(self, implementador_08):
        codigo = 'def obter_total():\n    return 42\n'
        microtasks = implementador_08.decompor_script_em_microtasks(codigo, '')
        assert microtasks[0].assinatura == 'obter_total()'

    def test_decompor_assinatura_com_args(self, implementador_08):
        codigo = 'def filtrar(items, key, reverse=False):\n    pass\n'
        microtasks = implementador_08.decompor_script_em_microtasks(codigo, '')
        assert 'items' in microtasks[0].assinatura
        assert 'key' in microtasks[0].assinatura


# =============================================================================
# POST-MORTEM ANALYZER
# =============================================================================

class TestPostMortemAnalyzer:
    """Testes do PostMortemAnalyzer — 5-Porquês, classificação, sugestão."""

    def test_analisar_falha_assertion(self, implementador_08):
        saida_pytest = (
            "FAILED test_somar.py::test_somar - AssertionError: assert 3 == 5\n"
            "  File \"tests/test_somar.py\", line 5, in test_somar\n"
            "    assert somar(2, 3) == 5\n"
            "AssertionError: assert 3 == 5\n"
        )
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            saida_pytest, IMPL_VALIDA['codigo'], 'somar'
        )
        assert analise['tipo_falha'] == 'assertion_failure'
        assert len(analise['porques']) == 5
        assert 'somar' in analise['funcao_afetada']
        assert analise['correcao_sugerida'] != ''

    def test_analisar_falha_import_error(self, implementador_08):
        saida_pytest = (
            "ERROR collecting tests/test_x.py\n"
            "ModuleNotFoundError: No module named 'pacote'\n"
        )
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            saida_pytest, 'import pacote\n', 'x'
        )
        assert analise['tipo_falha'] == 'import_error'
        assert 'src/' in analise['correcao_sugerida'] or '__init__' in analise['correcao_sugerida']

    def test_analisar_falha_type_error(self, implementador_08):
        saida_pytest = "TypeError: unsupported operand type(s)\n"
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            saida_pytest, '', ''
        )
        assert analise['tipo_falha'] == 'type_error'

    def test_analisar_falha_syntax_error(self, implementador_08):
        saida_pytest = "SyntaxError: invalid syntax\n"
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            saida_pytest, '', ''
        )
        assert analise['tipo_falha'] == 'syntax_error'

    def test_analisar_falha_attribute_error(self, implementador_08):
        saida_pytest = "AttributeError: 'dict' object has no attribute 'append'\n"
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            saida_pytest, '', ''
        )
        assert analise['tipo_falha'] == 'attribute_error'

    def test_analisar_falha_value_error(self, implementador_08):
        saida_pytest = "ValueError: invalid literal for int()\n"
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            saida_pytest, '', ''
        )
        assert analise['tipo_falha'] == 'value_error'

    def test_analisar_falha_key_error(self, implementador_08):
        saida_pytest = "KeyError: 'nome'\n"
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            saida_pytest, '', ''
        )
        assert analise['tipo_falha'] == 'key_error'

    def test_analisar_falha_index_error(self, implementador_08):
        saida_pytest = "IndexError: list index out of range\n"
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            saida_pytest, '', ''
        )
        assert analise['tipo_falha'] == 'index_error'

    def test_analisar_falha_desconhecida(self, implementador_08):
        saida_pytest = "SomethingWentWrong: totally unexpected\n"
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            saida_pytest, '', ''
        )
        assert analise['tipo_falha'] == 'unknown'

    def test_isolar_traceback(self, implementador_08):
        saida = (
            "some setup output\n"
            "Traceback (most recent call last):\n"
            "  File \"test_x.py\", line 3, in test_x\n"
            "    assert 1 == 2\n"
            "AssertionError\n"
            "\n"
            "=== 1 failed ===\n"
        )
        tb = implementador_08.PostMortemAnalyzer._isolar_traceback(saida)
        assert 'Traceback' in tb
        assert 'assert 1 == 2' in tb

    def test_isolar_traceback_vazio(self, implementador_08):
        tb = implementador_08.PostMortemAnalyzer._isolar_traceback("tudo ok\n")
        # Fallback: últimos 500 chars
        assert len(tb) <= 500

    def test_extrair_causa_raiz(self, implementador_08):
        saida = "line 5\nAssertionError: assert 3 == 5\n"
        causa = implementador_08.PostMortemAnalyzer._extrair_causa_raiz(saida)
        assert 'AssertionError' in causa or 'assert' in causa

    def test_localizar_erro_com_file_line(self, implementador_08):
        saida = '  File "tests/test_somar.py", line 5, in test_somar\n'
        loc = implementador_08.PostMortemAnalyzer._localizar_erro(saida, '')
        assert 'test_somar.py' in loc
        assert '5' in loc

    def test_localizar_erro_com_test_id(self, implementador_08):
        saida = "FAILED tests/test_calc.py::test_soma\n"
        loc = implementador_08.PostMortemAnalyzer._localizar_erro(saida, '')
        assert 'test_calc.py' in loc

    def test_localizar_erro_fallback(self, implementador_08):
        loc = implementador_08.PostMortemAnalyzer._localizar_erro("nada aqui", '')
        assert 'não identificada' in loc

    def test_porques_tem_5_elementos(self, implementador_08):
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            "AssertionError: x\n", '', ''
        )
        assert len(analise['porques']) == 5

    def test_relatorio_formato_string(self, implementador_08):
        analise = implementador_08.PostMortemAnalyzer.analisar_falha(
            "ValueError: bad\n", '', ''
        )
        assert isinstance(analise['relatorio'], str)
        assert '|' in analise['relatorio']

    def test_correcao_sugerida_nao_vazia(self, implementador_08):
        for tipo in ['assertion_failure', 'syntax_error', 'import_error',
                      'type_error', 'attribute_error', 'value_error',
                      'key_error', 'index_error', 'unknown']:
            saida = f"{tipo.replace('_', ' ').title()}: test\n"
            analise = implementador_08.PostMortemAnalyzer.analisar_falha(saida, '', '')
            assert analise['correcao_sugerida'] != ''


# =============================================================================
# RESULT MONAD — CHAMAR LLM
# =============================================================================

class TestChamarLLMResult:
    """Testes do _chamar_llm_result — Result Monad aplicado a chamadas LLM."""

    def test_chamar_llm_sucesso(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(
            implementador_08, 'solicitar_llm',
            lambda **kw: resposta_llm({'codigo': 'x', 'teste': 'y'}, tokens=50)
        )
        imp = implementador_08.ImplementadorFase8(tmp_path)
        result = imp._chamar_llm_result("prompt", "ctx", "fase")
        assert result.is_ok() is True
        assert result.unwrap()['codigo'] == 'x'
        assert imp._tokens_totais == 50

    def test_chamar_llm_retorna_none(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: None)
        imp = implementador_08.ImplementadorFase8(tmp_path)
        result = imp._chamar_llm_result("prompt", "ctx", "fase")
        assert result.is_err() is True
        assert "não respondeu" in result._error

    def test_chamar_llm_excecao_config(self, implementador_08, tmp_path, monkeypatch):
        def levanta(*a, **kw):
            raise implementador_08.LLMNaoConfiguradoException("msg", "det")
        monkeypatch.setattr(implementador_08, 'solicitar_llm', levanta)
        imp = implementador_08.ImplementadorFase8(tmp_path)
        result = imp._chamar_llm_result("prompt", "ctx", "fase")
        assert result.is_err() is True
        assert "msg" in result._error

    def test_chamar_llm_json_invalido(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(
            implementador_08, 'solicitar_llm',
            lambda **kw: {'conteudo': 'nao json', 'tokens_consumidos': 10,
                          'modelo_usado': 'x', 'timestamp_resposta': 'x'}
        )
        imp = implementador_08.ImplementadorFase8(tmp_path)
        result = imp._chamar_llm_result("prompt", "ctx", "fase")
        assert result.is_err() is True

    def test_chamar_llm_soma_tokens(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(
            implementador_08, 'solicitar_llm',
            lambda **kw: resposta_llm({'ok': True}, tokens=100)
        )
        imp = implementador_08.ImplementadorFase8(tmp_path)
        imp._chamar_llm_result("p1", "c1", "f1")
        imp._chamar_llm_result("p2", "c2", "f2")
        assert imp._tokens_totais == 200


# =============================================================================
# VALIDAR E ESCREVER RESULT
# =============================================================================

class TestValidarEEscreverResult:
    """Testes do _validar_e_escrever_result."""

    def test_validacao_ok(self, implementador_08, tmp_path):
        imp = implementador_08.ImplementadorFase8(tmp_path)
        result = imp._validar_e_escrever_result(IMPL_VALIDA, 'somar')
        assert result.is_ok() is True
        assert (tmp_path / 'src' / 'pacote' / 'somar.py').exists()
        assert (tmp_path / 'tests' / 'test_somar.py').exists()

    def test_validacao_falha_contrato(self, implementador_08, tmp_path):
        impl_quebrado = {
            'codigo': 'def outra():\n    pass\n',
            'teste': 'from pacote.x import funcao_inexistente\ndef test_x():\n    funcao_inexistente()\n',
            'caminho_relativo': 'pacote/x.py',
            'caminho_teste': 'test_x.py',
        }
        imp = implementador_08.ImplementadorFase8(tmp_path)
        result = imp._validar_e_escrever_result(impl_quebrado, 'x')
        assert result.is_err() is True
        assert 'CONTRATO' in result._error or 'funcao_inexistente' in result._error


# =============================================================================
# DECOMPOR E IMPLEMENTAR MICRO-TASKS
# =============================================================================

class TestDecomporEImplementarMicroTasks:
    """Testes de integração: decomposição + implementação de micro-tasks."""

    def test_microtasks_sucesso_primeira_tentativa(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA))
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

        imp = implementador_08.ImplementadorFase8(tmp_path)
        imp._escrever_implementacao(IMPL_VALIDA)
        result = imp.decompor_e_implementar_microtasks(
            'ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0], IMPL_VALIDA
        )
        assert result.is_ok() is True

    def test_microtasks_codigo_sem_funcoes(self, implementador_08, tmp_path, monkeypatch):
        """Script sem funções definíveis — fallback para monolítico."""
        impl_sem_funcoes = {
            'codigo': 'x = 42\nprint(x)\n',
            'teste': 'def test_x():\n    assert True\n',
            'caminho_relativo': 'script.py',
            'caminho_teste': 'test_script.py',
        }
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

        imp = implementador_08.ImplementadorFase8(tmp_path)
        imp._escrever_implementacao(impl_sem_funcoes)
        result = imp.decompor_e_implementar_microtasks(
            'ideia', {}, {}, impl_sem_funcoes
        )
        assert result.is_ok() is True

    def test_microtasks_falha_ativa_auto_cura(self, implementador_08, tmp_path, monkeypatch):
        """Se teste falha, auto-cura é ativada."""
        chamadas = []
        def fake_llm(**kw):
            chamadas.append(kw.get('fase', ''))
            return resposta_llm(IMPL_VALIDA)

        monkeypatch.setattr(implementador_08, 'solicitar_llm', fake_llm)
        # Primeira chamada: falha. Depois: sucesso (auto-cura corrige).
        resultados = iter([
            PytestFake(passaram=0, falharam=1),  # falha inicial
            PytestFake(passaram=1, falharam=0),  # auto-cura sucesso
        ])
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: next(resultados))

        imp = implementador_08.ImplementadorFase8(tmp_path)
        imp._escrever_implementacao(IMPL_VALIDA)
        result = imp.decompor_e_implementar_microtasks(
            'ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0], IMPL_VALIDA
        )
        assert result.is_ok() is True
        assert 'phase_08_autocura' in chamadas


# =============================================================================
# AUTO-CURA MICRO-TASKS
# =============================================================================

class TestAutoCuraMicroTasks:
    """Testes do loop de auto-cura com PostMortem."""

    def test_auto_cura_sucesso(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA))
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

        imp = implementador_08.ImplementadorFase8(tmp_path)
        imp._escrever_implementacao(IMPL_VALIDA)
        microtasks = implementador_08.decompor_script_em_microtasks(
            IMPL_VALIDA['codigo'], IMPL_VALIDA['teste']
        )
        resultado_falha = {
            'passaram': 0, 'falharam': 1, 'erros': 0, 'total': 1,
            'erro_coleta': False,
            'saida': 'FAILED test_somar.py::test_somar - AssertionError: assert 3 == 5\n',
        }
        result = imp._auto_cura_microtasks(
            'ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0],
            dict(IMPL_VALIDA), microtasks, resultado_falha
        )
        assert result.is_ok() is True

    def test_auto_cura_esgota_tentativas(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA))
        # Sempre falha
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=0, falharam=1))

        imp = implementador_08.ImplementadorFase8(tmp_path)
        imp._escrever_implementacao(IMPL_VALIDA)
        microtasks = implementador_08.decompor_script_em_microtasks(
            IMPL_VALIDA['codigo'], IMPL_VALIDA['teste']
        )
        resultado_falha = {
            'passaram': 0, 'falharam': 1, 'erros': 0, 'total': 1,
            'erro_coleta': False,
            'saida': 'FAILED - AssertionError\n',
        }
        result = imp._auto_cura_microtasks(
            'ideia', {}, {}, dict(IMPL_VALIDA), microtasks, resultado_falha
        )
        assert result.is_err() is True
        assert 'esgotou' in result._error or 'não convergiu' in result._error

    def test_auto_cura_llm_nao_responde(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: None)

        imp = implementador_08.ImplementadorFase8(tmp_path)
        microtasks = [implementador_08.MicroTask('f', 'f()', 'desc')]
        resultado_falha = {'saida': 'Error\n'}
        result = imp._auto_cura_microtasks(
            'ideia', {}, {}, dict(IMPL_VALIDA), microtasks, resultado_falha
        )
        assert result.is_err() is True

    def test_identificar_microtask_falha(self, implementador_08, tmp_path):
        imp = implementador_08.ImplementadorFase8(tmp_path)
        mt1 = implementador_08.MicroTask('somar', 'somar(a,b)', 'soma')
        mt2 = implementador_08.MicroTask('subtrair', 'subtrair(a,b)', 'subtração')
        analise = {'funcao_afetada': 'somar'}
        mt = imp._identificar_microtask_falha([mt1, mt2], analise)
        assert mt.nome_funcao == 'somar'

    def test_identificar_microtask_fallback(self, implementador_08, tmp_path):
        imp = implementador_08.ImplementadorFase8(tmp_path)
        mt1 = implementador_08.MicroTask('f1', 'f1()', 'desc')
        mt1.resultado_pytest = {'passaram': 1}
        mt2 = implementador_08.MicroTask('f2', 'f2()', 'desc')
        analise = {'funcao_afetada': 'nao_existe'}
        mt = imp._identificar_microtask_falha([mt1, mt2], analise)
        assert mt.nome_funcao == 'f2'  # primeira não testada

    def test_montar_prompt_auto_cura(self, implementador_08, tmp_path):
        imp = implementador_08.ImplementadorFase8(tmp_path)
        analise = {
            'porques': ['P1: erro', 'P2: local', 'P3: tipo', 'P4: padrão', 'P5: correção'],
            'traceback_isolado': 'Traceback...',
            'causa_raiz': 'AssertionError',
            'tipo_falha': 'assertion_failure',
            'correcao_sugerida': 'Corrigir lógica',
        }
        prompt = imp._montar_prompt_auto_cura('', 'modulo', IMPL_VALIDA, analise)
        assert 'PostMortem' in prompt
        assert '5-PORQUÊS' in prompt
        assert 'AssertionError' in prompt
        assert 'modulo' in prompt


# =============================================================================
# INTEGRAÇÃO: PIPELINE COMPLETO COM RESULT MONAD
# =============================================================================

class TestPipelineResultMonad:
    """Testes de integração: pipeline completo usando Result Monad."""

    def test_executar_sucesso_com_result_monad(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA, tokens=100))
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

        imp = implementador_08.ImplementadorFase8(tmp_path)
        index = imp.executar('ideia', ANALISE_COM_STACK, DESIGN_COM_1_SCRIPT)

        assert index is not None
        assert index['status'] == 'COMPLETO'
        assert index['tokens']['consumidos'] > 0

    def test_executar_llm_falha_retorna_none(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: None)
        imp = implementador_08.ImplementadorFase8(tmp_path)
        resultado = imp.executar('ideia', ANALISE_COM_STACK, DESIGN_COM_1_SCRIPT)
        assert resultado is None

    def test_implementar_script_usa_result_monad(self, implementador_08, tmp_path, monkeypatch):
        """Verifica que _implementar_script_com_verificacao usa Result internamente."""
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA))
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

        imp = implementador_08.ImplementadorFase8(tmp_path)
        resultado = imp._implementar_script_com_verificacao(
            'ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0]
        )
        assert resultado is not None
        assert resultado['tentativas'] == 1
        assert not resultado.get('falhou_apos_tentativas')

    def test_schema_compartilhado_usa_result_monad(self, implementador_08, tmp_path, monkeypatch):
        schema_sql = "CREATE TABLE t1 (id INTEGER PRIMARY KEY);"
        monkeypatch.setattr(
            implementador_08, 'solicitar_llm',
            lambda **kw: resposta_llm({'schema_sql': schema_sql, 'tabelas': ['t1']}, tokens=80)
        )
        imp = implementador_08.ImplementadorFase8(tmp_path)
        resultado = imp._gerar_schema_compartilhado('ideia', {'banco': 'SQLite'}, [])
        assert resultado == schema_sql

    def test_integracao_usa_result_monad(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(
            implementador_08, 'solicitar_llm',
            lambda **kw: resposta_llm({'teste': 'def test_x(): assert True', 'caminho_teste': 'test_integracao.py'}, tokens=50)
        )
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

        imp = implementador_08.ImplementadorFase8(tmp_path)
        gerou, res = imp._gerar_e_escrever_teste_integracao('ideia', {}, [IMPL_VALIDA])
        assert gerou is True
        assert res is not None


# =============================================================================
# BACKWARD COMPATIBILITY — Testes existentes ainda passam
# =============================================================================

class TestBackwardCompatibility:
    """Garante que a refatoração não quebra os testes existentes."""

    def test_gate_to_dict(self, implementador_08):
        gate = implementador_08.Gate('I1', 'descricao', True, 'detalhes')
        assert gate.to_dict() == {
            'gate_id': 'I1', 'descricao': 'descricao', 'status': 'PASSOU', 'detalhes': 'detalhes'
        }

    def test_implementar_script_sucesso_primeira_tentativa(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA))
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

        imp = implementador_08.ImplementadorFase8(tmp_path)
        resultado = imp._implementar_script_com_verificacao('ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0])

        assert resultado['tentativas'] == 1
        assert not resultado.get('falhou_apos_tentativas')

    def test_implementar_script_llm_nao_responde(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: None)
        imp = implementador_08.ImplementadorFase8(tmp_path)
        resultado = imp._implementar_script_com_verificacao('ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0])
        assert resultado is None

    def test_escrever_implementacao(self, implementador_08, tmp_path):
        imp = implementador_08.ImplementadorFase8(tmp_path)
        imp._escrever_implementacao(IMPL_VALIDA)
        assert (tmp_path / 'src' / 'pacote' / 'somar.py').exists()
        assert (tmp_path / 'tests' / 'test_somar.py').exists()

    def test_rodar_pytest_parseia_sucesso(self, implementador_08, tmp_path, monkeypatch):
        monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=3, falharam=0))
        imp = implementador_08.ImplementadorFase8(tmp_path)
        resultado = imp._rodar_pytest(None)
        assert resultado['passaram'] == 3
        assert resultado['erro_coleta'] is False

    def test_validar_contrato_ast(self, implementador_08):
        resultado = implementador_08.ImplementadorFase8._validar_contrato_ast(
            IMPL_VALIDA['codigo'], IMPL_VALIDA['teste']
        )
        assert resultado is None

    def test_normalizar_caminho_codigo(self, implementador_08):
        assert implementador_08.ImplementadorFase8._normalizar_caminho_codigo('src/x.py') == 'x.py'
        assert implementador_08.ImplementadorFase8._normalizar_caminho_codigo(None, 'y.py') == 'y.py'

    def test_extrair_falhas_pytest(self, implementador_08):
        saida = "PASSED test_a.py\nFAILED test_b.py::test_x - AssertionError\n=== 1 failed, 1 passed ==="
        falhas = implementador_08.ImplementadorFase8._extrair_falhas_pytest(saida)
        assert 'FAILED' in falhas
        assert 'PASSED test_a' not in falhas
