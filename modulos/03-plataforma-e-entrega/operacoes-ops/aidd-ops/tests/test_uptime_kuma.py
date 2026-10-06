# -*- coding: utf-8 -*-
"""
Testes unitários e de integração do gerenciador Uptime Kuma (NIH #14).
Valida que os healthchecks e monitores são extraídos dinamicamente da
infraestrutura real, sem nenhum dado fabricado/hardcoded.
"""

import http.server
import json
import os
import sys
import tempfile
import threading
from typing import Tuple
import pytest

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_ROOT not in sys.path:
    sys.path.insert(0, TOOL_ROOT)
if os.path.join(TOOL_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(TOOL_ROOT, "src"))

from src.core.uptime_kuma import UptimeKumaManager
from src.core.result import Result


class TestUptimeKumaManager:

    def test_extrair_monitores_de_servicos_sucesso(self):
        manager = UptimeKumaManager()
        servicos = [
            {"nome": "Traefik", "url": "http://localhost:80/ping", "intervalo": 30},
            {"nome": "Twenty CRM", "url": "http://localhost:3000/healthz", "intervalo": 45},
            {"nome": "Cal.com", "url": "http://localhost:3000/api/health", "intervalo": 60},
        ]
        res = manager.extrair_monitores_de_servicos(servicos)
        assert res.sucesso is True
        monitores = res.valor
        assert len(monitores) == 3

        m1 = monitores[0]
        assert m1["name"] == "Traefik"
        assert m1["url"] == "http://localhost:80/ping"
        assert m1["interval"] == 30
        assert m1["type"] == "http"
        assert m1["active"] == 1

        m2 = monitores[1]
        assert m2["name"] == "Twenty CRM"
        assert m2["url"] == "http://localhost:3000/healthz"
        assert m2["interval"] == 45

    def test_extrair_monitores_servicos_vazios_retorna_fail(self):
        manager = UptimeKumaManager()
        res = manager.extrair_monitores_de_servicos([])
        assert res.sucesso is False
        assert res.codigo == "SERVICOS_VAZIOS"

    def test_extrair_monitores_servico_sem_url_retorna_fail(self):
        manager = UptimeKumaManager()
        res = manager.extrair_monitores_de_servicos([{"nome": "Invalido"}])
        assert res.sucesso is False
        assert res.codigo == "SERVICO_SEM_URL"

    def test_extrair_monitores_de_compose_conteudo_com_healthcheck(self):
        compose_yaml = """
services:
  app-teste:
    image: my-app:latest
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]

  outro-servico:
    image: outro:latest
    ports:
      - "${PORTA_SRV:-9090}:9090"
"""
        manager = UptimeKumaManager()
        res = manager.extrair_monitores_de_compose_conteudo(compose_yaml)
        assert res.sucesso is True
        monitores = res.valor
        assert len(monitores) == 2
        assert monitores[0]["name"] == "app-teste"
        assert monitores[0]["url"] == "http://localhost:8080/health"
        assert monitores[1]["name"] == "outro-servico"
        assert monitores[1]["url"] == "http://localhost:9090/"

    def test_extrair_monitores_compose_vazio_retorna_fail(self):
        manager = UptimeKumaManager()
        res = manager.extrair_monitores_de_compose_conteudo("")
        assert res.sucesso is False
        assert res.codigo == "COMPOSE_VAZIO"

    def test_gerar_export_kuma_e_salvar(self):
        manager = UptimeKumaManager()
        servicos = [{"nome": "App", "url": "http://localhost:8000/healthz"}]
        res_mon = manager.extrair_monitores_de_servicos(servicos)
        assert res_mon.sucesso is True

        res_exp = manager.gerar_export_kuma(res_mon.valor, nome_dashboard="Stack Teste")
        assert res_exp.sucesso is True
        export_data = res_exp.valor
        assert export_data["version"] == "1.23.15"
        assert export_data["dashboard_title"] == "Stack Teste"
        assert len(export_data["monitorList"]) == 1

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_path = tf.name

        try:
            res_salvar = manager.salvar_export_kuma(export_data, temp_path)
            assert res_salvar.sucesso is True
            assert os.path.isfile(temp_path)

            with open(temp_path, "r", encoding="utf-8") as f:
                lido = json.load(f)
            assert lido["version"] == "1.23.15"
            assert lido["monitorList"][0]["name"] == "App"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_verificar_saude_dashboard_com_servidor_local(self):
        class HealthHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html>Uptime Kuma Mock</html>")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                _silence = (format, args)
                return _silence

        server = http.server.HTTPServer(("127.0.0.1", 0), HealthHandler)
        port = server.server_port
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            manager = UptimeKumaManager()
            url = f"http://127.0.0.1:{port}/"
            res = manager.verificar_saude_dashboard(url)
            assert res.sucesso is True
            assert res.valor["status"] == "online"
            assert res.valor["http_code"] == 200
        finally:
            server.shutdown()
            server.server_close()

    def test_verificar_saude_dashboard_falha_conexao(self):
        manager = UptimeKumaManager()
        res = manager.verificar_saude_dashboard("http://127.0.0.1:59999/")
        assert res.sucesso is False
        assert res.codigo == "CONEXAO_RECUSADA"

    def test_sem_dados_hardcoded_validacao_rejeita_fabricacao(self):
        manager = UptimeKumaManager()
        servicos_entrada = [
            {"nome": "Servico A", "url": "http://10.0.0.5:8001/status"},
            {"nome": "Servico B", "url": "http://10.0.0.6:8002/ping"},
        ]
        res = manager.extrair_monitores_de_servicos(servicos_entrada)
        assert res.sucesso is True
        monitores = res.valor
        
        urls_geradas = [m["url"] for m in monitores]
        assert "http://10.0.0.5:8001/status" in urls_geradas
        assert "http://10.0.0.6:8002/ping" in urls_geradas
        for url in urls_geradas:
            assert "8082" not in url
            assert "9000" not in url
