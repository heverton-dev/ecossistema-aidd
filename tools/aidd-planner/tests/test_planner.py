# -*- coding: utf-8 -*-
"""
Suíte de Testes Unitários e de Integração: aidd-planner
"""
import json
import os
import subprocess
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
    """Achado real (18/09/2026): exportar_para_fluxo_factory produzia
    {projeto, descricao, servicos, banco_central} — um formato que o
    pipeline_factory.py REAL rejeitava com FACTORY_INPUT_INVALID em 100%
    dos casos (nenhum PLANNER.json exportado por este comando jamais
    passou pelo pipeline real), quebrando o Fluxo 02 documentado
    (FORGE -> PRÉ-PLANO -> FACTORY) ponta a ponta via CLI. A exportação
    correta usa o envelope fase_1_intake/fase_2_curadoria/fase_3_sizing
    (aidd-ops, caminho "nicho dinâmico" — a stack já foi decidida no
    PRÉ-PLANO, sem tentar casar o domínio contra os 5 nichos fixos do
    catálogo). Regressão: roda o pipeline_factory.py REAL (não uma
    checagem paralela) contra o plano exportado e exige sucesso real."""
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_02_factory",
        projeto_nome="Stack OpenSource",
        slug="stack-opensource",
        descricao="Stack integrada de serviços abertos de mensageria",
        dominio="mensageria"
    )
    factory_input = exportar_para_fluxo_factory(plano)

    assert factory_input["fase_1_intake"]["saida"]["nicho_slug"].startswith("dinamico_")
    ferramentas = factory_input["fase_2_curadoria"]["saida"]["ferramentas"]
    assert any(f["nome"] == "Evolution API" for f in ferramentas)

    with tempfile.TemporaryDirectory() as tmpdir:
        plano_path = os.path.join(tmpdir, "PLANO-INFRAESTRUTURA.json")
        with open(plano_path, "w", encoding="utf-8") as f:
            json.dump(factory_input, f)

        _repo_root = os.path.dirname(_ECOSSISTEMA_DIR)  # _ECOSSISTEMA_DIR aqui e' "tools/", nao a raiz
        pipeline_script = os.path.join(_repo_root, "tools", "aidd-factory", "scripts", "pipeline_factory.py")
        saida_dir = os.path.join(tmpdir, "saida")
        resultado = subprocess.run(
            [sys.executable, pipeline_script, "--plano", plano_path, "--pasta", saida_dir, "--sem-llm"],
            capture_output=True, text=True, timeout=60,
        )
        assert resultado.returncode == 0, (
            f"pipeline_factory.py rejeitou o plano exportado pelo aidd-planner.\n"
            f"STDOUT: {resultado.stdout}\nSTDERR: {resultado.stderr}"
        )
        assert os.path.isfile(os.path.join(saida_dir, "factory_analysis.json"))
        assert os.path.isfile(os.path.join(saida_dir, "docker-compose.yml"))


def test_exportacao_para_aidd_factory_dominio_fora_do_catalogo_fixo():
    """Achado real (18/09/2026): "gestão de tarefas" não bate nenhuma das
    palavras-chave dos 5 nichos fixos de catalogo_nichos.json — antes desta
    correção, isso quebrava a exportação inteira (NICHO_NAO_RECONHECIDO)
    mesmo com a stack de ferramentas já decidida no PRÉ-PLANO. O caminho
    "nicho dinâmico" não depende de bater palavra-chave: qualquer domínio
    passa, desde que a stack já esteja definida no plano."""
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_02_factory",
        projeto_nome="Gestao de Tarefas",
        slug="gestao-tarefas-factory",
        descricao="Aplicacao de gestao de tarefas via engines OSS",
        dominio="gestao de tarefas",
    )
    factory_input = exportar_para_fluxo_factory(plano)
    assert factory_input["fase_1_intake"]["erro"] is None
    assert factory_input["fase_3_sizing"]["saida"] is not None


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


def test_cli_init_gera_design_system_unico_por_projeto():
    """Lei Inviolável #11: a identidade visual nasce no planner, de forma
    determinística e ÚNICA por projeto — não pode ser fixa/hardcoded no
    gerador de frontend (achado real do usuário, 18/09/2026: um design fixo
    faria todo projeto gerado ter a mesma cara)."""
    with tempfile.TemporaryDirectory() as tmp_saude, tempfile.TemporaryDirectory() as tmp_delivery:
        cli_main([
            "init", "--fluxo", "1", "--nome", "Clinica Bem Estar", "--slug", "clinica-bem-estar",
            "--descricao", "Sistema de agendamento para clinica de saude", "--dominio", "saude",
            "--pasta", tmp_saude,
        ])
        cli_main([
            "init", "--fluxo", "1", "--nome", "Lanchonete Rapida", "--slug", "lanchonete-rapida",
            "--descricao", "Sistema de pedidos para delivery de comida", "--dominio", "delivery",
            "--pasta", tmp_delivery,
        ])

        ds_saude_path = os.path.join(tmp_saude, "DESIGN-SYSTEM.json")
        ds_delivery_path = os.path.join(tmp_delivery, "DESIGN-SYSTEM.json")
        assert os.path.isfile(ds_saude_path)
        assert os.path.isfile(ds_delivery_path)

        with open(ds_saude_path, encoding="utf-8") as f:
            ds_saude = json.load(f)
        with open(ds_delivery_path, encoding="utf-8") as f:
            ds_delivery = json.load(f)

        # Nichos diferentes -> paletas diferentes (prova de que não é fixo)
        assert ds_saude["paleta"]["primaria"] != ds_delivery["paleta"]["primaria"]
        # Nicho "saude" bate a palavra-chave real do catálogo
        assert ds_saude["paleta"]["primaria"] == "#0F766E"
        assert ds_delivery["paleta"]["primaria"] == "#EA580C"

        # Determinismo: gerar de novo para o MESMO projeto dá a MESMA paleta
        from src.core.design_system import gerar_design_system
        ds_saude_repetido = gerar_design_system(
            "Clinica Bem Estar", "clinica-bem-estar",
            "Sistema de agendamento para clinica de saude", "saude",
        )
        assert ds_saude_repetido["paleta"] == ds_saude["paleta"]
