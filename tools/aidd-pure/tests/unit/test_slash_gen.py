#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: Slash Command Handler (scripts/commands/slash_gen.py)
Sprint 04 — Camada Zero Fricção
"""

import sys
from pathlib import Path

import pytest

# Adicionar diretórios ao path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / 'scripts' / 'commands'))
sys.path.insert(0, str(ROOT_DIR / 'scripts' / 'phases'))

from slash_gen import (
    SlashCommandHandler,
    ComandoSlash,
    ResultadoSlash,
    slash_para_pipeline_args,
    formatar_resultado,
    COMANDOS_SLASH,
    AJUDA_TEXTO,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def handler():
    return SlashCommandHandler()


# =============================================================================
# Testes: Comandos Diretos (/generate, /aidd-gen, /aidd, /gen)
# =============================================================================

class TestComandosDiretosGenerate:
    """Testes para /generate <ideia>."""

    def test_generate_basico(self, handler):
        r = handler.processar("/generate rastreador de hábitos via CLI")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'
        assert r.ideia == 'rastreador de hábitos via CLI'
        assert r.confianca == 1.0

    def test_generate_com_espacos(self, handler):
        r = handler.processar("/generate   sistema de gerenciamento de tarefas  ")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'
        assert 'gerenciamento' in r.ideia

    def test_generate_com_argumentos(self, handler):
        r = handler.processar("/generate app de finanças --pasta ../financas")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'
        assert r.ideia == 'app de finanças'
        assert r.argumentos.get('pasta') == '../financas'

    def test_generate_com_implementar_codigo(self, handler):
        r = handler.processar("/generate API REST --implementar-codigo")
        assert r.sucesso is True
        assert r.argumentos.get('implementar_codigo') is True
        # ideia não deve conter o argumento
        assert '--implementar-codigo' not in r.ideia

    def test_generate_sem_ideia_falha(self, handler):
        r = handler.processar("/generate")
        # /generate sem argumento não casa com o regex (precisa de \s+(.+))
        assert r.acao != 'gerar_projeto' or not r.sucesso


class TestComandosAiddGen:
    """Testes para /aidd-gen <ideia>."""

    def test_aidd_gen_basico(self, handler):
        r = handler.processar("/aidd-gen sistema de gerenciamento de tarefas")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'
        assert 'gerenciamento' in r.ideia
        assert r.confianca == 1.0

    def test_aidd_gen_com_pasta(self, handler):
        r = handler.processar("/aidd-gen bot Discord --pasta ../meu-bot")
        assert r.sucesso is True
        assert r.argumentos.get('pasta') == '../meu-bot'


class TestComandosAidd:
    """Testes para /aidd <ideia>."""

    def test_aidd_basico(self, handler):
        r = handler.processar("/aidd API REST para catálogo de livros")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'
        assert r.confianca == 0.95

    def test_aidd_case_insensitive(self, handler):
        r = handler.processar("/AIDD sistema de tarefas")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'


class TestComandosGen:
    """Testes para /gen <ideia> (alias curto)."""

    def test_gen_basico(self, handler):
        r = handler.processar("/gen bot para Discord")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'
        assert r.confianca == 0.95

    def test_gen_com_argumentos(self, handler):
        r = handler.processar("/gen app de finanças --pasta ../fin --interativo")
        assert r.sucesso is True
        assert r.argumentos.get('pasta') == '../fin'
        assert r.argumentos.get('interativo') is True


# =============================================================================
# Testes: Comandos de Pipeline (/continue, /resume, /status)
# =============================================================================

class TestComandosPipeline:
    def test_continue(self, handler):
        r = handler.processar("/continue")
        assert r.sucesso is True
        assert r.acao == 'continuar_pipeline'
        assert r.confianca == 1.0

    def test_resume(self, handler):
        r = handler.processar("/resume")
        assert r.sucesso is True
        assert r.acao == 'continuar_pipeline'

    def test_status(self, handler):
        r = handler.processar("/status")
        assert r.sucesso is True
        assert r.acao == 'ver_status'

    def test_aidd_status(self, handler):
        r = handler.processar("/aidd-status")
        assert r.sucesso is True
        assert r.acao == 'ver_status'


# =============================================================================
# Testes: Comando /help
# =============================================================================

class TestComandoHelp:
    def test_help(self, handler):
        r = handler.processar("/help")
        assert r.sucesso is True
        assert r.acao == 'ajuda'
        assert 'COMANDOS' in r.mensagem

    def test_aidd_help(self, handler):
        r = handler.processar("/aidd-help")
        assert r.sucesso is True
        assert r.acao == 'ajuda'


# =============================================================================
# Testes: Linguagem Natural (Intent Router fallback)
# =============================================================================

class TestLinguagemNatural:
    def test_crie_um_sistema(self, handler):
        r = handler.processar("crie um sistema de gerenciamento de tarefas com Python")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'
        assert 'gerenciamento' in r.ideia
        assert r.confianca >= 0.7

    def test_quero_um_app(self, handler):
        r = handler.processar("quero um app para controlar finanças pessoais")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'

    def test_construa_api(self, handler):
        r = handler.processar("construa uma API REST para cadastro de clientes")
        assert r.sucesso is True
        assert 'cadastro' in r.ideia

    def test_preciso_de_um_bot(self, handler):
        r = handler.processar("preciso de um bot para Discord que gerencie tarefas")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'

    def test_build_english(self, handler):
        r = handler.processar("build a habit tracker CLI with Python and SQLite")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'
        assert 'habit tracker' in r.ideia

    def test_create_english(self, handler):
        r = handler.processar("create a REST API for managing a book catalog")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'

    def test_i_need_english(self, handler):
        r = handler.processar("I need a task management system with FastAPI")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'


# =============================================================================
# Testes: Texto não detectável
# =============================================================================

class TestNaoDetectado:
    def test_texto_curto(self, handler):
        r = handler.processar("oi")
        assert r.sucesso is False
        assert r.acao == 'desconhecido'

    def test_texto_vazio(self, handler):
        r = handler.processar("")
        assert r.sucesso is False

    def test_none(self, handler):
        r = handler.processar(None)
        assert r.sucesso is False

    def test_aleatorio(self, handler):
        r = handler.processar("ajuda")
        assert r.sucesso is False
        assert r.acao == 'desconhecido'


# =============================================================================
# Testes: parsear_comando
# =============================================================================

class TestParsearComando:
    def test_parse_generate(self, handler):
        cmd = handler.parsear_comando("/generate meu projeto")
        assert cmd is not None
        assert cmd.comando == '/generate'
        assert cmd.argumento == 'meu projeto'

    def test_parse_aidd_gen(self, handler):
        cmd = handler.parsear_comando("/aidd-gen sistema X")
        assert cmd is not None
        assert cmd.comando == '/aidd-gen'

    def test_parse_continue(self, handler):
        cmd = handler.parsear_comando("/continue")
        assert cmd is not None
        assert cmd.argumento == ''

    def test_parse_nao_comando(self, handler):
        cmd = handler.parsear_comando("crie um sistema de tarefas")
        assert cmd is None

    def test_parse_vazio(self, handler):
        cmd = handler.parsear_comando("")
        assert cmd is None

    def test_parse_none(self, handler):
        cmd = handler.parsear_comando(None)
        assert cmd is None


# =============================================================================
# Testes: slash_para_pipeline_args
# =============================================================================

class TestSlashParaPipelineArgs:
    def test_generate_com_pasta(self):
        args = slash_para_pipeline_args("/generate rastreador de hábitos --pasta ../habitos")
        assert args.get('ideia') == 'rastreador de hábitos'
        assert args.get('pasta') == '../habitos'

    def test_aidd_gen_linguagem_natural(self):
        args = slash_para_pipeline_args("crie um sistema de gerenciamento de tarefas com Python")
        assert 'ideia' in args
        assert 'gerenciamento' in args['ideia']

    def test_pasta_default(self):
        args = slash_para_pipeline_args("/generate meu projeto de teste")
        assert 'pasta' in args
        assert args['pasta'].startswith('../')

    def test_texto_curto_retorna_vazio(self):
        args = slash_para_pipeline_args("oi")
        assert args == {}

    def test_continue_retorna_vazio(self):
        args = slash_para_pipeline_args("/continue")
        assert args == {}

    def test_help_retorna_vazio(self):
        args = slash_para_pipeline_args("/help")
        assert args == {}


# =============================================================================
# Testes: formatar_resultado
# =============================================================================

class TestFormatarResultado:
    def test_formatar_gerar_projeto(self):
        r = ResultadoSlash(
            acao='gerar_projeto',
            ideia='sistema de tarefas',
            confianca=0.9,
            pasta_sugerida='../sistema-de-tarefas',
            sucesso=True,
        )
        texto = formatar_resultado(r)
        assert 'sistema de tarefas' in texto
        assert '90%' in texto

    def test_formatar_ajuda(self):
        r = ResultadoSlash(acao='ajuda', sucesso=True, mensagem=AJUDA_TEXTO)
        texto = formatar_resultado(r)
        assert 'COMANDOS' in texto

    def test_formatar_continuar(self):
        r = ResultadoSlash(acao='continuar_pipeline', sucesso=True)
        texto = formatar_resultado(r)
        assert 'Continuando' in texto

    def test_formatar_erro(self):
        r = ResultadoSlash(acao='desconhecido', sucesso=False, mensagem='Erro teste')
        texto = formatar_resultado(r)
        assert 'Erro teste' in texto

    def test_formatar_status(self):
        r = ResultadoSlash(acao='ver_status', sucesso=True)
        texto = formatar_resultado(r)
        assert 'Status' in texto


# =============================================================================
# Testes: Data Classes
# =============================================================================

class TestComandoSlash:
    def test_criacao(self):
        cmd = ComandoSlash(comando='/generate', argumento='meu projeto', raw='/generate meu projeto')
        assert cmd.comando == '/generate'
        assert cmd.argumento == 'meu projeto'
        assert cmd.raw == '/generate meu projeto'


class TestResultadoSlash:
    def test_defaults(self):
        r = ResultadoSlash(acao='desconhecido')
        assert r.sucesso is True
        assert r.ideia is None
        assert r.confianca == 0.0
        assert r.argumentos == {}
        assert r.pasta_sugerida is None

    def test_argumentos_default_factory(self):
        r1 = ResultadoSlash(acao='gerar_projeto')
        r2 = ResultadoSlash(acao='gerar_projeto')
        r1.argumentos['x'] = 1
        assert 'x' not in r2.argumentos


# =============================================================================
# Testes: listar_comandos
# =============================================================================

class TestListarComandos:
    def test_retorna_lista(self, handler):
        cmds = handler.listar_comandos()
        assert isinstance(cmds, list)
        assert len(cmds) >= 5
        assert any('/generate' in c for c in cmds)
        assert any('/aidd-gen' in c for c in cmds)


# =============================================================================
# Testes: COMANDOS_SLASH registry
# =============================================================================

class TestComandosSlashRegistry:
    def test_registry_nao_vazio(self):
        assert len(COMANDOS_SLASH) > 0

    def test_registry_tem_generate(self):
        comandos = [c[0] for c in COMANDOS_SLASH]
        assert any('/generate' in c for c in comandos)

    def test_registry_tem_aidd_gen(self):
        comandos = [c[0] for c in COMANDOS_SLASH]
        assert any('/aidd-gen' in c for c in comandos)

    def test_registry_tem_continue(self):
        comandos = [c[0] for c in COMANDOS_SLASH]
        assert any('/continue' in c for c in comandos)

    def test_registry_tem_help(self):
        comandos = [c[0] for c in COMANDOS_SLASH]
        assert any('/help' in c for c in comandos)


# =============================================================================
# Testes: Case Insensitive
# =============================================================================

class TestCaseInsensitive:
    def test_generate_maiusculo(self, handler):
        r = handler.processar("/GENERATE sistema de tarefas")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'

    def test_aidd_gen_misto(self, handler):
        r = handler.processar("/AIDD-Gen sistema de tarefas")
        assert r.sucesso is True
        assert r.acao == 'gerar_projeto'

    def test_continue_maiusculo(self, handler):
        r = handler.processar("/CONTINUE")
        assert r.sucesso is True
        assert r.acao == 'continuar_pipeline'


# =============================================================================
# Testes: Argumentos extras no texto
# =============================================================================

class TestArgumentosExtras:
    def test_implementar_codigo(self, handler):
        r = handler.processar("/generate API REST --implementar-codigo")
        assert r.argumentos.get('implementar_codigo') is True

    def test_com_codigo(self, handler):
        r = handler.processar("/generate API REST --com-codigo")
        assert r.argumentos.get('implementar_codigo') is True

    def test_interativo(self, handler):
        r = handler.processar("/generate API REST --interativo")
        assert r.argumentos.get('interativo') is True

    def test_nao_interativo(self, handler):
        r = handler.processar("/generate API REST --nao-interativo")
        assert r.argumentos.get('nao_interativo') is True

    def test_multiplos_argumentos(self, handler):
        r = handler.processar("/generate API REST --pasta ../api --implementar-codigo --interativo")
        assert r.argumentos.get('pasta') == '../api'
        assert r.argumentos.get('implementar_codigo') is True
        assert r.argumentos.get('interativo') is True
        # ideia não deve conter os argumentos
        assert '--pasta' not in r.ideia
        assert '--implementar-codigo' not in r.ideia
