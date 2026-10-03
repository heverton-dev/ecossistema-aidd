# -*- coding: utf-8 -*-
"""Testes TDD para o servidor local Mobbin MCP."""
import pytest
from unittest.mock import patch

def test_executar_tool_mobbin_buscar_telas():
    import componentes.compartilhado.mcps.mobbin_mcp.server as server_mod

    mock_resp = {
        "screens": [
            {
                "app_name": "Stripe",
                "name": "Checkout",
                "url": "https://mobbin.com/screens/1",
                "image_url": "https://img.mobbin.com/1.png"
            }
        ]
    }

    with patch.object(server_mod, "executar_busca", return_value=mock_resp):
        res = server_mod.executar_tool("mobbin_buscar_telas", {
            "query": "checkout stripe",
            "platform": "web",
            "mode": "standard",
            "limit": 5
        })

        assert res["sucesso"] is True
        assert len(res["screens"]) == 1
        assert res["screens"][0]["app_name"] == "Stripe"
