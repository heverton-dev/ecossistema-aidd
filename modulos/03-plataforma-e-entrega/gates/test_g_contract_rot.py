#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TESTES DE QUALIDADE: G_CONTRACT_ROT (ISSUE-0014 & Lei Canônica #13)
=============================================================================
Testa o portão G_CONTRACT_ROT:
1. Caminho feliz: servidor em execução com árvore de rotas idêntica ao openapi.json (exit 0).
2. Prova que morde (Lei #13): mutação deliberada do status code de uma rota faz o gate
   executar e asserir exit 1, nomeando explicitamente a rota divergente no output.
3. Prova que morde (Lei #13): mutação deliberada de tipo de query param asserte exit 1.
4. Prova que morde (Lei #13): mutação deliberada de tipo de campo no schema asserte exit 1.
5. Trava conhecida: validação do caminho real servido /docs (não /swagger).
=============================================================================
"""

import http.server
import json
import os
import socketserver
import subprocess
import sys
import tempfile
import threading
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from gates.G_CONTRACT_ROT import (
    diff_specs,
    auditar_servidor_e_spec,
    coletar_spec_servidor_vivo,
    encontrar_porta_livre,
)

GATE_SCRIPT = os.path.join(ROOT_DIR, "gates", "G_CONTRACT_ROT.py")


def _criar_spec_base():
    """Gera uma especificação OpenAPI 3.1 canônica com rotas e Quarteto Sine Qua Non."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "App Teste", "version": "1.0.0"},
        "paths": {
            "/api/usuarios": {
                "get": {
                    "summary": "Listar Usuários",
                    "parameters": [
                        {
                            "name": "ativo",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "boolean"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Lista de usuários",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "total": {"type": "integer"},
                                            "status": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/api/usuarios/criar": {
                "post": {
                    "summary": "Criar Usuário",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "nome": {"type": "string"},
                                        "idade": {"type": "integer"},
                                    },
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Usuário criado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"id": {"type": "integer"}},
                                    }
                                }
                            },
                        }
                    },
                }
            },
        },
    }


class ServidorMockHandler(http.server.BaseHTTPRequestHandler):
    """Handler HTTP real para servir /openapi.json e endpoints do Quarteto Sine Qua Non."""

    spec_atual: dict = {}

    def log_message(self, format, *args):
        # Silencia logs no stderr durante execução dos testes
        pass

    def do_GET(self):
        if self.path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(self.spec_atual).encode("utf-8"))
            return

        # Rotas reais do Quarteto Sine Qua Non
        if self.path in ["/docs", "/webhooks", "/mcp", "/docs/guia"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body>OK</body></html>")
            return

        if self.path.startswith("/api/usuarios"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"total": 1, "status": "ok"}')
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/usuarios/criar":
            self.send_response(201)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"id": 10}')
            return

        self.send_response(404)
        self.end_headers()


@pytest.fixture
def running_test_server():
    """Sobe um servidor HTTP real em background em porta efêmera para os testes."""
    porta = encontrar_porta_livre()
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", porta), ServidorMockHandler)
    httpd.allow_reuse_address = True
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{porta}"
    yield base_url, ServidorMockHandler

    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=2.0)


def test_caminho_feliz_servidor_vivo_e_spec_identicos_aprova(running_test_server):
    """Caminho feliz: servidor em execução serve exatamente o que o openapi.json commitado declara."""
    base_url, handler_cls = running_test_server
    spec = _criar_spec_base()
    handler_cls.spec_atual = spec

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(spec, f)
        spec_file = f.name

    try:
        codigo, divergencias, stats = auditar_servidor_e_spec(base_url, spec_file)
        assert codigo == 0
        assert len(divergencias) == 0
        assert stats["rotas"] == 2
        assert stats["metodos"] == 2
        assert stats["status_codes"] >= 2
    finally:
        if os.path.exists(spec_file):
            os.remove(spec_file)


def test_failing_path_mutacao_status_code_reprova(running_test_server):
    """Lei #13 (Strict Reading): Mutar deliberadamente o status code de uma rota.

    Executa o gate contra o servidor vivo, asserte exit 1 e confirma que o output
    nomeia explicitamente a rota divergente.
    """
    base_url, handler_cls = running_test_server

    spec_commitada = _criar_spec_base()

    # MUTAÇÃO DELIBERADA: o servidor em execução passa a expor status code 201 no GET /api/usuarios em vez de 200
    spec_mutada_servidor = json.loads(json.dumps(spec_commitada))
    spec_mutada_servidor["paths"]["/api/usuarios"]["get"]["responses"] = {
        "201": {"description": "Criado inesperadamente"}
    }
    handler_cls.spec_atual = spec_mutada_servidor

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(spec_commitada, f)
        spec_file = f.name

    try:
        # 1. Executa via chamada do módulo
        codigo, divergencias, _ = auditar_servidor_e_spec(base_url, spec_file)
        assert codigo == 1
        assert any("/api/usuarios" in d and "status codes" in d for d in divergencias)
        assert any("201" in d and "200" in d for d in divergencias)

        # 2. Executa via processo real do gate (CLI subprocess)
        res = subprocess.run(
            [sys.executable, GATE_SCRIPT, "--url", base_url, "--committed-spec", spec_file],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert res.returncode == 1
        assert "/api/usuarios" in res.stdout
        assert "status codes" in res.stdout
        assert "[BLOQUEIO]" in res.stdout
    finally:
        if os.path.exists(spec_file):
            os.remove(spec_file)


def test_failing_path_mutacao_query_param_reprova(running_test_server):
    """Lei #13: Mutar deliberadamente o tipo de um query param sem atualizar o contrato commitado."""
    base_url, handler_cls = running_test_server
    spec_commitada = _criar_spec_base()

    # MUTAÇÃO DELIBERADA: o servidor vivo muda o tipo do query param 'ativo' de boolean para integer
    spec_mutada_servidor = json.loads(json.dumps(spec_commitada))
    spec_mutada_servidor["paths"]["/api/usuarios"]["get"]["parameters"][0]["schema"]["type"] = "integer"
    handler_cls.spec_atual = spec_mutada_servidor

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(spec_commitada, f)
        spec_file = f.name

    try:
        codigo, divergencias, _ = auditar_servidor_e_spec(base_url, spec_file)
        assert codigo == 1
        assert any("/api/usuarios" in d and "ativo" in d and "integer" in d for d in divergencias)

        res = subprocess.run(
            [sys.executable, GATE_SCRIPT, "--url", base_url, "--committed-spec", spec_file],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert res.returncode == 1
        assert "/api/usuarios" in res.stdout
        assert "ativo" in res.stdout
    finally:
        if os.path.exists(spec_file):
            os.remove(spec_file)


def test_failing_path_mutacao_tipo_campo_schema_reprova(running_test_server):
    """Lei #13: Mutar deliberadamente o tipo de um campo no requestBody sem atualizar openapi.json."""
    base_url, handler_cls = running_test_server
    spec_commitada = _criar_spec_base()

    # MUTAÇÃO DELIBERADA: campo 'idade' de integer para string no servidor vivo
    spec_mutada_servidor = json.loads(json.dumps(spec_commitada))
    spec_mutada_servidor["paths"]["/api/usuarios/criar"]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]["idade"]["type"] = "string"
    handler_cls.spec_atual = spec_mutada_servidor

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(spec_commitada, f)
        spec_file = f.name

    try:
        codigo, divergencias, _ = auditar_servidor_e_spec(base_url, spec_file)
        assert codigo == 1
        assert any("/api/usuarios/criar" in d and "idade" in d and "string" in d for d in divergencias)

        res = subprocess.run(
            [sys.executable, GATE_SCRIPT, "--url", base_url, "--committed-spec", spec_file],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert res.returncode == 1
        assert "/api/usuarios/criar" in res.stdout
        assert "idade" in res.stdout
    finally:
        if os.path.exists(spec_file):
            os.remove(spec_file)


def test_failing_path_rota_ausente_no_servidor_reprova(running_test_server):
    """Lei #13: Uma rota documentada no openapi.json não é servida pelo servidor vivo."""
    base_url, handler_cls = running_test_server
    spec_commitada = _criar_spec_base()

    # Servidor vivo removeu /api/usuarios/criar
    spec_mutada_servidor = json.loads(json.dumps(spec_commitada))
    del spec_mutada_servidor["paths"]["/api/usuarios/criar"]
    handler_cls.spec_atual = spec_mutada_servidor

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(spec_commitada, f)
        spec_file = f.name

    try:
        codigo, divergencias, _ = auditar_servidor_e_spec(base_url, spec_file)
        assert codigo == 1
        assert any("/api/usuarios/criar" in d and "ausente no servidor" in d for d in divergencias)
    finally:
        if os.path.exists(spec_file):
            os.remove(spec_file)


def test_servidor_serve_docs_real_e_nao_swagger(running_test_server):
    """Trava conhecida ISSUE-0001/ISSUE-0014: certifica que o caminho servido real é /docs."""
    base_url, _ = running_test_server
    # Requisição direta na rota real
    import urllib.request
    with urllib.request.urlopen(f"{base_url}/docs", timeout=2) as resp:
        assert resp.status == 200

    # /swagger não existe no servidor real (retorna 404)
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(f"{base_url}/swagger", timeout=2)
    assert exc.value.code == 404
