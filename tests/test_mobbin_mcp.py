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
        assert "tokens_referencia" in res
        assert res["tokens_referencia"] is not None
        assert "cores" in res["tokens_referencia"]


def test_executar_tool_mobbin_extrair_tokens():
    import componentes.compartilhado.mcps.mobbin_mcp.server as server_mod

    tela_mock = {
        "app_name": "Linear",
        "id": "123",
        "image_url": None
    }

    res = server_mod.executar_tool("mobbin_extrair_tokens", {"tela": tela_mock})
    assert res["sucesso"] is True
    assert "tokens" in res
    assert res["tokens"]["cores"]["modo"] == "dark"
    assert "font_sans" in res["tokens"]["tipografia"]
    assert len(res["tokens"]["regras_craft_floor"]) >= 3


def test_executar_tool_mobbin_compilar_design_system(tmp_path):
    import componentes.compartilhado.mcps.mobbin_mcp.server as server_mod

    tokens_mock = {
        "origem_referencia": {"app_name": "Teste", "screen_id": "456"},
        "cores": {
            "background": "#ffffff",
            "surface": "#f8fafc",
            "primary": "#0f172a",
            "foreground": "#0f172a",
            "muted": "#64748b",
            "border": "rgba(0,0,0,0.1)"
        },
        "tipografia": {
            "font_sans": "Public Sans",
            "font_mono": "JetBrains Mono",
            "escala": {"base": "14px"}
        },
        "espacamentos": {"grid_base": "4px"},
        "raios_borda": {"btn": "6px"}
    }

    res = server_mod.executar_tool("mobbin_compilar_design_system", {
        "tokens": tokens_mock,
        "saida_dir": str(tmp_path)
    })

    assert res["sucesso"] is True
    assert "arquivos" in res
    assert (tmp_path / "theme-tokens.json").exists()
    assert (tmp_path / "design-system.css").exists()
    conteudo_css = (tmp_path / "design-system.css").read_text(encoding="utf-8")
    assert "--color-primary: #0f172a;" in conteudo_css
    assert ".btn-primary" in conteudo_css
