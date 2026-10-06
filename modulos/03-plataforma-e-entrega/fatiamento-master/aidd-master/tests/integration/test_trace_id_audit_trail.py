# -*- coding: utf-8 -*-
"""
Teste End-to-End Real da Trilha de Auditoria (X-Trace-Id / LGPD / GDPR)
ISSUE-0006 — Prova de fogo:
1. A requisição HTTP entra portando X-Trace-Id;
2. O servidor processa e retorna exatamente o mesmo X-Trace-Id no cabeçalho da resposta;
3. O log estruturado do servidor registra o mesmo trace_id no contexto de auditoria;
4. Na ausência do cabeçalho, um novo trace_id é gerado, retornado e registrado de ponta a ponta.
"""

import io
import json
import logging
import socketserver
import threading
import time
import urllib.request
import urllib.error
import pytest

from src.server import AppHandler, logger
from src.core.logs import JSONFormatter, correlation_id_var
from src.core.opentelemetry import extract_or_generate_trace_id, get_current_trace_id


class _LogCaptureHandler(logging.Handler):
    """Handler em memória para capturar logs estruturados durante o teste."""
    def __init__(self):
        super().__init__()
        self.records = []
        self.formatted_entries = []

    def emit(self, record):
        self.records.append(record)
        formatted = self.format(record)
        try:
            self.formatted_entries.append(json.loads(formatted))
        except Exception:
            self.formatted_entries.append({"raw": formatted})


@pytest.fixture(scope="module")
def live_server():
    """Inicializa um servidor HTTP real em porta efêmera."""
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), AppHandler)
    host, port = server.server_address

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(0.1)  # Breve tempo para bind
    base_url = f"http://{host}:{port}"

    yield base_url

    server.shutdown()
    server.server_close()


@pytest.fixture
def log_capture():
    """Captura e formata logs emitidos pelo logger do servidor."""
    handler = _LogCaptureHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    yield handler
    logger.removeHandler(handler)


def test_trace_id_enters_returns_and_logs(live_server, log_capture):
    """Prova que X-Trace-Id fornecido pelo cliente percorre todo o ciclo:
    entra na requisição -> retorna idêntico no header -> é registrado no log."""
    custom_trace_id = "trace-client-lgpd-auditoria-12345"

    req = urllib.request.Request(f"{live_server}/openapi.json")
    req.add_header("X-Trace-Id", custom_trace_id)

    with urllib.request.urlopen(req, timeout=5) as resp:
        status = resp.status
        headers = dict(resp.headers)
        body = resp.read()

    assert status == 200
    # 1. Header de resposta carrega exatamente o trace id injetado
    assert "X-Trace-Id" in headers or "x-trace-id" in headers
    resp_trace_id = headers.get("X-Trace-Id") or headers.get("x-trace-id")
    assert resp_trace_id == custom_trace_id

    # 2. Log estruturado gravou o evento com o mesmo trace_id
    matching_logs = [
        entry for entry in log_capture.formatted_entries
        if entry.get("trace_id") == custom_trace_id
    ]
    assert len(matching_logs) >= 1, f"Nenhum log com trace_id='{custom_trace_id}' encontrado. Logs capturados: {log_capture.formatted_entries}"
    log_entry = matching_logs[0]
    assert log_entry["trace_id"] == custom_trace_id
    assert log_entry["correlation_id"] == custom_trace_id


def test_trace_id_generated_when_absent(live_server, log_capture):
    """Prova que requisição sem header recebe um trace_id gerado, retornado e logado."""
    req = urllib.request.Request(f"{live_server}/openapi.json")

    with urllib.request.urlopen(req, timeout=5) as resp:
        status = resp.status
        headers = dict(resp.headers)

    assert status == 200
    resp_trace_id = headers.get("X-Trace-Id") or headers.get("x-trace-id")
    assert resp_trace_id is not None
    assert len(resp_trace_id) >= 16  # UUID hex gerado

    # Log estruturado contém o trace_id gerado
    matching_logs = [
        entry for entry in log_capture.formatted_entries
        if entry.get("trace_id") == resp_trace_id
    ]
    assert len(matching_logs) >= 1, f"Nenhum log com trace_id gerado '{resp_trace_id}' encontrado."


def test_trace_id_case_insensitive_header(live_server, log_capture):
    """Garante compatibilidade com variantes como X-Trace-ID."""
    custom_trace_id = "trace-uppercase-id-67890"

    req = urllib.request.Request(f"{live_server}/openapi.json")
    req.add_header("X-Trace-ID", custom_trace_id)

    with urllib.request.urlopen(req, timeout=5) as resp:
        status = resp.status
        headers = dict(resp.headers)

    assert status == 200
    resp_trace_id = headers.get("X-Trace-Id") or headers.get("x-trace-id")
    assert resp_trace_id == custom_trace_id

    matching_logs = [
        entry for entry in log_capture.formatted_entries
        if entry.get("trace_id") == custom_trace_id
    ]
    assert len(matching_logs) >= 1
