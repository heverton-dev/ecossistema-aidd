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
FORGE_DIR = ROOT_DIR / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-forge"
if str(FORGE_DIR) not in sys.path:
    sys.path.insert(0, str(FORGE_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env", override=False)
except ImportError:
    pass

try:
    from aidd_forge.core.mobbin_client import executar_busca
except ImportError:
    try:
        from aidd_planner.core.mobbin_client import executar_busca
    except ImportError:
        _planner_src = ROOT_DIR / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-planner" / "src"
        if str(_planner_src) not in sys.path:
            sys.path.insert(0, str(_planner_src))
        from core.mobbin_client import executar_busca
from componentes.compartilhado.mcps.mobbin_mcp.token_extractor import extrair_tokens_mobbin
from componentes.compartilhado.mcps.mobbin_mcp.theme_compiler import compilar_contrato_design

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
            screens = res.get("screens", [])
            # Extrai tokens determinísticos se houver telas retornadas
            tokens = extrair_tokens_mobbin(screens[0]) if screens else None
            return {"sucesso": True, "screens": screens, "tokens_referencia": tokens, "raw": res}
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    if nome_tool == "mobbin_extrair_tokens":
        tela = args.get("tela")
        if not tela:
            return {"sucesso": False, "erro": "O parâmetro 'tela' é obrigatório."}
        try:
            tokens = extrair_tokens_mobbin(tela)
            return {"sucesso": True, "tokens": tokens}
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    if nome_tool == "mobbin_compilar_design_system":
        tokens = args.get("tokens")
        saida = args.get("saida_dir")
        if not tokens or not saida:
            return {"sucesso": False, "erro": "Parâmetros 'tokens' e 'saida_dir' são obrigatórios."}
        try:
            res = compilar_contrato_design(tokens, Path(saida))
            return {
                "sucesso": True,
                "arquivos": {
                    "json": str(res["json"]),
                    "css": str(res["css"])
                }
            }
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


@mcp.tool()
def mobbin_extrair_tokens(tela: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai design tokens determinísticos (paleta, tipografia, bordas) a partir de uma tela do Mobbin."""
    return executar_tool("mobbin_extrair_tokens", {"tela": tela})


@mcp.tool()
def mobbin_compilar_design_system(tokens: Dict[str, Any], saida_dir: str) -> Dict[str, Any]:
    """Gera os arquivos de contrato global (theme-tokens.json e design-system.css) para harmonia estrita do app."""
    return executar_tool("mobbin_compilar_design_system", {"tokens": tokens, "saida_dir": saida_dir})


if __name__ == "__main__":
    mcp.run()
