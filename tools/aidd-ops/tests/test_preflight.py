# -*- coding: utf-8 -*-
"""
Testes unitários rigorosos e herméticos para o PreflightRunner (Pacote 7).
Utiliza servidores HTTP locais reais (http.server.HTTPServer em 127.0.0.1:0)
e dependency injection para DNS e SSL, sem tocar em rede externa.
"""

import http.server
import json
import os
import sys
import threading
import unittest
from pathlib import Path
from typing import List, Tuple

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_ROOT not in sys.path:
    sys.path.insert(0, TOOL_ROOT)
if os.path.join(TOOL_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(TOOL_ROOT, "src"))

from src.core.preflight import PreflightRunner


class _MockHealthHandler(http.server.BaseHTTPRequestHandler):
    """Handler HTTP local real para simulação de healthz e webhook."""

    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        elif self.path == "/error":
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "error"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/webhook":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            if data.get("evento") == "ping_sintetico":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"recebido": true}')
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silencia logs de requisição no console de teste
        _ = (format, args)


class TestPreflightRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Sobe servidor HTTP real em porta aleatória do localhost
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), _MockHealthHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_healthz_servidor_local_sucesso(self):
        url = f"http://127.0.0.1:{self.port}/healthz"
        runner = PreflightRunner(alvo="127.0.0.1", timeout=2.0)
        res = runner.checar_healthz([{"nome": "api", "url": url}])
        self.assertEqual(res["status"], "passou")
        self.assertEqual(len(res["detalhes"]["sucessos"]), 1)

    def test_healthz_servidor_local_falha_500(self):
        url = f"http://127.0.0.1:{self.port}/error"
        runner = PreflightRunner(alvo="127.0.0.1", timeout=1.0, retries=1)
        res = runner.checar_healthz([{"nome": "api_erro", "url": url}])
        self.assertEqual(res["status"], "falhou")
        self.assertEqual(len(res["detalhes"]["falhas"]), 1)
        self.assertEqual(res["detalhes"]["falhas"][0]["status"], 500)

    def test_healthz_servidor_local_404(self):
        url = f"http://127.0.0.1:{self.port}/inexistente"
        runner = PreflightRunner(alvo="127.0.0.1", timeout=1.0, retries=1)
        res = runner.checar_healthz([{"nome": "api_404", "url": url}])
        self.assertEqual(res["status"], "falhou")

    def test_healthz_lista_vazia_retorna_nao_aplicavel(self):
        runner = PreflightRunner(alvo="127.0.0.1")
        res = runner.checar_healthz([])
        self.assertEqual(res["status"], "nao_aplicavel")

    def test_dns_resolver_injetado_sucesso(self):
        mock_resolver = lambda h: ["192.168.1.100", "192.168.1.101"] if h == "app.teste.local" else []
        runner = PreflightRunner(alvo="teste", dns_resolver_fn=mock_resolver, retries=1)
        res = runner.checar_dns(["app.teste.local"])
        self.assertEqual(res["status"], "passou")
        self.assertIn("192.168.1.100", res["detalhes"]["resolvidos"]["app.teste.local"])

    def test_dns_resolver_injetado_falha(self):
        mock_resolver = lambda h: []
        runner = PreflightRunner(alvo="teste", dns_resolver_fn=mock_resolver, retries=1)
        res = runner.checar_dns(["invalido.local"])
        self.assertEqual(res["status"], "falhou")
        self.assertIn("invalido.local", res["detalhes"]["falhas"])

    def test_ssl_validator_injetado_sucesso(self):
        mock_ssl = lambda host, port, timeout: {
            "valido": True,
            "emissor": {"commonName": "Let's Encrypt Authority"},
            "notAfter": "May 31 23:59:59 2027 GMT",
        }
        runner = PreflightRunner(alvo="app.exemplo.com", ssl_validator_fn=mock_ssl)
        res = runner.checar_ssl("app.exemplo.com")
        self.assertEqual(res["status"], "passou")
        self.assertEqual(res["detalhes"]["emissor"]["commonName"], "Let's Encrypt Authority")

    def test_ssl_localhost_retorna_nao_aplicavel(self):
        runner = PreflightRunner(alvo="localhost")
        res = runner.checar_ssl("localhost")
        self.assertEqual(res["status"], "nao_aplicavel")

    def test_webhook_servidor_local_sucesso(self):
        url = f"http://127.0.0.1:{self.port}/webhook"
        runner = PreflightRunner(alvo="127.0.0.1", timeout=2.0)
        res = runner.checar_webhook(url)
        self.assertEqual(res["status"], "passou")
        self.assertEqual(res["detalhes"]["status_code"], 200)

    def test_webhook_endpoint_invalido_falha(self):
        url = f"http://127.0.0.1:{self.port}/nao_existe"
        runner = PreflightRunner(alvo="127.0.0.1", timeout=1.0, retries=1)
        res = runner.checar_webhook(url)
        self.assertEqual(res["status"], "falhou")

    def test_bateria_completa_passa_com_result_ok(self):
        url_health = f"http://127.0.0.1:{self.port}/healthz"
        url_hook = f"http://127.0.0.1:{self.port}/webhook"
        mock_dns = lambda h: ["127.0.0.1"]
        mock_ssl = lambda host, port, timeout: {"valido": True, "emissor": {"CN": "Mock CA"}}

        runner = PreflightRunner(
            alvo="app.teste.local",
            dns_resolver_fn=mock_dns,
            ssl_validator_fn=mock_ssl,
        )

        res = runner.executar_bateria(
            servicos_healthz=[{"nome": "gateway", "url": url_health}],
            subdominios_dns=["app.teste.local"],
            webhook_url=url_hook,
            hostname_ssl="app.teste.local",
        )

        self.assertTrue(res.sucesso)
        self.assertEqual(res.valor["resumo"]["falhou"], 0)
        self.assertEqual(res.valor["resumo"]["passou"], 4)

    def test_bateria_completa_falha_com_result_fail(self):
        url_health = f"http://127.0.0.1:{self.port}/error"
        mock_dns = lambda h: []

        runner = PreflightRunner(
            alvo="app.teste.local",
            dns_resolver_fn=mock_dns,
            retries=1,
            retry_interval=0.01,
        )

        res = runner.executar_bateria(
            servicos_healthz=[{"nome": "gateway", "url": url_health}],
            subdominios_dns=["app.teste.local"],
            hostname_ssl="localhost",  # n/a
        )

        self.assertFalse(res.sucesso)
        self.assertEqual(res.codigo, "PREFLIGHT_FAILED")
        self.assertGreater(res.detalhes["resumo"]["falhou"], 0)


if __name__ == "__main__":
    unittest.main()
