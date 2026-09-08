"""
Testes unitários herméticos para os servidores MCP do aidd-ops:
- cloudflare-mcp (criação e consulta DNS com urllib mockado)
- docker-mcp (leitura de compose, status e logs com subprocess/shutil mockados)

Os servidores usam o SDK oficial do MCP (`mcp.server.fastmcp.FastMCP`).
As asserções de protocolo usam `FastMCP.list_tools()` e `FastMCP.call_tool()`,
enquanto as de lógica de negócio continuam exercitando `executar_tool` com
os mesmos mocks (urllib/subprocess/shutil).
"""

import asyncio
import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def carregar_modulo(nome_modulo: str, caminho_arquivo: Path):
    spec = importlib.util.spec_from_file_location(nome_modulo, caminho_arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cf_server = carregar_modulo(
    "cloudflare_mcp_server",
    REPO_ROOT / "componentes" / "aidd-ops" / "mcps" / "cloudflare-mcp" / "server.py",
)
docker_server = carregar_modulo(
    "docker_mcp_server",
    REPO_ROOT / "componentes" / "aidd-ops" / "mcps" / "docker-mcp" / "server.py",
)


class TestCloudflareMCP(unittest.TestCase):
    def setUp(self):
        self.patcher = patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "mock_token_12345"})
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_list_tools_via_sdk(self):
        names = asyncio.run(_list_tool_names(cf_server.mcp))
        self.assertIn("cloudflare_criar_registro_a", names)
        self.assertIn("cloudflare_criar_registro_cname", names)
        self.assertIn("cloudflare_consultar_dns", names)

    @patch.object(cf_server.urllib.request, "urlopen")
    def test_create_dns_record_a_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "success": True,
            "errors": [],
            "result": {"id": "rec_123", "name": "app.example.com", "type": "A", "content": "1.2.3.4"}
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = asyncio.run(_run_tool(cf_server.mcp, "cloudflare_criar_registro_a", {
            "zone_id": "zone_abc",
            "name": "app.example.com",
            "content": "1.2.3.4"
        }))

        self.assertTrue(res["sucesso"])
        self.assertEqual(res["dados"]["id"], "rec_123")

    @patch.object(cf_server.urllib.request, "urlopen")
    def test_create_dns_record_cname_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "success": True,
            "errors": [],
            "result": {"id": "cname_123", "name": "crm.example.com", "type": "CNAME", "content": "app.example.com"}
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = asyncio.run(_run_tool(cf_server.mcp, "cloudflare_criar_registro_cname", {
            "zone_id": "zone_abc",
            "name": "crm.example.com",
            "content": "app.example.com"
        }))

        self.assertTrue(res["sucesso"])
        self.assertEqual(res["dados"]["id"], "cname_123")

    def test_create_dns_record_missing_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                cf_server.executar_tool("cloudflare_criar_registro_a", {
                    "zone_id": "zone_abc",
                    "name": "app.example.com",
                    "content": "1.2.3.4"
                })
            self.assertIn("CLOUDFLARE_API_TOKEN", str(ctx.exception))

    @patch.object(cf_server.urllib.request, "urlopen")
    def test_consultar_dns_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "success": True,
            "errors": [],
            "result": [
                {"id": "rec_1", "name": "app.example.com", "type": "A", "content": "1.2.3.4"}
            ]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = asyncio.run(_run_tool(cf_server.mcp, "cloudflare_consultar_dns", {
            "zone_id": "zone_abc",
            "name": "app.example.com"
        }))
        self.assertTrue(res["sucesso"])
        self.assertEqual(len(res["registros"]), 1)


class TestDockerMCP(unittest.TestCase):
    def test_list_tools_via_sdk(self):
        names = asyncio.run(_list_tool_names(docker_server.mcp))
        self.assertIn("docker_compose_config", names)
        self.assertIn("docker_status_conteineres", names)
        self.assertIn("docker_logs", names)

    @patch.object(docker_server.os.path, "exists", return_value=True)
    @patch.object(docker_server.shutil, "which", return_value="/usr/bin/docker")
    @patch.object(docker_server.subprocess, "run")
    def test_docker_compose_config(self, mock_run, mock_which, mock_exists):
        mock_run.return_value = MagicMock(returncode=0, stdout="services:\n  web:\n    image: nginx", stderr="")
        res = asyncio.run(_run_tool(docker_server.mcp, "docker_compose_config", {
            "compose_path": "docker-compose.yml"
        }))
        self.assertTrue(res["sucesso"])
        self.assertIn("nginx", res["stdout"])

    @patch.object(docker_server.shutil, "which", return_value="/usr/bin/docker")
    @patch.object(docker_server.subprocess, "run")
    def test_docker_ps(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0, stdout='[{"ID":"123","Names":"traefik"}]', stderr="")
        res = asyncio.run(_run_tool(docker_server.mcp, "docker_status_conteineres", {
            "todos": True
        }))
        self.assertTrue(res["sucesso"])
        self.assertIn("traefik", res["stdout"])

    @patch.object(docker_server.shutil, "which", return_value=None)
    def test_docker_not_installed(self, mock_which):
        res = asyncio.run(_run_tool(docker_server.mcp, "docker_status_conteineres", {}))
        self.assertFalse(res["sucesso"])
        self.assertEqual(res["exit_code"], 127)
        self.assertIn("não encontrado", res["erro"])


async def _list_tool_names(mcp_server) -> list:
    tools = await mcp_server.list_tools()
    return [t.name for t in tools]


async def _run_tool(mcp_server, name: str, args: dict) -> dict:
    resultado = await mcp_server.call_tool(name, args)
    if isinstance(resultado, tuple):
        structured = resultado[1]
        if isinstance(structured, dict):
            return structured
        resultado = resultado[0]
    blocks = list(resultado) if not isinstance(resultado, list) else resultado
    if not blocks:
        return {}
    from mcp.types import TextContent

    textos = [b.text for b in blocks if isinstance(b, TextContent)]
    try:
        return json.loads(textos[0]) if textos else {}
    except (json.JSONDecodeError, IndexError):
        return {"_conteudo": textos[0] if textos else ""}


if __name__ == "__main__":
    unittest.main()