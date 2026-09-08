#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP: Mcp Verificador Cve

Servidor MCP que expoe uma tool de consulta simulada de CVEs conhecidas para pacotes Python informados pelo nome, como apoio a auditoria de seguranca de dependencias.

Servidor MCP que usa o SDK oficial do Model Context Protocol (`modelcontextprotocol/python-sdk`).
Gerado pelo Injetor Universal de Componentes (aidd-generator).

Uso:
    python server.py
    (transporte stdio; JSON-RPC 2.0, negociacao de protocolo e codigos de
    erro tratados pelo SDK oficial)
"""

from mcp.server.fastmcp import FastMCP

NOME_SERVIDOR = "mcp-verificador-cve"
DESCRICAO_SERVIDOR = 'Servidor MCP que expoe uma tool de consulta simulada de CVEs conhecidas para pacotes Python informados pelo nome, como apoio a auditoria de seguranca de dependencias.'

mcp = FastMCP(NOME_SERVIDOR, instructions=DESCRICAO_SERVIDOR)


@mcp.tool()
def mcp_verificador_cve(consulta: str) -> dict:
    """Servidor MCP que expoe uma tool de consulta simulada de CVEs conhecidas para pacotes Python informados pelo nome, como apoio a auditoria de seguranca de dependencias."""
    return {
        "servidor": NOME_SERVIDOR,
        "consulta_recebida": consulta,
        "resultado": f"[{NOME_SERVIDOR}] processado: {consulta}",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")