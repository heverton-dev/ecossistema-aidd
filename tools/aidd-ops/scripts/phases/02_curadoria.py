# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops MVP — Fase 2: Curadoria e Seleção da Stack
=============================================================================
Lookup direto em data/catalogo_nichos.json para retornar a lista de
ferramentas open-source associadas ao nicho reconhecido na Fase 1.
Valida o resultado contra schemas/schema_stack_selecionada.json.

100% determinístico — zero LLM, zero síntese criativa.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from core.result import Result

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "schemas")


def _carregar_catalogo() -> Dict[str, Any]:
    caminho = os.path.join(_DATA_DIR, "catalogo_nichos.json")
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _carregar_schema_stack() -> Dict[str, Any]:
    caminho = os.path.join(_SCHEMAS_DIR, "schema_stack_selecionada.json")
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _validar_campos_obrigatorios(dados: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validação manual de campos obrigatórios do JSON Schema (sem dependência externa)."""
    erros: List[str] = []
    for campo in schema.get("required", []):
        if campo not in dados:
            erros.append(f"Campo obrigatório ausente: '{campo}'")
    return erros


def curar_stack(nicho_slug: str, nicho_nome_exibicao: str) -> Result:
    """Retorna a stack de ferramentas para o nicho especificado.

    Args:
        nicho_slug: Slug do nicho (ex: "clinicas").
        nicho_nome_exibicao: Nome de exibição (ex: "Clínicas & Odontologia").

    Returns:
        Result.ok(stack_selecionada) ou Result.fail(NICHO_SEM_STACK).
    """
    catalogo = _carregar_catalogo()
    schema = _carregar_schema_stack()

    nichos = catalogo.get("nichos", [])
    nicho_encontrado = None
    for n in nichos:
        if n["slug"] == nicho_slug:
            nicho_encontrado = n
            break

    if nicho_encontrado is None:
        return Result.fail(
            f"Nicho '{nicho_slug}' não encontrado no catálogo.",
            codigo="NICHO_SEM_STACK",
            detalhes={"nicho_slug": nicho_slug, "slugs_disponiveis": [n["slug"] for n in nichos]},
        )

    ferramentas_raw = nicho_encontrado.get("ferramentas", [])
    if not ferramentas_raw:
        return Result.fail(
            f"Nicho '{nicho_slug}' não possui ferramentas catalogadas.",
            codigo="NICHO_SEM_STACK",
        )

    # Montar payload conforme schema
    stack_selecionada = {
        "nicho_slug": nicho_slug,
        "nicho_nome_exibicao": nicho_nome_exibicao,
        "ferramentas": [{"nome": f["nome"]} for f in ferramentas_raw],
    }

    # Validar contra schema
    erros_validacao = _validar_campos_obrigatorios(stack_selecionada, schema)
    if erros_validacao:
        return Result.fail(
            "Stack selecionada não passa na validação do schema.",
            codigo="SCHEMA_VALIDATION_ERROR",
            detalhes={"erros": erros_validacao},
        )

    return Result.ok(stack_selecionada)
