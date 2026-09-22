# -*- coding: utf-8 -*-
"""
Suíte de Testes Unitários e de Integração: Compilador de Grafo Topológico VSA (ISSUE-MESO-0002)
"""
import json
import os
import sys
import tempfile
import pytest

_PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ECOSSISTEMA_DIR = os.path.dirname(_PLANNER_DIR)
_ROOT_DIR = os.path.dirname(_ECOSSISTEMA_DIR)

if _PLANNER_DIR not in sys.path:
    sys.path.insert(0, _PLANNER_DIR)
if _ECOSSISTEMA_DIR not in sys.path:
    sys.path.insert(0, _ECOSSISTEMA_DIR)

from src.core.planner_engine import (
    gerar_template_plano,
    compilar_grafo_topologico_vsa,
    PlannerValidationError,
)
from src.cli import main as cli_main
from jsonschema import Draft7Validator

_SCHEMA_VSA_PATH = os.path.join(
    _ROOT_DIR, "componentes", "compartilhado", "specs", "vsa-topological-dispatch.schema.json"
)


def _obter_validator_vsa():
    with open(_SCHEMA_VSA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def test_compilar_vsa_fluxo_01_valido():
    validator = _obter_validator_vsa()
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_01_generator",
        projeto_nome="App Loja Pure",
        slug="app-loja-pure",
        descricao="Sistema completo do zero puro",
        dominio="comercio",
    )
    manifesto = compilar_grafo_topologico_vsa(plano)

    assert manifesto["versao_schema"] == "1.0.0"
    assert manifesto["fluxo_alvo"] == "fluxo_01_generator"
    assert len(manifesto["grafo_fatias"]) >= 1
    assert manifesto["convergencia_master"]["merge_strategy"] == "fast-forward"

    erros = list(validator.iter_errors(manifesto))
    assert len(erros) == 0, f"Erros de validação do schema: {erros}"


def test_compilar_vsa_fluxo_02_valido():
    validator = _obter_validator_vsa()
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_02_factory",
        projeto_nome="App Factory Open",
        slug="app-factory-open",
        descricao="Sistema baseado em componentes open source",
        dominio="logistica",
    )
    manifesto = compilar_grafo_topologico_vsa(plano)

    assert manifesto["versao_schema"] == "1.0.0"
    assert manifesto["fluxo_alvo"] == "fluxo_02_factory"
    assert len(manifesto["grafo_fatias"]) >= 1

    erros = list(validator.iter_errors(manifesto))
    assert len(erros) == 0, f"Erros de validação do schema: {erros}"


def test_compilar_vsa_fluxo_03_valido():
    validator = _obter_validator_vsa()
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_03_bridge",
        projeto_nome="App Freedom Bridge",
        slug="app-freedom-bridge",
        descricao="Sistema migrado de low-code para stack soberana",
        dominio="saude",
    )
    manifesto = compilar_grafo_topologico_vsa(plano)

    assert manifesto["versao_schema"] == "1.0.0"
    assert manifesto["fluxo_alvo"] == "fluxo_03_bridge"
    assert len(manifesto["grafo_fatias"]) >= 1

    erros = list(validator.iter_errors(manifesto))
    assert len(erros) == 0, f"Erros de validação do schema: {erros}"


def test_compilador_vsa_rejeita_ciclo():
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_01_generator",
        projeto_nome="App Ciclico",
        slug="app-ciclico",
        descricao="Sistema com ciclo intencional",
        dominio="financeiro",
    )
    # Cria ciclo direto: A depende de B, B depende de A
    plano["ddd_bounded_contexts"] = [
        {
            "modulo": "Modulo Alpha",
            "dependencias": ["modulo_beta"],
            "entidades": [
                {
                    "nome": "Alpha",
                    "atributos": {"id": "integer"},
                    "regras_invariantes": ["id positivo"],
                }
            ],
        },
        {
            "modulo": "Modulo Beta",
            "dependencias": ["modulo_alpha"],
            "entidades": [
                {
                    "nome": "Beta",
                    "atributos": {"id": "integer"},
                    "regras_invariantes": ["id positivo"],
                }
            ],
        },
    ]

    with pytest.raises(PlannerValidationError) as excinfo:
        compilar_grafo_topologico_vsa(plano)

    assert "Ciclo de dependência detectado" in str(excinfo.value)


def test_compilador_vsa_rejeita_dependencia_inexistente():
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_01_generator",
        projeto_nome="App Dep Inexistente",
        slug="app-dep-inexistente",
        descricao="Sistema com dependencia fantasma",
        dominio="financeiro",
    )
    plano["ddd_bounded_contexts"] = [
        {
            "modulo": "Modulo Alpha",
            "dependencias": ["modulo_inexistente_xyz"],
            "entidades": [
                {
                    "nome": "Alpha",
                    "atributos": {"id": "integer"},
                    "regras_invariantes": ["id positivo"],
                }
            ],
        }
    ]

    with pytest.raises(PlannerValidationError) as excinfo:
        compilar_grafo_topologico_vsa(plano)

    assert "referencia dependência inexistente" in str(excinfo.value)


def test_cli_export_dispatch_sucesso():
    plano = gerar_template_plano(
        fluxo_alvo="fluxo_01_generator",
        projeto_nome="App CLI Teste",
        slug="app-cli-teste",
        descricao="Teste de export via CLI",
        dominio="comercio",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        plano_path = os.path.join(tmpdir, "PLANNER.json")
        with open(plano_path, "w", encoding="utf-8") as f:
            json.dump(plano, f, indent=2)

        saida_dispatch = os.path.join(tmpdir, "vsa_dispatch.json")
        ret = cli_main(["export-dispatch", plano_path, "--output", saida_dispatch])
        assert ret == 0
        assert os.path.isfile(saida_dispatch)

        with open(saida_dispatch, "r", encoding="utf-8") as f:
            dados = json.load(f)

        assert dados["versao_schema"] == "1.0.0"
        assert dados["projeto_slug"] == "app-cli-teste"
        assert len(dados["grafo_fatias"]) >= 1
