# -*- coding: utf-8 -*-
"""
Testes automatizados para o gate G_STACK_PADRAO_OURO (Lei #11).
Comprova que o portão morde (exit 1 em violação de stack sem override)
e aprova caminhos conformes e cenários de override explícito (exit 0).
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

from G_STACK_PADRAO_OURO import (
    main,
    auditar_projeto,
    auditar_frontend,
    auditar_backend,
    extrair_overrides_explicitos,
)


def test_stack_morde_quando_falta_tailwind(tmp_path):
    """Prova que o portão morde: frontend sem Tailwind CSS causa exit 1."""
    proj = tmp_path / "proj_sem_tailwind"
    proj.mkdir()
    fe = proj / "frontend"
    fe.mkdir()
    pkg = {
        "dependencies": {"next": "14.2.5", "react": "18.3.1"},
        "devDependencies": {"typescript": "5.4.5"}
        # Sem tailwindcss
    }
    (fe / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

    codigo, erros, res = auditar_projeto(str(proj))
    assert codigo == 1
    assert any("Tailwind CSS" in e for e in erros)

    # Verifica via subprocess para garantir saída binária
    cmd = [sys.executable, os.path.abspath("gates/G_STACK_PADRAO_OURO.py"), str(proj)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "[ERRO]" in proc.stderr or "[FALHA]" in proc.stderr or "[FALHA]" in proc.stdout


def test_stack_morde_quando_backend_sem_sqlite_wal(tmp_path):
    """Prova que o portão morde: backend Python sem SQLite WAL causa exit 1."""
    proj = tmp_path / "proj_sem_wal"
    proj.mkdir()
    server_code = """
from fastapi import FastAPI
app = FastAPI()
# openapi declarado mas sem WAL
OPENAPI_VERSION = "3.1.0"
"""
    (proj / "server.py").write_text(server_code, encoding="utf-8")

    codigo, erros, res = auditar_projeto(str(proj))
    assert codigo == 1
    assert any("SQLite no modo WAL" in e for e in erros)


def test_stack_respeita_override_explicito_no_plano(tmp_path):
    """Prova que override explícito documentado para a camada dispensa reprovação."""
    proj = tmp_path / "proj_override"
    proj.mkdir()
    fe = proj / "frontend"
    fe.mkdir()
    # Frontend com Vue em vez de Next.js
    pkg = {"dependencies": {"vue": "3.0.0"}}
    (fe / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

    # Registra override explícito em PLANNER.json
    plano = {
        "nome": "Projeto com override justificado",
        "stack_override": {
            "frontend": "Vue 3 solicitado expressamente pelo cliente",
            "backend": "Dispensa backend"
        }
    }
    (proj / "PLANNER.json").write_text(json.dumps(plano), encoding="utf-8")

    codigo, erros, res = auditar_projeto(str(proj))
    assert codigo == 0
    assert len(erros) == 0


def test_stack_projeto_completo_conforme(tmp_path):
    """Caminho feliz: projeto com Next.js, TypeScript, Tailwind, SQLite WAL e OpenAPI 3.1."""
    proj = tmp_path / "proj_padrao_ouro"
    proj.mkdir()
    fe = proj / "frontend"
    fe.mkdir()
    pkg = {
        "dependencies": {"next": "14.2.5", "react": "18.3.1"},
        "devDependencies": {"typescript": "5.4.5", "tailwindcss": "3.4.4"}
    }
    (fe / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

    server_code = """
import sqlite3
conn = sqlite3.connect("app.db")
conn.execute("PRAGMA journal_mode=WAL;")

openapi_spec = {
    "openapi": "3.1.0",
    "info": {"title": "App Padrão-Ouro", "version": "1.0.0"}
}
"""
    (proj / "server.py").write_text(server_code, encoding="utf-8")

    codigo, erros, res = auditar_projeto(str(proj))
    assert codigo == 0
    assert len(erros) == 0


def test_stack_referencia_real_proj_ctt():
    """Valida a referência canônica real proj_ctt se presente no ambiente."""
    ctt_path = r"C:\Users\trcnologia\Desktop\proj_ctt\planos-ctt-app"
    if os.path.isdir(ctt_path):
        codigo, erros, res = auditar_projeto(ctt_path)
        assert codigo == 0
        assert len(erros) == 0
        assert res["frontend"]["ok"] is True
        assert res["backend"]["ok"] is True


def test_stack_execucao_raiz():
    """Valida a execução do gate no ecossistema sem argumentos."""
    codigo = main("")
    assert codigo == 0
