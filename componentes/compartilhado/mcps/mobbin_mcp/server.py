#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP: Mobbin MCP (Servidor de Busca de Interfaces de Referência)

Exõe a busca determinística de telas do Mobbin via Model Context Protocol (FastMCP)
para qualquer harness (Claude, OpenCode, MiMo, Cursor, etc.).
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Garante import do ecossistema e do aidd_forge
ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
FORGE_DIR = ROOT_DIR / "tools" / "aidd-forge"
if str(FORGE_DIR) not in sys.path:
    sys.path.insert(0, str(FORGE_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env", override=False)
except ImportError:
    pass

from aidd_forge.core.mobbin_client import executar_busca

NOME_SERVIDOR = "mobbin-mcp"
DESCRICAO_SERVIDOR = "Servidor MCP para busca determinística de telas de design no Mobbin."

mcp = FastMCP(NOME_SERVIDOR, instructions=DESCRICAO_SERVIDOR)


def executar_tool(nome_tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Roteia e executa a tool MCP solicitada."""
    if nome_tool == "mobbin_buscar_telas":
        query = args.get("query", "").strip()
        if not query:
            return {"sucesso": False, "erro": "O parâmetro 'query' é obrigatório."}

        platform = args.get("platform", "web")
        mode = args.get("mode", "standard")
        limit = args.get("limit", 10)

        try:
            res = executar_busca(query=query, platform=platform, mode=mode, limit=limit)
            return {"sucesso": True, "screens": res.get("screens", []), "raw": res}
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    raise ValueError(f"Tool desconhecida: {nome_tool}")


@mcp.tool()
def mobbin_buscar_telas(query: str, platform: str = "web", mode: str = "standard", limit: int = 10) -> Dict[str, Any]:
    """Busca telas reais de UI no Mobbin com base em palavras-chave ou requisitos visuais."""
    return executar_tool("mobbin_buscar_telas", {
        "query": query,
        "platform": platform,
        "mode": mode,
        "limit": limit
    })


if __name__ == "__main__":
    mcp.run()
