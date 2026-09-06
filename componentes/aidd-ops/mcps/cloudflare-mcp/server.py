#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP: Cloudflare MCP (Gestão de DNS de Borda)

Servidor MCP mínimo (JSON-RPC 2.0 sobre stdio, biblioteca padrão apenas urllib.request).
Expõe tools para criar registros A, CNAME e consultar status DNS na Cloudflare.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List

NOME_SERVIDOR = "cloudflare-mcp"
DESCRICAO_SERVIDOR = "Servidor MCP para gerenciamento determinístico de registros DNS na Cloudflare via API REST oficial."
API_BASE = "https://api.cloudflare.com/client/v4"

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "cloudflare_criar_registro_a",
        "description": "Cria um registro DNS do tipo A apontando um hostname para um IPv4.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "zone_id": {"type": "string", "description": "ID da zona DNS na Cloudflare"},
                "name": {"type": "string", "description": "Nome do registro DNS (ex: app.dominio.com ou @)"},
                "content": {"type": "string", "description": "Endereço IPv4 de destino"},
                "proxied": {"type": "boolean", "description": "Se o tráfego deve ser proxied pelo Cloudflare (default: true)", "default": True},
                "ttl": {"type": "integer", "description": "TTL em segundos (1 para automático)", "default": 1}
            },
            "required": ["zone_id", "name", "content"]
        }
    },
    {
        "name": "cloudflare_criar_registro_cname",
        "description": "Cria um registro DNS do tipo CNAME apontando um hostname para outro domínio.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "zone_id": {"type": "string", "description": "ID da zona DNS na Cloudflare"},
                "name": {"type": "string", "description": "Nome do registro DNS (ex: crm.dominio.com)"},
                "content": {"type": "string", "description": "Hostname de destino de destino (ex: app.dominio.com)"},
                "proxied": {"type": "boolean", "description": "Se o tráfego deve ser proxied pelo Cloudflare (default: true)", "default": True},
                "ttl": {"type": "integer", "description": "TTL em segundos (1 para automático)", "default": 1}
            },
            "required": ["zone_id", "name", "content"]
        }
    },
    {
        "name": "cloudflare_consultar_dns",
        "description": "Consulta registros DNS existentes em uma zona filtrando por nome e/ou tipo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "zone_id": {"type": "string", "description": "ID da zona DNS na Cloudflare"},
                "name": {"type": "string", "description": "Nome do registro para filtrar (opcional)"},
                "type": {"type": "string", "description": "Tipo do registro (ex: A, CNAME, TXT) (opcional)"}
            },
            "required": ["zone_id"]
        }
    }
]


def _requisicao_api(metodo: str, endpoint: str, payload: dict = None) -> dict:
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
            filtros.append(f"name={urllib.request.quote(args['name'])}")
        if args.get("type"):
            filtros.append(f"type={urllib.request.quote(args['type'])}")
        query_str = f"?{'&'.join(filtros)}" if filtros else ""
        res = _requisicao_api("GET", f"/zones/{zone_id}/dns_records{query_str}")
        return {"sucesso": res.get("success", False), "registros": res.get("result", []), "erros": res.get("errors", [])}

    raise ValueError(f"Tool desconhecida: {nome_tool}")


def processar_requisicao(req: dict) -> dict:
    metodo = req.get("method")
    req_id = req.get("id")

    if metodo == "initialize":
        resultado = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": NOME_SERVIDOR, "version": "1.0"},
            "capabilities": {"tools": {}},
        }
    elif metodo == "tools/list":
        resultado = {"tools": TOOLS}
    elif metodo == "tools/call":
        params = req.get("params", {})
        resultado = executar_tool(params.get("name"), params.get("arguments", {}))
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Método não suportado: {metodo}"},
        }

    return {"jsonrpc": "2.0", "id": req_id, "result": resultado}


def main():
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            req = json.loads(linha)
            resp = processar_requisicao(req)
        except Exception as exc:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
