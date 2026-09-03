#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP: Mcp Verificador Cve

Servidor MCP que expoe uma tool de consulta simulada de CVEs conhecidas para pacotes Python informados pelo nome, como apoio a auditoria de seguranca de dependencias.

Servidor MCP minimo (JSON-RPC 2.0 sobre stdio, biblioteca padrao apenas).
Gerado pelo Injetor Universal de Componentes (aidd-generator).

Uso:
    python server.py
    (le requisicoes JSON-RPC, uma por linha, de stdin; escreve respostas
    JSON-RPC, uma por linha, em stdout)
"""

import json
import sys

NOME_SERVIDOR = "mcp-verificador-cve"
DESCRICAO_SERVIDOR = 'Servidor MCP que expoe uma tool de consulta simulada de CVEs conhecidas para pacotes Python informados pelo nome, como apoio a auditoria de seguranca de dependencias.'

TOOLS = [
    {
        "name": "mcp_verificador_cve",
        "description": DESCRICAO_SERVIDOR,
        "inputSchema": {
            "type": "object",
            "properties": {
                "consulta": {"type": "string", "description": "Entrada da consulta"}
            },
            "required": ["consulta"],
        },
    }
]


def executar_tool(nome_tool_chamada, argumentos):
    """Executa a unica tool exposta por este servidor."""
    if nome_tool_chamada != "mcp_verificador_cve":
        raise ValueError(f"tool desconhecida: {nome_tool_chamada}")

    consulta = argumentos.get("consulta", "")
    return {
        "servidor": NOME_SERVIDOR,
        "consulta_recebida": consulta,
        "resultado": f"[{NOME_SERVIDOR}] processado: {consulta}",
    }


def processar_requisicao(req):
    """Processa uma unica requisicao JSON-RPC 2.0 e devolve a resposta."""
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
            "error": {"code": -32601, "message": f"metodo nao suportado: {metodo}"},
        }

    return {"jsonrpc": "2.0", "id": req_id, "result": resultado}


def main():
    """Loop principal: le requisicoes de stdin, escreve respostas em stdout."""
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            req = json.loads(linha)
            resp = processar_requisicao(req)
        except (json.JSONDecodeError, ValueError) as exc:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
