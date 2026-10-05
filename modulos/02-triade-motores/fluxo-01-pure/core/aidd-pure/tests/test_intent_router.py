#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: Intent Router (Detecção de Intenção Zero Fricção)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'phases'))

from utils_intent_router import (
    IntentRouter,
    IntentResultado,
    extrair_argumentos,
    texto_para_pipeline_args,
    detectar_injecao,
    slug_a_partir_da_ideia,
)


# =============================================================================
# Testes: Comandos Diretos (/generate, /aidd-gen, /aidd)
# =============================================================================

class TestComandosDiretos:
    def setup_method(self):
        self.router = IntentRouter()

    def test_generate(self):
        r = self.router.detectar("/generate rastreador de hábitos via CLI")
        assert r.detectado is True
        assert r.intencao == 'gerar_projeto'
        assert r.ideia_extraida == 'rastreador de hábitos via CLI'
        assert r.confianca == 1.0

    def test_aidd_gen(self):
        r = self.router.detectar("/aidd-gen sistema de gerenciamento de tarefas")
        assert r.detectado is True
        assert r.intencao == 'gerar_projeto'
        assert 'gerenciamento' in r.ideia_extraida

    def test_aidd(self):
        r = self.router.detectar("/aidd API REST para catálogo de livros")
        assert r.detectado is True
        assert r.confianca == 0.95

    def test_continue(self):
        r = self.router.detectar("/continue")
        assert r.detectado is True
        assert r.intencao == 'continuar_pipeline'

    def test_status(self):
        r = self.router.detectar("/status")
        assert r.detectado is True
        assert r.intencao == 'ver_status'


# =============================================================================
# Testes: Português Natural
# =============================================================================

class TestPortuguesNatural:
    def setup_method(self):
        self.router = IntentRouter()

    def test_crie_um_sistema(self):
        r = self.router.detectar("crie um sistema de gerenciamento de tarefas com Python")
        assert r.detectado is True
        assert r.intencao == 'gerar_projeto'
        assert 'gerenciamento' in r.ideia_extraida

    def test_quero_um_app(self):
        r = self.router.detectar("quero um app para controlar finanças pessoais")
        assert r.detectado is True
        assert r.intencao == 'gerar_projeto'

    def test_construa_api(self):
        r = self.router.detectar("construa uma API REST para cadastro de clientes")
        assert r.detectado is True
        assert 'cadastro' in r.ideia_extraida

    def test_preciso_de_um_bot(self):
        r = self.router.detectar("preciso de um bot para Discord que gerencie tarefas")
        assert r.detectado is True

    def test_gerar_projeto(self):
        r = self.router.detectar("gere um projeto de e-commerce com Flask")
        assert r.detectado is True
        assert 'e-commerce' in r.ideia_extraida

    def test_continuar_pipeline_pt(self):
        r = self.router.detectar("continue o pipeline")
        assert r.detectado is True
        assert r.intencao == 'continuar_pipeline'

    def test_proxima_fase(self):
        r = self.router.detectar("próxima fase")
        assert r.detectado is True
        assert r.intencao == 'continuar_pipeline'


# =============================================================================
# Testes: Inglês Natural
# =============================================================================

class TestInglesNatural:
    def setup_method(self):
        self.router = IntentRouter()

    def test_build_habit_tracker(self):
        r = self.router.detectar("build a habit tracker CLI with Python and SQLite")
        assert r.detectado is True
        assert r.intencao == 'gerar_projeto'
        assert 'habit tracker' in r.ideia_extraida

    def test_create_rest_api(self):
        r = self.router.detectar("create a REST API for managing a book catalog")
        assert r.detectado is True

    def test_i_need(self):
        r = self.router.detectar("I need a task management system with FastAPI")
        assert r.detectado is True


# =============================================================================
# Testes: Fallback (texto longo)
# =============================================================================

class TestFallback:
    def setup_method(self):
        self.router = IntentRouter()

    def test_texto_longo_vira_ideia(self):
        texto = "um sistema completo de gerenciamento de biblioteca com login, catálogo e empréstimos"
        r = self.router.detectar_ou_fallback(texto)
        assert r.detectado is True
        assert r.intencao == 'gerar_projeto'
        assert r.confianca == 0.5

    def test_texto_curto_nao_detecta(self):
        r = self.router.detectar_ou_fallback("oi")
        assert r.detectado is False

    def test_detectar_puro_texto_curto(self):
        r = self.router.detectar("oi")
        assert r.detectado is False


# =============================================================================
# Testes: Extração de Argumentos
# =============================================================================

class TestExtrairArgumentos:
    def test_pasta(self):
        args = extrair_argumentos("crie um sistema --pasta ../meu-projeto")
        assert args.get('pasta') == '../meu-projeto'

    def test_implementar_codigo(self):
        args = extrair_argumentos("crie um sistema --implementar-codigo")
        assert args.get('implementar_codigo') is True

    def test_com_codigo(self):
        args = extrair_argumentos("crie um sistema --com-codigo")
        assert args.get('implementar_codigo') is True

    def test_interativo(self):
        args = extrair_argumentos("crie um sistema --interativo")
        assert args.get('interativo') is True

    def test_nao_interativo(self):
        args = extrair_argumentos("crie um sistema --nao-interativo")
        assert args.get('nao_interativo') is True

    def test_sem_argumentos(self):
        args = extrair_argumentos("crie um sistema de tarefas")
        assert len(args) == 0

    def test_multiplos_argumentos(self):
        args = extrair_argumentos("crie um sistema --pasta ../x --implementar-codigo --interativo")
        assert args.get('pasta') == '../x'
        assert args.get('implementar_codigo') is True
        assert args.get('interativo') is True


# =============================================================================
# Testes: texto_para_pipeline_args
# =============================================================================

class TestTextoParaPipelineArgs:
    def test_comando_completo(self):
        args = texto_para_pipeline_args("/generate rastreador de hábitos --pasta ../habitos")
        assert args.get('ideia') == 'rastreador de hábitos'
        assert args.get('pasta') == '../habitos'

    def test_linguagem_natural(self):
        args = texto_para_pipeline_args("crie um sistema de gerenciamento de tarefas com Python")
        assert 'ideia' in args
        assert 'gerenciamento' in args['ideia']

    def test_pasta_default(self):
        args = texto_para_pipeline_args("/generate meu projeto de teste")
        assert 'pasta' in args
        assert args['pasta'].startswith('../')

    def test_texto_curto_retorna_vazio(self):
        args = texto_para_pipeline_args("oi")
        assert args == {}


# =============================================================================
# Testes: IntentResultado
# =============================================================================

class TestIntentResultado:
    def test_defaults(self):
        r = IntentResultado()
        assert r.detectado is False
        assert r.intencao is None
        assert r.confianca == 0.0

    def test_argumentos_extras_default(self):
        r = IntentResultado()
        assert r.argumentos_extras == {}


# =============================================================================
# Testes: Injeção de Componentes (Injetor Universal — skills/MCPs/rules/specs/configs)
# =============================================================================

class TestDetectarInjecao:
    def test_skill(self):
        r = detectar_injecao("crie uma skill de auditoria de dependências")
        assert r.detectado is True
        assert r.intencao == 'injetar_componente'
        assert r.argumentos_extras['tipo'] == 'skill'
        assert 'auditoria de dependências' in r.ideia_extraida

    def test_habilidade_mapeia_para_skill(self):
        r = detectar_injecao("adicione uma habilidade de revisão de contratos")
        assert r.argumentos_extras['tipo'] == 'skill'

    def test_mcp(self):
        r = detectar_injecao("adicione um mcp de verificação de CVEs")
        assert r.detectado is True
        assert r.argumentos_extras['tipo'] == 'mcp'
        assert 'CVEs' in r.ideia_extraida

    def test_regra_mapeia_para_rule(self):
        r = detectar_injecao("crie uma regra de não commitar segredos")
        assert r.argumentos_extras['tipo'] == 'rule'

    def test_spec(self):
        r = detectar_injecao("crie uma spec de integração com o gateway de pagamento")
        assert r.argumentos_extras['tipo'] == 'spec'

    def test_especificacao_mapeia_para_spec(self):
        r = detectar_injecao("gere uma especificação de migração de banco de dados")
        assert r.argumentos_extras['tipo'] == 'spec'

    def test_config(self):
        r = detectar_injecao("adicione uma config de timeout do pipeline")
        assert r.argumentos_extras['tipo'] == 'config'

    def test_comando_slash_inject(self):
        r = detectar_injecao("/inject skill auditoria de segredos")
        assert r.detectado is True
        assert r.confianca == 1.0
        assert r.argumentos_extras['tipo'] == 'skill'

    def test_texto_sem_intencao_de_injecao_nao_detecta(self):
        r = detectar_injecao("crie um sistema de gerenciamento de tarefas")
        assert r.detectado is False

    def test_texto_vazio_nao_detecta(self):
        assert detectar_injecao("").detectado is False

    def test_nao_interfere_com_gerar_projeto(self):
        """Padrões de injeção não devem capturar frases de geração de projeto (aditivo, sem regressão)."""
        router = IntentRouter()
        r = router.detectar("crie um sistema de gerenciamento de tarefas com Python")
        assert r.intencao == 'gerar_projeto'

    def test_metodo_no_router_delega_para_funcao(self):
        router = IntentRouter()
        r = router.detectar_injecao("crie uma skill de teste")
        assert r.detectado is True
        assert r.argumentos_extras['tipo'] == 'skill'


class TestSlugAPartirDaIdeia:
    def test_gera_slug_kebab_case(self):
        assert slug_a_partir_da_ideia("Auditoria de Dependências") == 'auditoria-de-depend-ncias'

    def test_slug_nao_vazio_para_texto_sem_letras(self):
        assert slug_a_partir_da_ideia("!!!") == 'componente'

    def test_respeita_tamanho_maximo(self):
        texto_longo = "a" * 200
        assert len(slug_a_partir_da_ideia(texto_longo, tamanho_max=50)) <= 50
