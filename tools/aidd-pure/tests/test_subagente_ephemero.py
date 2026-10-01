#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: Context-Purge Engine (Subagentes Efêmeros)
"""

import ast
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Adicionar diretório de fases ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'phases'))

from utils_subagente_ephemero import (
    ResultadoSubagente,
    MetricasPurge,
    SubagenteEphemero,
    ContextPurgeEngine,
    validar_ast_python,
    validar_json_estruturado,
    validar_codigo_com_campos_obrigatorios,
    validar_teste_pytest,
    construir_prompt_ephemero,
    prompt_codigo_ephemero,
    prompt_schema_ephemero,
    prompt_correcao_ephemero,
    prompt_integracao_ephemero,
)


# =============================================================================
# Testes: Validadores Mecânicos (Zero Token)
# =============================================================================

class TestValidadorAST:
    def test_codigo_valido(self):
        ok, msg = validar_ast_python("def foo(): return 42")
        assert ok is True
        assert "OK" in msg

    def test_codigo_vazio(self):
        ok, msg = validar_ast_python("")
        assert ok is False
        assert "vazio" in msg.lower()

    def test_codigo_none(self):
        ok, msg = validar_ast_python(None)
        assert ok is False

    def test_syntax_error(self):
        ok, msg = validar_ast_python("def foo(: return 42")
        assert ok is False
        assert "SyntaxError" in msg

    def test_codigo_complexo_valido(self):
        codigo = """
import os
from pathlib import Path

class MyClass:
    def __init__(self, x):
        self.x = x

    def method(self):
        return self.x * 2

def standalone():
    return MyClass(5).method()
"""
        ok, msg = validar_ast_python(codigo)
        assert ok is True

    def test_codigo_com_caracteres_especiais(self):
        ok, msg = validar_ast_python("x = 'olá mundo 🌍'")
        assert ok is True


class TestValidadorJSON:
    def test_json_valido_dict(self):
        ok, msg = validar_json_estruturado('{"chave": "valor"}')
        assert ok is True

    def test_json_com_code_fence(self):
        ok, msg = validar_json_estruturado('```json\n{"chave": "valor"}\n```')
        assert ok is True

    def test_json_invalido(self):
        ok, msg = validar_json_estruturado("isto não é json")
        assert ok is False

    def test_json_vazio(self):
        ok, msg = validar_json_estruturado("")
        assert ok is False


class TestValidadorCamposObrigatorios:
    def test_todos_campos_presentes(self):
        codigo = """
def criar_tabela(conn):
    pass

def listar_itens(conn):
    pass
"""
        ok, msg = validar_codigo_com_campos_obrigatorios(codigo, ['criar_tabela', 'listar_itens'])
        assert ok is True
        assert "2" in msg

    def test_campo_ausente(self):
        codigo = "def criar_tabela(conn): pass"
        ok, msg = validar_codigo_com_campos_obrigatorios(codigo, ['criar_tabela', 'listar_itens'])
        assert ok is False
        assert "listar_itens" in msg

    def test_codigo_vazio(self):
        ok, msg = validar_codigo_com_campos_obrigatorios("", ['foo'])
        assert ok is False

    def test_com_classe(self):
        codigo = """
class Servico:
    def criar(self): pass
    def listar(self): pass
"""
        ok, msg = validar_codigo_com_campos_obrigatorios(codigo, ['Servico'])
        assert ok is True


class TestValidadorPytest:
    def test_teste_valido(self):
        ok, msg = validar_teste_pytest("def test_foo(): assert True")
        assert ok is True
        assert "1" in msg

    def test_multiplos_testes(self):
        codigo = """
def test_a(): assert 1 == 1
def test_b(): assert 2 == 2
def test_c(): assert 3 == 3
"""
        ok, msg = validar_teste_pytest(codigo)
        assert ok is True
        assert "3" in msg

    def test_sem_funcao_teste(self):
        ok, msg = validar_teste_pytest("def helper(): pass")
        assert ok is False
        assert "test_*" in msg

    def test_vazio(self):
        ok, msg = validar_teste_pytest("")
        assert ok is False

    def test_syntax_error(self):
        ok, msg = validar_teste_pytest("def test_x(: pass")
        assert ok is False
        assert "SyntaxError" in msg


# =============================================================================
# Testes: MetricasPurge
# =============================================================================

class TestMetricasPurge:
    def test_inicializacao(self):
        m = MetricasPurge()
        assert m.total_subagentes_criados == 0
        assert m.total_tokens_consumidos == 0

    def test_registrar_sucesso(self):
        m = MetricasPurge()
        r = ResultadoSubagente(
            id='test1', sucesso=True, tokens_consumidos=100,
            contexto_purgado=True, duracao_segundos=1.5
        )
        m.registrar(r)
        assert m.total_subagentes_criados == 1
        assert m.total_subagentes_bem_sucedidos == 1
        assert m.total_tokens_consumidos == 100
        assert m.total_contextos_purgados == 1

    def test_registrar_falha(self):
        m = MetricasPurge()
        r = ResultadoSubagente(
            id='test2', sucesso=False, tokens_consumidos=50,
            contexto_purgado=True, duracao_segundos=0.5
        )
        m.registrar(r)
        assert m.total_subagentes_falharam == 1
        assert m.total_subagentes_bem_sucedidos == 0

    def test_to_dict(self):
        m = MetricasPurge()
        r = ResultadoSubagente(id='test', sucesso=True, tokens_consumidos=100, contexto_purgado=True)
        m.registrar(r)
        d = m.to_dict()
        assert d['total_subagentes_criados'] == 1
        assert d['taxa_sucesso'] == 100.0

    def test_taxa_sucesso_zero_divisao(self):
        m = MetricasPurge()
        assert m.to_dict()['taxa_sucesso'] == 0.0


# =============================================================================
# Testes: ResultadoSubagente
# =============================================================================

class TestResultadoSubagente:
    def test_to_dict(self):
        r = ResultadoSubagente(
            id='abc', sucesso=True, tokens_consumidos=200,
            modelo_usado='test-model', duracao_segundos=2.0,
            tentativas=1, validacao_passou=True, contexto_purgado=True
        )
        d = r.to_dict()
        assert d['id'] == 'abc'
        assert d['sucesso'] is True
        assert d['tokens_consumidos'] == 200
        assert d['contexto_purgado'] is True


# =============================================================================
# Testes: SubagenteEphemero
# =============================================================================

class TestSubagenteEphemero:
    def test_criacao(self):
        s = SubagenteEphemero(
            prompt="test prompt",
            contexto="test contexto",
            fase="test_phase",
        )
        assert s.prompt == "test prompt"
        assert s.contexto == "test contexto"
        assert s.contexto_purgado is False

    @patch('utils_subagente_ephemero.solicitar_llm')
    def test_executar_sucesso(self, mock_llm):
        mock_llm.return_value = {
            'conteudo': '{"codigo": "def foo(): pass", "teste": "def test_foo(): assert True"}',
            'tokens_consumidos': 100,
            'modelo_usado': 'test-model',
        }

        s = SubagenteEphemero(
            prompt="gere código",
            contexto="test",
            fase="test",
            validador_fn=lambda x: (True, "OK"),
        )
        resultado = s.executar()

        assert resultado.sucesso is True
        assert resultado.tokens_consumidos == 100
        assert resultado.contexto_purgado is True
        assert s.contexto_purgado is True
        assert s.prompt is None  # Purgado

    @patch('utils_subagente_ephemero.solicitar_llm')
    def test_executar_falha_validacao_tenta_novamente(self, mock_llm):
        # Primeira chamada: falha validação. Segunda: passa.
        mock_llm.side_effect = [
            {'conteudo': '{"codigo": "invalido"}', 'tokens_consumidos': 50, 'modelo_usado': 'm'},
            {'conteudo': '{"codigo": "def foo(): pass"}', 'tokens_consumidos': 60, 'modelo_usado': 'm'},
        ]

        chamadas = []
        def validador(x):
            chamadas.append(x)
            if len(chamadas) == 1:
                return False, "primeira falha"
            return True, "OK"

        s = SubagenteEphemero(
            prompt="gere", contexto="test", fase="test",
            validador_fn=validador, max_tentativas=3,
        )
        resultado = s.executar()

        assert resultado.sucesso is True
        assert resultado.tentativas == 2
        assert resultado.tokens_consumidos == 110

    @patch('utils_subagente_ephemero.solicitar_llm')
    def test_executar_llm_retorna_none(self, mock_llm):
        mock_llm.return_value = None

        s = SubagenteEphemero(
            prompt="gere", contexto="test", fase="test",
            max_tentativas=2,
        )
        resultado = s.executar()

        assert resultado.sucesso is False
        assert resultado.tentativas == 2
        assert resultado.contexto_purgado is True

    def test_purgar_contexto_idempotente(self):
        s = SubagenteEphemero(prompt="p", contexto="c", fase="f")
        s.purgar_contexto()
        assert s.contexto_purgado is True
        # Segunda chamada não deve falhar
        s.purgar_contexto()
        assert s.contexto_purgado is True


# =============================================================================
# Testes: ContextPurgeEngine
# =============================================================================

class TestContextPurgeEngine:
    def test_criacao(self, tmp_path):
        engine = ContextPurgeEngine(pasta_cache=tmp_path)
        assert engine.tokens_totais == 0
        assert engine.taxa_sucesso == 0.0

    @patch('utils_subagente_ephemero.solicitar_llm')
    def test_executar_subagente_sucesso(self, mock_llm, tmp_path):
        mock_llm.return_value = {
            'conteudo': '{"codigo": "def foo(): pass"}',
            'tokens_consumidos': 100,
            'modelo_usado': 'test',
        }

        engine = ContextPurgeEngine(pasta_cache=tmp_path)
        resultado = engine.executar_subagente(
            prompt="gere código",
            contexto="test contexto",
            fase="test_fase",
            validador_fn=lambda x: (True, "OK"),
        )

        assert resultado.sucesso is True
        assert engine.metricas.total_subagentes_criados == 1
        assert engine.metricas.total_subagentes_bem_sucedidos == 1
        assert engine.tokens_totais == 100

    @patch('utils_subagente_ephemero.solicitar_llm')
    def test_executar_subagente_falha(self, mock_llm, tmp_path):
        mock_llm.return_value = None

        engine = ContextPurgeEngine(pasta_cache=tmp_path)
        resultado = engine.executar_subagente(
            prompt="gere", contexto="test", fase="test", max_tentativas=1,
        )

        assert resultado.sucesso is False
        assert engine.metricas.total_subagentes_falharam == 1

    def test_persistir_metricas(self, tmp_path):
        engine = ContextPurgeEngine(pasta_cache=tmp_path)
        caminho = engine.persistir_metricas()
        assert caminho.exists()

        dados = json.loads(caminho.read_text(encoding='utf-8'))
        assert dados['engine'] == 'ContextPurgeEngine'
        assert dados['versao'] == '2.1'
        assert 'metricas' in dados

    @patch('utils_subagente_ephemero.solicitar_llm')
    def test_lote_paralelo(self, mock_llm, tmp_path):
        mock_llm.return_value = {
            'conteudo': '{"ok": true}',
            'tokens_consumidos': 50,
            'modelo_usado': 'test',
        }

        engine = ContextPurgeEngine(pasta_cache=tmp_path)
        tarefas = [
            {'prompt': f'tarefa {i}', 'contexto': f'ctx {i}', 'fase': 'test'}
            for i in range(3)
        ]
        resultados = engine.executar_lote_paralelo(tarefas, max_workers=2)

        assert len(resultados) == 3
        assert engine.metricas.total_subagentes_criados == 3


# =============================================================================
# Testes: Helpers de Prompt
# =============================================================================

class TestHelpersPrompt:
    def test_construir_prompt_ephemero(self):
        p = construir_prompt_ephemero(
            tarefa="Implemente X",
            regras=["Regra 1", "Regra 2"],
            formato_saida='{"codigo":"..."}',
        )
        assert "Implemente X" in p
        assert "1. Regra 1" in p
        assert "2. Regra 2" in p
        assert '{"codigo":"..."}' in p

    def test_construir_prompt_com_contexto(self):
        p = construir_prompt_ephemero(
            tarefa="Tarefa",
            regras=["R1"],
            formato_saida="JSON",
            contexto_minimo="SCHEMA: CREATE TABLE...",
        )
        assert "SCHEMA: CREATE TABLE..." in p

    def test_prompt_codigo_ephemero(self):
        p = prompt_codigo_ephemero("service.py", "CRUD", "criar, listar")
        assert "service.py" in p
        assert "CRUD" in p
        assert "pytest" in p

    def test_prompt_schema_ephemero(self):
        p = prompt_schema_ephemero("app de tarefas", "Python+SQLite", "service, cli")
        assert "app de tarefas" in p
        assert "SQLite" in p

    def test_prompt_correcao_ephemero(self):
        p = prompt_correcao_ephemero("mod.py", "def foo(): pass", "def test_foo(): assert False", "AssertionError")
        assert "mod.py" in p
        assert "AssertionError" in p

    def test_prompt_integracao_ephemero(self):
        p = prompt_integracao_ephemero("app", "Python", "mod1, mod2")
        assert "integração" in p.lower() or "integracao" in p.lower()

    def test_prompts_sao_enxutos(self):
        """Todos os prompts devem ser < 3000 chars (~750 tokens) para efemeridade."""
        prompts = [
            prompt_codigo_ephemero("s.py", "CRUD", "criar"),
            prompt_schema_ephemero("ideia", "stack", "scripts"),
            prompt_correcao_ephemero("m.py", "code", "test", "err"),
            prompt_integracao_ephemero("ideia", "stack", "scripts"),
        ]
        for p in prompts:
            assert len(p) < 3000, f"Prompt muito longo: {len(p)} chars (max 3000)"
