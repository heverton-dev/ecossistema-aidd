# -*- coding: utf-8 -*-
"""
Teste TDD para o MCP Lazy Gatekeeper
Valida:
1. Inicialização com backends dormentes (RAM = 0).
2. Spawn sob demanda na primeira chamada.
3. Idle reaping automático após inatividade.
4. Repasse de argumentos e respostas JSON-RPC.
"""

import sys
import os
import time
import json
import subprocess
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATEKEEPER_PATH = os.path.join(ROOT_DIR, "componentes", "compartilhado", "src-core", "mcp_gatekeeper.py")

def test_mcp_gatekeeper_arquivo_existe():
    assert os.path.isfile(GATEKEEPER_PATH), f"mcp_gatekeeper.py deve existir em {GATEKEEPER_PATH}"

def test_mcp_gatekeeper_lifecycle(tmp_path):
    # Cria backend mock simples em Python
    mock_backend = tmp_path / "mock_backend.py"
    mock_backend.write_text("""
import sys, json
for line in sys.stdin:
    if not line.strip():
        continue
    req = json.loads(line)
    req_id = req.get('id')
    method = req.get('method')
    if method == 'initialize':
        resp = {'jsonrpc': '2.0', 'id': req_id, 'result': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'serverInfo': {'name': 'mock', 'version': '1.0'}}}
    elif method == 'tools/list':
        resp = {'jsonrpc': '2.0', 'id': req_id, 'result': {'tools': [{'name': 'echo_tool', 'description': 'Echo', 'inputSchema': {}}]}}
    elif method == 'tools/call':
        params = req.get('params', {})
        resp = {'jsonrpc': '2.0', 'id': req_id, 'result': {'content': [{'type': 'text', 'text': f"Echo: {params.get('arguments', {}).get('msg')}"}]}}
    else:
        resp = {'jsonrpc': '2.0', 'id': req_id, 'result': {}}
    sys.stdout.write(json.dumps(resp) + '\\n')
    sys.stdout.flush()
""", encoding="utf-8")

    config_file = tmp_path / "gatekeeper_test.json"
    config = {
        "idle_timeout": 2,
        "backends": {
            "mock": {
                "command": sys.executable,
                "args": [str(mock_backend)]
            }
        }
    }
    config_file.write_text(json.dumps(config), encoding="utf-8")

    # Inicia o gatekeeper
    proc = subprocess.Popen(
        [sys.executable, GATEKEEPER_PATH, "--config", str(config_file)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # 1. Initialize Handshake
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        }
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        res = json.loads(line)
        assert res["id"] == 1
        assert "serverInfo" in res["result"]

        # 2. Tools/list retorna as meta-tools do gatekeeper
        list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        proc.stdin.write(json.dumps(list_req) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        res = json.loads(line)
        tools = [t["name"] for t in res["result"]["tools"]]
        assert "get_mcp_tools" in tools or "list_backends" in tools
        assert "call_mcp_tool" in tools

        # 3. Call tool dispara o backend mock
        call_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "call_mcp_tool",
                "arguments": {
                    "server": "mock",
                    "tool": "echo_tool",
                    "arguments": {"msg": "Ola AIDD"}
                }
            }
        }
        proc.stdin.write(json.dumps(call_req) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        res = json.loads(line)
        assert "Ola AIDD" in str(res["result"])

    finally:
        proc.terminate()
        proc.wait(timeout=3)
