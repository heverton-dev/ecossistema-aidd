# -*- coding: utf-8 -*-
"""Pacote contratos — Verificação e integridade SHA-256 de artefatos de handoff."""
from .validador_sha256 import (
    calcular_sha256_payload,
    validar_integridade_contrato,
    assinar_contrato_payload,
)

__all__ = [
    "calcular_sha256_payload",
    "validar_integridade_contrato",
    "assinar_contrato_payload",
]
