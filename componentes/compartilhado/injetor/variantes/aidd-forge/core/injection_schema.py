"""Validador do contrato universal de injecao (Draft 2020-12), zero dependencias.

Le `aidd_forge/schemas/injection_request.schema.json` como fonte da verdade e
aplica as poucas palavras-chave usadas por esse contrato (`type`, `enum`,
`pattern`, `minLength`, `required`, `additionalProperties`) sem depender da
biblioteca externa `jsonschema` — mecanica pura, custo zero de tokens.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "injection_request.schema.json"

_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "object": dict,
    "array": list,
    "boolean": bool,
}


@dataclass
class SchemaValidationResult:
    """Resumo da validacao de um payload contra o contrato de injecao."""

    valid: bool
    errors: list[str] = field(default_factory=list)


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate_property(name: str, value: Any, rules: dict[str, Any], errors: list[str]) -> None:
    expected_type = rules.get("type")
    if expected_type is not None:
        python_type = _TYPE_MAP[expected_type]
        if python_type is int and isinstance(value, bool):
            errors.append(f"'{name}': esperado tipo 'integer', recebido 'boolean'")
            return
        if not isinstance(value, python_type):
            errors.append(f"'{name}': esperado tipo '{expected_type}', recebido '{type(value).__name__}'")
            return

    if "enum" in rules and value not in rules["enum"]:
        errors.append(f"'{name}': valor '{value}' fora do enum permitido {rules['enum']}")

    if "pattern" in rules and isinstance(value, str) and not re.match(rules["pattern"], value):
        errors.append(f"'{name}': valor '{value}' nao casa com o padrao '{rules['pattern']}'")

    if "minLength" in rules and isinstance(value, str) and len(value) < rules["minLength"]:
        errors.append(f"'{name}': deve ter ao menos {rules['minLength']} caractere(s)")


def validate_request(payload: dict[str, Any]) -> SchemaValidationResult:
    """Valida `payload` contra o contrato universal de injecao."""
    schema = _load_schema()
    properties: dict[str, Any] = schema.get("properties", {})
    required: list[str] = schema.get("required", [])
    additional_allowed = schema.get("additionalProperties", True)

    errors: list[str] = []

    if not isinstance(payload, dict):
        return SchemaValidationResult(valid=False, errors=["payload deve ser um objeto JSON"])

    for field_name in required:
        if field_name not in payload:
            errors.append(f"campo obrigatorio ausente: '{field_name}'")

    for name, value in payload.items():
        if name not in properties:
            if not additional_allowed:
                errors.append(f"campo desconhecido: '{name}'")
            continue
        _validate_property(name, value, properties[name], errors)

    return SchemaValidationResult(valid=not errors, errors=errors)
