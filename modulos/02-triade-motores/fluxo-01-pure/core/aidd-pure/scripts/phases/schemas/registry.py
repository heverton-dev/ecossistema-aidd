# -*- coding: utf-8 -*-
"""
Registry de schemas versionados do Protocolo Delegado.

Gerencia carregamento e validação de JSON Schemas para payloads
_llm_request e _llm_response, com versionamento semântico (v1, v2, ...).

Uso:
    from schemas.registry import validar_request, validar_response
    validar_request(dados)  # levanta SchemaValidationError se inválido
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from jsonschema import validate, ValidationError as JsonSchemaValidationError

SCHEMA_DIR = Path(__file__).parent


class SchemaVersion:
    """Versionamento semântico dos schemas do Protocolo Delegado e Pipeline."""

    LATEST = "v1"

    SUPPORTED = {
        "v1": {
            "request": "llm_request_v1.json",
            "response": "llm_response_v1.json",
            "pipeline_state": "pipeline_state_v1.json",
            "cache_insights_phase1": "cache_insights_phase1_v1.json",
            "cache_analise_phase2": "cache_analise_phase2_v1.json",
            "cache_design_phase3": "cache_design_phase3_v1.json",
            "cache_config_phase4": "cache_config_phase4_v1.json",
        },
    }


class SchemaValidationError(Exception):
    """Payload não corresponde ao JSON Schema especificado."""

    def __init__(self, schema_name: str, errors: list):
        self.schema_name = schema_name
        self.errors = errors
        msg = f"Validação '{schema_name}' falhou: {len(errors)} erro(s)"
        super().__init__(msg)

    def __str__(self) -> str:
        detalhes = "; ".join(self.errors[:5])
        return f"{super().__str__()} — {detalhes}"


def carregar_schema(tipo: str, version: Optional[str] = None) -> Dict[str, Any]:
    """Carrega JSON Schema do disco.

    Args:
        tipo: Identificador do schema (ex: 'request', 'response', 'pipeline_state', etc.)
        version: Versão do schema (default: LATEST)

    Returns:
        Dict com o schema JSON carregado

    Raises:
        FileNotFoundError: Se o arquivo de schema não existir
        ValueError: Se a versão ou o tipo não forem suportados
    """
    version = version or SchemaVersion.LATEST

    if version not in SchemaVersion.SUPPORTED:
        raise ValueError(
            f"Versão '{version}' não suportada. "
            f"Versões disponíveis: {list(SchemaVersion.SUPPORTED.keys())}"
        )

    versoes_disponiveis = SchemaVersion.SUPPORTED[version]
    if tipo not in versoes_disponiveis:
        raise ValueError(
            f"Tipo '{tipo}' inválido para versão '{version}'. "
            f"Tipos suportados: {list(versoes_disponiveis.keys())}"
        )

    arquivo = SCHEMA_DIR / versoes_disponiveis[tipo]

    if not arquivo.exists():
        raise FileNotFoundError(f"Schema não encontrado: {arquivo}")

    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)


def validar_payload(dados: Dict[str, Any], tipo: str, version: Optional[str] = None) -> None:
    """Valida payload contra o JSON Schema correspondente.

    Args:
        dados: Dict com os dados a validar
        tipo: Identificador do schema (ex: 'request', 'pipeline_state', etc.)
        version: Versão do schema (default: LATEST)

    Raises:
        SchemaValidationError: Se o payload não passar na validação
    """
    schema = carregar_schema(tipo, version)
    schema_name = f"{tipo}_{version or SchemaVersion.LATEST}"

    erros = []
    try:
        validate(instance=dados, schema=schema)
    except JsonSchemaValidationError as e:
        erros.append(e.message)

    if erros:
        raise SchemaValidationError(schema_name, erros)


def validar_request(dados: Dict[str, Any], version: Optional[str] = None) -> None:
    """Valida payload de requisição LLM delegada."""
    validar_payload(dados, "request", version)


def validar_response(dados: Dict[str, Any], version: Optional[str] = None) -> None:
    """Valida payload de resposta LLM delegada."""
    validar_payload(dados, "response", version)


def validar_pipeline_state(dados: Dict[str, Any], version: Optional[str] = None) -> None:
    """Valida payload de estado versionado do pipeline (_pipeline_state.json)."""
    validar_payload(dados, "pipeline_state", version)


def validar_cache(dados: Dict[str, Any], tipo: str, version: Optional[str] = None) -> None:
    """Valida payload de arquivo de cache inter-fases contra o schema correspondente."""
    validar_payload(dados, tipo, version)

