# -*- coding: utf-8 -*-
"""
Suíte de Testes Unitários e de Integração: aidd-planner
"""
import json
import os
import sys
import tempfile
import pytest

_PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ECOSSISTEMA_DIR = os.path.dirname(_PLANNER_DIR)

if _PLANNER_DIR not in sys.path:
    sys.path.insert(0, _PLANNER_DIR)
if _ECOSSISTEMA_DIR not in sys.path:
    sys.path.insert(0, _ECOSSISTEMA_DIR)

from src.core.planner_engine import (
    carregar_schema,
    validar_plano,
    gerar_template_plano,
    exportar_para_fluxo_factory,
    PlannerValidationError,
)
from src.cli import main as cli_main
from gates.G_PLANNER_SCHEMA import main as gate_schema_main
from gates.G_PLANNER_SINE_QUA_NON import main as gate_sine_main
from gates.G_PLANNER_COERENCIA_FLUXO import main as gate_coerencia_main


def test_carregamento_schema_valido():
    schema = carregar_schema()
    assert "$schema" in schema
    assert "properties" in schema
    assert "quarteto_sine_qua_non" in schema["required"]


def test_geracao_e_validacao_fluxo_01():
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_01_generator",
        projeto_nome="App E-Commerce",
        slug="app-ecommerce",
        descricao="Sistema completo de comércio eletrônico com pagamentos",
        dominio="comercio"
    )
    valido, erros = validar_plano(plano)
    assert valido is True, f"Erros encontrados: {erros}"
    assert len(erros) == 0
    assert plano["meta"]["fluxo_alvo"] == "fluxo_01_generator"
    assert len(plano["payload_especifico_fluxo"]["fatias_vsa"]) >= 1
    assert len(plano["payload_especifico_fluxo"]["casos_teste_tdd"]) >= 1


def test_geracao_e_validacao_fluxo_02():
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_02_factory",
        projeto_nome="Hub Atendimento",
        slug="hub-atendimento",
        descricao="Plataforma multicanal de atendimento e automação",
        dominio="atendimento"
    )
    valido, erros = validar_plano(plano)
    assert valido is True, f"Erros encontrados: {erros}"
    assert len(erros) == 0
    assert plano["meta"]["fluxo_alvo"] == "fluxo_02_factory"
    assert len(plano["payload_especifico_fluxo"]["ferramentas_opensource"]) >= 1


def test_geracao_e_validacao_fluxo_03():
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_03_bridge",
        projeto_nome="Portal Financeiro",
        slug="portal-financeiro",
        descricao="Dashboard financeiro exportado do Lovable",
        dominio="financeiro"
    )
    valido, erros = validar_plano(plano)
    assert valido is True, f"Erros encontrados: {erros}"
    assert len(erros) == 0
    assert plano["meta"]["fluxo_alvo"] == "fluxo_03_bridge"
    assert len(plano["payload_especifico_fluxo"]["mapeamento_banco"]) >= 1


def test_rejeicao_plano_sem_quarteto():
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_01_generator",
        projeto_nome="Teste Quebrado",
        slug="teste-quebrado",
        descricao="Descrição com mais de dez caracteres",
        dominio="geral"
    )
    del plano["quarteto_sine_qua_non"]
    valido, erros = validar_plano(plano)
    assert valido is False
    assert any("quarteto_sine_qua_non" in e for e in erros)


def test_rejeicao_plano_sem_cenarios_bdd():
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_01_generator",
        projeto_nome="Teste Sem BDD",
        slug="teste-sem-bdd",
        descricao="Descrição longa de teste para validação",
        dominio="geral"
    )
    plano["bdd_cenarios"] = []
    valido, erros = validar_plano(plano)
    assert valido is False
    assert any("bdd_cenarios" in e for e in erros)


def test_exportacao_para_aidd_factory():
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_02_factory",
        projeto_nome="Stack OpenSource",
        slug="stack-opensource",
        descricao="Stack integrada de serviços abertos de mensageria",
        dominio="mensageria"
    )
    factory_input = exportar_para_fluxo_factory(plano)
    assert factory_input["projeto"] == "stack-opensource"
    assert len(factory_input["servicos"]) >= 1
    assert factory_input["servicos"][0]["nome"] == "evolution-api"


def test_gates_execucao_com_arquivo_valido():
    with tempfile.TemporaryDirectory() as tmpdir:
        plano = gerar_template_plano(
            fluxo_alvo="fluxo_01_generator",
            projeto_nome="Gate Test Proj",
            slug="gate-test-proj",
            descricao="Projeto dedicado para validar os quality gates",
            dominio="testes"
        )
        caminho = os.path.join(tmpdir, "PLANNER.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(plano, f, indent=2)

        assert gate_schema_main(tmpdir) == 0
        assert gate_sine_main(tmpdir) == 0
        assert gate_coerencia_main(tmpdir) == 0


def test_cli_init_e_validate():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Teste init
        ret_init = cli_main([
            "init",
            "--fluxo", "1",
            "--nome", "Projeto CLI Test",
            "--slug", "projeto-cli-test",
            "--descricao", "Descrição detalhada do projeto para passar nas validações",
            "--pasta", tmpdir
        ])
        assert ret_init == 0
        planner_file = os.path.join(tmpdir, "PLANNER.json")
        assert os.path.isfile(planner_file)

        # 2. Teste validate
        ret_val = cli_main(["validate", planner_file])
        assert ret_val == 0
