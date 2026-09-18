# -*- coding: utf-8 -*-
"""Testes unitários para o Quality Gate G_PROTOCOL_FALLBACK."""

import json
import os
import subprocess
import sys
import tempfile
import pytest

from gates.G_PROTOCOL_FALLBACK import verificar_paridade_contratos, scan_protocol_fallbacks, main


def test_paridade_contratos_sucesso(tmp_path):
    swagger_file = tmp_path / "swagger_spec.json"
    mcp_file = tmp_path / "mcp_studio.json"

    swagger_data = {
        "paths": {
            "/clientes": {
                "get": {"operationId": "listar_clientes"},
                "post": {"operationId": "criar_cliente"}
            },
            "/pedidos/{id}": {
                "get": {"operationId": "obter_pedido"}
            }
        }
    }
    mcp_data = {
        "tools": [
            {"name": "listar_clientes", "description": "Lista todos os clientes"},
            {"name": "criar-cliente", "description": "Cria um novo cliente"},
            {"name": "obter_pedido", "description": "Busca pedido por id"}
        ]
    }

    swagger_file.write_text(json.dumps(swagger_data), encoding="utf-8")
    mcp_file.write_text(json.dumps(mcp_data), encoding="utf-8")

    erros = verificar_paridade_contratos(str(swagger_file), str(mcp_file))
    assert erros == []


def test_paridade_contratos_detecta_tool_orfa(tmp_path):
    swagger_file = tmp_path / "swagger_spec.json"
    mcp_file = tmp_path / "mcp_studio.json"

    swagger_data = {
        "paths": {
            "/clientes": {
                "get": {"operationId": "listar_clientes"}
            }
        }
    }
    mcp_data = {
        "tools": [
            {"name": "listar_clientes", "description": "Lista clientes"},
            {"name": "deletar_base_dados_secreta", "description": "Ação perigosa sem rota REST"}
        ]
    }

    swagger_file.write_text(json.dumps(swagger_data), encoding="utf-8")
    mcp_file.write_text(json.dumps(mcp_data), encoding="utf-8")

    erros = verificar_paridade_contratos(str(swagger_file), str(mcp_file))
    assert len(erros) == 1
    assert "deletar_base_dados_secreta" in erros[0]


def test_paridade_contratos_arquivo_inexistente(tmp_path):
    erros = verificar_paridade_contratos(
        str(tmp_path / "inexistente_sw.json"),
        str(tmp_path / "inexistente_mcp.json")
    )
    assert erros == []


def test_paridade_contratos_json_corrompido(tmp_path):
    swagger_file = tmp_path / "swagger_spec.json"
    mcp_file = tmp_path / "mcp_studio.json"

    swagger_file.write_text("{conteudo invalido json", encoding="utf-8")
    mcp_file.write_text("{}", encoding="utf-8")

    erros = verificar_paridade_contratos(str(swagger_file), str(mcp_file))
    assert len(erros) == 1
    assert "Erro ao carregar arquivos de contrato" in erros[0]


def test_scan_protocol_fallbacks_ignora_pastas_especiais(tmp_path):
    pasta_git = tmp_path / ".git"
    pasta_git.mkdir()
    (pasta_git / "swagger_spec.json").write_text("{}", encoding="utf-8")
    (pasta_git / "mcp_studio.json").write_text("{}", encoding="utf-8")

    erros = scan_protocol_fallbacks(str(tmp_path))
    assert erros == []
