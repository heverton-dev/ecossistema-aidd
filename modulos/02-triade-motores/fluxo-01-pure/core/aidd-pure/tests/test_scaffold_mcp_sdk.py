#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: scaffold MCP gerado pelo Injetor Universal usa o SDK oficial do MCP
(NIH #24 — Fase2-Gen3). Garante que o servidor gerado não reimplementa
JSON-RPC 2.0 à mão e que tools/list + tools/call funcionam via SDK.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

from scripts.core.injector.scaffolds import gerar_mcp


def _executar_codigo_gerado(codigo: str):
    """Compila e executa o código gerado como módulo, retornando o namespace."""
    with tempfile.TemporaryDirectory() as d:
        caminho = Path(d) / "server.py"
        caminho.write_text(codigo, encoding="utf-8")
        namespace = {}
        exec(compile(codigo, str(caminho), "exec"), namespace)
        return namespace


def _extrair_resultado_estruturado(resultado, nome_tool: str):
    import json

    from mcp.types import TextContent

    if isinstance(resultado, tuple):
        structured = resultado[1]
        if isinstance(structured, dict):
            return structured
        resultado = resultado[0]
    blocos = list(resultado) if not isinstance(resultado, list) else resultado
    textos = [b.text for b in blocos if isinstance(b, TextContent)]
    try:
        return json.loads(textos[0]) if textos else {}
    except (json.JSONDecodeError, IndexError):
        raise AssertionError(f"Resultado da tool {nome_tool} não é JSON serializável: {textos}")


class TestScaffoldMCPSDK:
    def test_gerar_mcp_nao_reimplementa_json_rpc(self):
        codigo = gerar_mcp("mcp-teste-nih24", "Servidor de teste do SDK oficial")
        proibidos = [
            "processar_requisicao",
            "sys.stdin",
        ]
        for trecho in proibidos:
            assert trecho not in codigo, f"Scaffold ainda reimplementa JSON-RPC à mão: {trecho}"
        assert "from mcp.server.fastmcp import FastMCP" in codigo
        assert "mcp.run(transport=\"stdio\")" in codigo

    def test_gerar_mcp_python_valido(self):
        codigo = gerar_mcp("mcp-teste-nih24", "Servidor de teste do SDK oficial")
        compile(codigo, "server.py", "exec")

    def test_gerar_mcp_tools_list_via_sdk(self):
        codigo = gerar_mcp("mcp-teste-nih24", "Servidor de teste do SDK oficial")
        namespace = _executar_codigo_gerado(codigo)
        mcp = namespace["mcp"]
        tools = asyncio.run(mcp.list_tools())
        nomes = [t.name for t in tools]
        assert "mcp_teste_nih24" in nomes

    def test_gerar_mcp_tools_call_via_sdk(self):
        codigo = gerar_mcp("mcp-teste-nih24", "Servidor de teste do SDK oficial")
        namespace = _executar_codigo_gerado(codigo)
        mcp = namespace["mcp"]
        resultado = asyncio.run(mcp.call_tool("mcp_teste_nih24", {"consulta": "requests==2.0"}))
        estruturado = _extrair_resultado_estruturado(resultado, "mcp_teste_nih24")
        assert estruturado["servidor"] == "mcp-teste-nih24"
        assert estruturado["consulta_recebida"] == "requests==2.0"
        assert "processado: requests==2.0" in estruturado["resultado"]


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])