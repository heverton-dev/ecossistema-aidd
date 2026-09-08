#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP: Cloudflare MCP (Gestão de DNS de Borda)

Servidor MCP que usa o SDK oficial do Model Context Protocol
(`modelcontextprotocol/python-sdk`). Expose tools para criar registros A,
CNAME e consultar status DNS na Cloudflare.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

try:
    from dotenv import load_dotenv
    # Este arquivo vive 4 niveis abaixo da raiz do ecossistema tanto na fonte
    # (componentes/aidd-ops/mcps/cloudflare-mcp/) quanto no destino sincronizado
    # (tools/aidd-ops/mcps/cloudflare-mcp/) — mesma profundidade nas duas copias.
    load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=False)
except ImportError:
    pass  # python-dotenv ausente no venv que sobe este MCP: segue só com o shell env.

NOME_SERVIDOR = "cloudflare-mcp"
DESCRICAO_SERVIDOR = "Servidor MCP para gerenciamento determinístico de registros DNS na Cloudflare via API REST oficial."
API_BASE = "https://api.cloudflare.com/client/v4"

mcp = FastMCP(NOME_SERVIDOR, instructions=DESCRICAO_SERVIDOR)


def _requisicao_api(metodo: str, endpoint: str, payload: Optional[dict] = None) -> dict:
    """Executa requisição HTTP autenticada à API da Cloudflare usando urllib."""
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token or not token.strip():
        raise RuntimeError("Variável de ambiente CLOUDFLARE_API_TOKEN não configurada")

    url = f"{API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None

    req = urllib.request.Request(url, data=data, headers=headers, method=metodo)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            corpo = resp.read().decode("utf-8")
            return json.loads(corpo)
    except urllib.error.HTTPError as e:
        detalhes = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(detalhes)
        except Exception:
            return {"success": False, "errors": [{"code": e.code, "message": str(e), "detail": detalhes}]}
    except urllib.error.URLError as e:
        return {"success": False, "errors": [{"code": "NETWORK_ERROR", "message": str(e.reason)}]}


def executar_tool(nome_tool: str, args: dict) -> dict:
    """Roteia e executa a tool MCP solicitada."""
    zone_id = args.get("zone_id", "").strip()
    if not zone_id:
        return {"sucesso": False, "erro": "zone_id é obrigatório"}

    if nome_tool == "cloudflare_criar_registro_a":
        payload = {
            "type": "A",
            "name": args.get("name"),
            "content": args.get("content"),
            "ttl": args.get("ttl", 1),
            "proxied": args.get("proxied", True),
        }
        res = _requisicao_api("POST", f"/zones/{zone_id}/dns_records", payload)
        return {"sucesso": res.get("success", False), "dados": res.get("result"), "erros": res.get("errors", [])}

    elif nome_tool == "cloudflare_criar_registro_cname":
        payload = {
            "type": "CNAME",
            "name": args.get("name"),
            "content": args.get("content"),
            "ttl": args.get("ttl", 1),
            "proxied": args.get("proxied", True),
        }
        res = _requisicao_api("POST", f"/zones/{zone_id}/dns_records", payload)
        return {"sucesso": res.get("success", False), "dados": res.get("result"), "erros": res.get("errors", [])}

    elif nome_tool == "cloudflare_consultar_dns":
        filtros = []
        if args.get("name"):
            filtros.append(f"name={urllib.parse.quote(args['name'])}")
        if args.get("type"):
            filtros.append(f"type={urllib.parse.quote(args['type'])}")
        query_str = f"?{'&'.join(filtros)}" if filtros else ""
        res = _requisicao_api("GET", f"/zones/{zone_id}/dns_records{query_str}")
        return {"sucesso": res.get("success", False), "registros": res.get("result", []), "erros": res.get("errors", [])}

    raise ValueError(f"Tool desconhecida: {nome_tool}")


@mcp.tool()
def cloudflare_criar_registro_a(zone_id: str, name: str, content: str, proxied: bool = True, ttl: int = 1) -> dict:
    """Cria um registro DNS do tipo A apontando um hostname para um IPv4."""
    return executar_tool("cloudflare_criar_registro_a", {
        "zone_id": zone_id, "name": name, "content": content, "proxied": proxied, "ttl": ttl,
    })


@mcp.tool()
def cloudflare_criar_registro_cname(zone_id: str, name: str, content: str, proxied: bool = True, ttl: int = 1) -> dict:
    """Cria um registro DNS do tipo CNAME apontando um hostname para outro domínio."""
    return executar_tool("cloudflare_criar_registro_cname", {
        "zone_id": zone_id, "name": name, "content": content, "proxied": proxied, "ttl": ttl,
    })


@mcp.tool()
def cloudflare_consultar_dns(zone_id: str, name: Optional[str] = None, type: Optional[str] = None) -> dict:
    """Consulta registros DNS existentes em uma zona filtrando por nome e/ou tipo."""
    return executar_tool("cloudflare_consultar_dns", {
        "zone_id": zone_id, "name": name or "", "type": type or "",
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")