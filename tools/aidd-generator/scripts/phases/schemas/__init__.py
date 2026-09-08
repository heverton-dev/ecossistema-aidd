# -*- coding: utf-8 -*-
"""
Schemas versionados do Protocolo Delegado (JSON Schema Draft 2020-12).

Uso:
    from schemas import validar_request, validar_response, SchemaVersion
"""

from .registry import (
    SchemaVersion,
    SCHEMA_DIR,
    carregar_schema,
    validar_request,
    validar_response,
    validar_payload,
)

__all__ = [
    "SchemaVersion",
    "SCHEMA_DIR",
    "carregar_schema",
    "validar_request",
    "validar_response",
    "validar_payload",
]
