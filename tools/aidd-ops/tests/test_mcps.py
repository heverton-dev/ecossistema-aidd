"""
Testes unitários herméticos para os servidores MCP do aidd-ops:
- cloudflare-mcp (criação e consulta DNS com urllib mockado)
- docker-mcp (leitura de compose, status e logs com subprocess/shutil mockados)
"""

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

    def test_list_tools(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        res = cf_server.processar_requisicao(req)
        self.assertIn("result", res)
        tools = res["result"]["tools"]
        nomes = [t["name"] for t in tools]
        self.assertIn("cloudflare_criar_registro_a", nomes)
        self.assertIn("cloudflare_criar_registro_cname", nomes)
        self.assertIn("cloudflare_consultar_dns", nomes)

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

        res = cf_server.executar_tool("cloudflare_criar_registro_a", {
            "zone_id": "zone_abc",
            "name": "app.example.com",
            "content": "1.2.3.4"
        })

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

        res = cf_server.executar_tool("cloudflare_criar_registro_cname", {
            "zone_id": "zone_abc",
            "name": "crm.example.com",
            "content": "app.example.com"
        })

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

        res = cf_server.executar_tool("cloudflare_consultar_dns", {
            "zone_id": "zone_abc",
            "name": "app.example.com"
        })
        self.assertTrue(res["sucesso"])
        self.assertEqual(len(res["registros"]), 1)


class TestDockerMCP(unittest.TestCase):
    def test_list_tools(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        res = docker_server.processar_requisicao(req)
        self.assertIn("result", res)
        tools = res["result"]["tools"]
        nomes = [t["name"] for t in tools]
        self.assertIn("docker_compose_config", nomes)
        self.assertIn("docker_status_conteineres", nomes)
        self.assertIn("docker_logs", nomes)

    @patch.object(docker_server.os.path, "exists", return_value=True)
    @patch.object(docker_server.shutil, "which", return_value="/usr/bin/docker")
    @patch.object(docker_server.subprocess, "run")
    def test_docker_compose_config(self, mock_run, mock_which, mock_exists):
        mock_run.return_value = MagicMock(returncode=0, stdout="services:\n  web:\n    image: nginx", stderr="")
        res = docker_server.executar_tool("docker_compose_config", {"compose_path": "docker-compose.yml"})
        self.assertTrue(res["sucesso"])
        self.assertIn("nginx", res["stdout"])

    @patch.object(docker_server.shutil, "which", return_value="/usr/bin/docker")
    @patch.object(docker_server.subprocess, "run")
    def test_docker_ps(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0, stdout='[{"ID":"123","Names":"traefik"}]', stderr="")
        res = docker_server.executar_tool("docker_status_conteineres", {"todos": True})
        self.assertTrue(res["sucesso"])
        self.assertIn("traefik", res["stdout"])

    @patch.object(docker_server.shutil, "which", return_value=None)
    def test_docker_not_installed(self, mock_which):
        res = docker_server.executar_tool("docker_status_conteineres", {})
        self.assertFalse(res["sucesso"])
        self.assertEqual(res["exit_code"], 127)
        self.assertIn("não encontrado", res["erro"])


if __name__ == "__main__":
    unittest.main()
