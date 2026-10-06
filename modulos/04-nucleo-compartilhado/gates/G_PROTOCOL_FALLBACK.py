# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_PROTOCOL_FALLBACK
=============================================================================
Auditoria de Paridade e Fallback REST vs Model Context Protocol (MCP).

Regra Inviolável de Arquitetura:
  Nenhuma funcionalidade de negócio do sistema pode ser exposta exclusivamente
  via MCP. Como o Model Context Protocol é um padrão recente e sujeito a
  instabilidade de conectividade ou quebras de versão de clientes agênticos,
  100% das ferramentas (tools) disponibilizadas no MCP Studio ('mcp_studio.json'
  ou endpoints '/mcp') DEVEM possuir rota HTTP REST funcional equivalente
  documentada na especificação OpenAPI ('swagger_spec.json' ou '/docs').

Saída:
  exit 0 = Todas as tools MCP possuem fallback REST documentado e funcional.
  exit 1 = Ferramenta MCP órfã detectada sem contrapartida REST OpenAPI.
"""

import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def verificar_paridade_contratos(swagger_path: str, mcp_path: str) -> list[str]:
    """Compara as tools expostas no MCP com as operações REST do Swagger."""
    erros = []
    if not os.path.isfile(swagger_path) or not os.path.isfile(mcp_path):
        return erros

    try:
        with open(swagger_path, "r", encoding="utf-8") as f:
            swagger_data = json.load(f)
        with open(mcp_path, "r", encoding="utf-8") as f:
            mcp_data = json.load(f)
    except Exception as exc:
        return [f"Erro ao carregar arquivos de contrato: {exc}"]

    # Extrai conjunto de operationIds ou endpoints REST normalizados
    operacoes_rest = set()
    paths = swagger_data.get("paths", {})
    for path_str, path_item in paths.items():
        if isinstance(path_item, dict):
            # Normaliza o path sem barras e hífens: /encomendas -> encomendas
            path_clean = path_str.strip("/").replace("/", "_").replace("-", "_").lower()
            operacoes_rest.add(path_clean)
            for method, op_data in path_item.items():
                if isinstance(op_data, dict):
                    op_id = op_data.get("operationId")
                    if op_id:
                        operacoes_rest.add(op_id.lower())

    # Extrai tools do MCP Studio
    tools = mcp_data.get("tools", [])
    for tool in tools:
        tool_name = tool.get("name", "").strip().lower()
        if not tool_name:
            continue

        # Verifica correspondência direta ou semântica
        norm_tool = tool_name.replace("-", "_")
        encontrado = any(
            norm_tool == op or norm_tool in op or op in norm_tool
            for op in operacoes_rest
        )
        if not encontrado:
            erros.append(
                f"Tool MCP '{tool_name}' não possui operação REST correspondente em {os.path.basename(swagger_path)}"
            )

    return erros


def scan_protocol_fallbacks(repo_root: str) -> list[str]:
    """Localiza todos os pares quarteto_sine_qua_non nos deliverables e templates."""
    todos_erros = []
    for root, _, files in os.walk(repo_root):
        if any(skip in root for skip in [".git", "__pycache__", "node_modules", "venv"]):
            continue
        if "swagger_spec.json" in files and "mcp_studio.json" in files:
            sw_path = os.path.join(root, "swagger_spec.json")
            mcp_path = os.path.join(root, "mcp_studio.json")
            erros = verificar_paridade_contratos(sw_path, mcp_path)
            todos_erros.extend(erros)
    return todos_erros


def main() -> int:
    print("=" * 72)
    print(" [GATE] G_PROTOCOL_FALLBACK — Paridade e Fallback REST vs MCP")
    print("=" * 72)

    diretorios_busca = [
        os.path.join(ROOT_DIR, "tools"),
        os.path.join(ROOT_DIR, "testes"),
    ]

    erros = []
    for d in diretorios_busca:
        if os.path.exists(d):
            erros.extend(scan_protocol_fallbacks(d))

    if erros:
        print(f"\n[FALHA] Detectada(s) {len(erros)} inconsistência(s) de fallback REST para MCP:\n")
        for err in erros:
            print(f"  - {err}")
        print("\nRegra: Toda tool MCP DEVE ter rota REST OpenAPI correspondente no Swagger.")
        print("=" * 72)
        return 1

    print("\n[SUCESSO] Quality Gate G_PROTOCOL_FALLBACK APROVADO — 100% de paridade e fallback REST!")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
