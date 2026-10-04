#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_aidd_enterprise (D13)
=============================================================================
Quality Gate Determinístico de contratos de componentes do aidd-enterprise
(Lei #8 / Lei #13). Valida estritamente um manifest de componente:
  1. JSON legível e presente.
  2. Aderência ao JSON Schema canônico component_manifest.schema.json.
  3. SHA-256 declarado confere com a carga útil (content / files / mcp).
  4. Arquivo materializado (`arquivo`) existe e seus bytes batem com o
     SHA-256 declarado (componente adulterado -> reprova).

Critérios de Aceite:
  - Exit 0: manifest 100% conforme (schema + integridade).
  - Exit 1: qualquer violação (componente adulterado, hash divergente,
            schema quebrado, entrada inválida).
=============================================================================
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - dependencia declarada em requirements.txt
    Draft202012Validator = None  # type: ignore[assignment]

ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = (
    ROOT_DIR / "componentes" / "compartilhado" / "injetor" / "schema" / "component_manifest.schema.json"
)


def calcular_sha256(dados: Any) -> str:
    """SHA-256 deterministico de texto, bytes ou objeto JSON canonico."""
    if isinstance(dados, bytes):
        bruto = dados
    elif isinstance(dados, str):
        bruto = dados.encode("utf-8")
    else:
        bruto = json.dumps(dados, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(bruto).hexdigest()


def carga_integridade(payload: dict) -> Any:
    if isinstance(payload.get("content"), str):
        return payload["content"]
    if isinstance(payload.get("files"), dict):
        return payload["files"]
    if isinstance(payload.get("mcp"), dict):
        return payload["mcp"]
    raise ValueError("manifest sem carga util (content, files ou mcp)")


def validar_schema(payload: dict) -> List[str]:
    violacoes: List[str] = []
    if Draft202012Validator is None:
        return ["biblioteca jsonschema indisponivel: validacao de schema impossivel"]
    if not SCHEMA_PATH.is_file():
        return [f"schema canonico ausente: {SCHEMA_PATH}"]
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"schema canonico ilegivel: {exc}"]
    for erro in sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda e: list(e.absolute_path)):
        campo = "/".join(str(p) for p in erro.absolute_path) or "<raiz>"
        violacoes.append(f"schema quebrado em '{campo}': {erro.message}")
    return violacoes


def validar_integridade(payload: dict, diretorio: Path) -> List[str]:
    violacoes: List[str] = []
    declarado = payload.get("sha256")
    if not isinstance(declarado, str) or not declarado:
        violacoes.append("manifest sem campo 'sha256' declarado")
        return violacoes

    try:
        calculado = calcular_sha256(carga_integridade(payload))
    except ValueError as exc:
        violacoes.append(str(exc))
        return violacoes

    if calculado.lower() != declarado.lower():
        violacoes.append(f"SHA-256 divergente: declarado {declarado}, calculado {calculado}")
        return violacoes

    arquivo = payload.get("arquivo")
    if arquivo is None:
        return violacoes
    if not isinstance(arquivo, str) or not arquivo.strip():
        violacoes.append("campo 'arquivo' invalido")
        return violacoes

    caminho = (diretorio / arquivo).resolve()
    try:
        caminho.relative_to(diretorio.resolve())
    except ValueError:
        violacoes.append(f"arquivo fora do diretorio alvo: {caminho}")
        return violacoes

    if not caminho.is_file():
        violacoes.append(f"componente ausente no diretorio alvo: {arquivo}")
        return violacoes

    hash_arquivo = hashlib.sha256(caminho.read_bytes()).hexdigest()
    if hash_arquivo.lower() != declarado.lower():
        violacoes.append(
            f"componente adulterado: SHA-256 do arquivo {hash_arquivo} difere do declarado {declarado}"
        )
    return violacoes


def validar_manifest_arquivo(manifest_path: Path, diretorio: Path) -> Tuple[bool, List[str]]:
    if not manifest_path.is_file():
        return False, [f"manifest inexistente: {manifest_path}"]
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, [f"manifest JSON invalido: {exc}"]
    if not isinstance(payload, dict):
        return False, ["manifest deve ser um objeto JSON"]

    violacoes: List[str] = []
    violacoes.extend(validar_schema(payload))
    violacoes.extend(validar_integridade(payload, diretorio))
    return (not violacoes), violacoes


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python gates/G_aidd_enterprise.py",
        description="Quality Gate determinístico de contratos do aidd-enterprise (D13)",
    )
    parser.add_argument("--manifest", required=True, help="Arquivo JSON do manifest do componente")
    parser.add_argument("--dir", default=".", help="Diretorio alvo dos componentes (padrao: .)")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 1

    aprovado, violacoes = validar_manifest_arquivo(Path(args.manifest).resolve(), Path(args.dir).resolve())
    if aprovado:
        print("[SUCESSO] Quality Gate G_aidd_enterprise APROVADO. EXIT 0")
        return 0
    for violacao in violacoes:
        print(f"[VIOLAÇÃO] {violacao}")
    print("[ERRO] Quality Gate G_aidd_enterprise REPROVADO. EXIT 1")
    return 1


if __name__ == "__main__":
    sys.exit(main())
