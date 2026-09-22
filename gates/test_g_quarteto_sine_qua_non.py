# -*- coding: utf-8 -*-
"""
Testes automatizados para o gate G_QUARTETO_SINE_QUA_NON (Lei #10).
Comprova que o portão morde (exit 1 em violação real) e aprova caminhos conformes (exit 0).
"""

import json
import os
import subprocess
import sys
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES_DIR = os.path.join(ROOT_DIR, "gates")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if GATES_DIR not in sys.path:
    sys.path.insert(0, GATES_DIR)

from G_QUARTETO_SINE_QUA_NON import (
    main,
    auditar_projeto,
    auditar_openapi_spec,
    auditar_codigo_fonte,
    PILARES_OBRIGATORIOS,
)


def test_quarteto_falha_quando_falta_pilar_morde(tmp_path):
    """Prova que o portão morde: se faltar o pilar MCP, o gate DEVE falhar com exit 1."""
    # Cria projeto mock com apenas Swagger, Webhooks e Guia (sem MCP)
    server_code = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/docs")
def docs(): return {"status": "ok"}

@app.post("/webhooks")
def webhooks(): return {"status": "ok"}

@app.get("/docs/guia")
def guia(): return {"status": "ok"}
"""
    proj_dir = tmp_path / "proj_sem_mcp"
    proj_dir.mkdir()
    (proj_dir / "server.py").write_text(server_code, encoding="utf-8")

    codigo, erros, status = auditar_projeto(str(proj_dir))
    assert codigo == 1
    assert status["swagger"] is True
    assert status["webhooks"] is True
    assert status["guia"] is True
    assert status["mcp"] is False
    assert any("MCP Studio" in e for e in erros)

    # Executa via CLI/subprocess para garantir saída binária 1
    cmd = [sys.executable, os.path.abspath("gates/G_QUARTETO_SINE_QUA_NON.py"), str(proj_dir)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1
    assert "[ERRO]" in res.stderr or "[FALHA]" in res.stdout or "[FALHA]" in res.stderr


def test_quarteto_aprova_projeto_completo_conforme(tmp_path):
    """Caminho feliz: projeto com todos os 4 pilares DEVE retornar exit 0."""
    server_code = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/docs")
def docs(): return {"status": "ok"}

@app.post("/webhooks")
def webhooks(): return {"status": "ok"}

@app.post("/mcp/rpc")
def mcp(): return {"status": "ok"}

@app.get("/docs/guia")
def guia(): return {"status": "ok"}
"""
    proj_dir = tmp_path / "proj_completo"
    proj_dir.mkdir()
    (proj_dir / "server.py").write_text(server_code, encoding="utf-8")

    codigo, erros, status = auditar_projeto(str(proj_dir))
    assert codigo == 0
    assert len(erros) == 0
    assert all(status.values())

    cmd = [sys.executable, os.path.abspath("gates/G_QUARTETO_SINE_QUA_NON.py"), str(proj_dir)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "[SUCESSO]" in res.stdout


def test_quarteto_aprova_via_openapi_spec(tmp_path):
    """Valida que uma spec OpenAPI completa satisfaz os 4 pilares."""
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/api/v1/items": {},
            "/webhooks/events": {},
            "/mcp/tools": {},
            "/docs/guia": {},
        }
    }
    proj_dir = tmp_path / "proj_openapi"
    proj_dir.mkdir()
    (proj_dir / "openapi.json").write_text(json.dumps(spec), encoding="utf-8")

    codigo, erros, status = auditar_projeto(str(proj_dir))
    assert codigo == 0
    assert all(status.values())


def test_quarteto_execucao_raiz():
    """Valida a execução do gate no ecossistema sem argumentos."""
    codigo = main("")
    assert codigo == 0


def test_quarteto_projetos_reais_canonicos():
    """Valida projetos canônicos reais do ecossistema."""
    enterprise_suite = os.path.join(ROOT_DIR, "tools", "aidd-enterprise", "materiais-extras", "examples", "enterprise-suite-v4")
    if os.path.isdir(enterprise_suite):
        cod, errs, status = auditar_projeto(enterprise_suite)
        assert cod == 0
        assert all(status.values())

    ctt_path = r"C:\Users\trcnologia\Desktop\proj_ctt\planos-ctt-app"
    if os.path.isdir(ctt_path):
        cod, errs, status = auditar_projeto(ctt_path)
        assert cod == 0
        assert all(status.values())


def test_quarteto_aprova_nova_taxonomia_canonica(tmp_path):
    """Valida projeto estritamente formatado na nova taxonomia [/api, /webhook, /mcp, /docs]."""
    server_code = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/api")
def api_studio(): return {"pilar": "API Studio"}

@app.post("/webhook")
def webhook_studio(): return {"pilar": "Webhook Studio"}

@app.post("/mcp")
def mcp_studio(): return {"pilar": "MCP Studio"}

@app.get("/docs")
def central_docs(): return {"pilar": "Central de Documentação"}
"""
    proj_dir = tmp_path / "proj_nova_taxonomia"
    proj_dir.mkdir()
    (proj_dir / "server.py").write_text(server_code, encoding="utf-8")

    codigo, erros, status = auditar_projeto(str(proj_dir))
    assert codigo == 0
    assert len(erros) == 0
    assert all(status.values())


