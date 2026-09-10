# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — Validação do Contrato PLANO-INFRAESTRUTURA.json (Item 5)
=============================================================================
Validação DETERMINÍSTICA (jsonschema) do plano gerado pelas Fases 1-3 contra
o schema canônico versionado em:

    componentes/compartilhado/specs/plano-infraestrutura.schema.json

Fonte única do contrato (aidd-ops = produtor; aidd-master/aidd-enterprise =
consumidores via scaffold_infra.py). O schema aceita tanto planos com sucesso
em todas as fases quanto planos com falha estruturada de fase (saida=None +
erro=to_dict), cobrindo o early-exit legítimo do pipeline.

Regra de Ouro #1 (Determinismo): nenhuma decisão via LLM — parsing mecânico
via biblioteca jsonschema.
"""

import json
import os
import sys
from typing import Dict

# Garantir que src/ está no path (mesmo padrão de pipeline_ops.py)
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOL_ROOT = os.path.dirname(_SCRIPTS_DIR)
sys.path.insert(0, os.path.join(_TOOL_ROOT, "src"))

from core.result import Result  # noqa: E402

from jsonschema import ValidationError, validate  # noqa: E402

_RAIZ_ECOSSISTEMA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
SCHEMA_CONTRATO_PATH = os.path.join(
    _RAIZ_ECOSSISTEMA,
    "componentes",
    "compartilhado",
    "specs",
    "plano-infraestrutura.schema.json",
)


def caminho_schema_contrato() -> str:
    """Caminho absoluto do schema canônico do contrato."""
    return SCHEMA_CONTRATO_PATH


def carregar_schema_contrato() -> Dict:
    """Carrega o schema canônico do contrato como dict.

    Returns:
        Dict do JSON Schema Draft 2020-12.

    Raises:
        FileNotFoundError: se o schema canônico não existir (quebra de
            instalação — o contrato é parte do repositório).
        json.JSONDecodeError: se o schema estiver corrompido.
    """
    with open(SCHEMA_CONTRATO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validar_plano_contrato(plano: dict) -> Result:
    """Valida um plano de infraestrutura contra o schema canônico.

    Args:
        plano: Dict do PLANO-INFRAESTRUTURA produzido pelas Fases 1-3.

    Returns:
        Result.ok(plano) se 100% aderente;
        Result.fail(..., codigo="PLANO_INVALIDO_CONTRATO") caso contrário,
        com `erros` no detalhes (caminhos dos pontos de falha).
    """
    try:
        schema = carregar_schema_contrato()
    except FileNotFoundError as exc:
        return Result.fail(
            f"Schema canônico do contrato não encontrado: {SCHEMA_CONTRATO_PATH}",
            codigo="SCHEMA_CONTRATO_AUSENTE",
        )
    except json.JSONDecodeError as exc:
        return Result.fail(
            f"Schema canônico do contrato corrompido (JSON inválido): {exc}",
            codigo="SCHEMA_CONTRATO_CORROMPIDO",
        )

    try:
        validate(instance=plano, schema=schema)
    except ValidationError as exc:
        return Result.fail(
            f"Plano não adere ao contrato: {exc.message}",
            codigo="PLANO_INVALIDO_CONTRATO",
            detalhes={"caminho": list(exc.path), "erros": [exc.message]},
        )
    return Result.ok(plano)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Valida PLANO-INFRAESTRUTURA.json contra o schema canônico do Item 5."
    )
    parser.add_argument("plano", help="Caminho do PLANO-INFRAESTRUTURA.json a validar")
    args = parser.parse_args()

    try:
        with open(args.plano, "r", encoding="utf-8") as f:
            plano_dados = json.load(f)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {args.plano}")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"[ERRO] JSON inválido: {exc}")
        sys.exit(1)

    resultado = validar_plano_contrato(plano_dados)
    if resultado.sucesso:
        print(f"[OK] {args.plano} está 100% aderente ao contrato ({SCHEMA_CONTRATO_PATH})")
        sys.exit(0)
    print(f"[ERRO] {resultado.codigo}: {resultado.erro}")
    if resultado.detalhes:
        print(f"Detalhes: {json.dumps(resultado.detalhes, ensure_ascii=False)}")
    sys.exit(1)