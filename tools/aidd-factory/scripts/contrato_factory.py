# -*- coding: utf-8 -*-
"""
AIDD-Factory — Validador de Contratos de Input/Output.

Valida PLANO-INFRAESTRUTURA.json (input) e FACTORY_OUTPUT.json (output)
contra seus respectivos JSON Schemas.
"""
import json
import os
import sys

_FACTORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "src"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "..", "..", "componentes", "compartilhado", "src-core"))

from core.result import Result

_SCHEMAS_DIR = os.path.join(_FACTORY_ROOT, "schemas")


def _carregar_schema(nome: str) -> dict:
    caminho = os.path.join(_SCHEMAS_DIR, nome)
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _validar_campos_obrigatorios(dados: dict, schema: dict) -> list:
    """Validacao manual de campos obrigatorios (sem jsonschema dep)."""
    erros = []
    for campo in schema.get("required", []):
        if campo not in dados:
            erros.append(f"Campo obrigatorio ausente: '{campo}'")
    return erros


def validar_plano_factory(dados: dict) -> Result:
    """Valida PLANO-INFRAESTRUTURA.json contra schema_factory_input.json."""
    schema = _carregar_schema("schema_factory_input.json")
    erros = _validar_campos_obrigatorios(dados, schema)
    if erros:
        return Result.fail(
            "PLANO-INFRAESTRUTURA nao adere ao contrato factory.",
            codigo="FACTORY_INPUT_INVALID",
            detalhes={"erros": erros},
        )
    # Validar que pelo menos fase_3_sizing tem saida (nao erro)
    fase3 = dados.get("fase_3_sizing", {})
    if fase3.get("saida") is None:
        return Result.fail(
            "PLANO-INFRAESTRUTURA com fase_3_sizing sem saida (erro na fase).",
            codigo="FACTORY_INPUT_INCOMPLETE",
            detalhes={"fase_3_erro": fase3.get("erro")},
        )
    return Result.ok(dados)


def validar_factory_output(dados: dict) -> Result:
    """Valida FACTORY_OUTPUT.json contra schema_factory_output.json."""
    schema = _carregar_schema("schema_factory_output.json")
    erros = _validar_campos_obrigatorios(dados, schema)
    if erros:
        return Result.fail(
            "FACTORY_OUTPUT nao adere ao contrato.",
            codigo="FACTORY_OUTPUT_INVALID",
            detalhes={"erros": erros},
        )
    return Result.ok(dados)
