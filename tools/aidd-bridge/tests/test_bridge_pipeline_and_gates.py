# -*- coding: utf-8 -*-
"""
Testes unitários e de integração para os novos componentes e Quality Gates da aidd-bridge:
- G_BRIDGE_VENDOR_LOCKIN
- G_BRIDGE_DOCKER_OCI
- G_BRIDGE_POSTGRESQL
- G_BRIDGE_VSA_COMPAT
- BridgeVSAExporter (Quarteto Sine Qua Non)
- BridgePipeline (FLUXO 03)
"""

import os
import sys
import json
import tempfile
import pytest

# Adiciona o diretório da ferramenta e dos gates no path
BRIDGE_DIR = os.path.dirname(os.path.dirname(__file__))
GATES_DIR = os.path.join(BRIDGE_DIR, "gates")
sys.path.insert(0, BRIDGE_DIR)
sys.path.insert(0, GATES_DIR)

from aidd_bridge.vsa_exporter import BridgeVSAExporter
from aidd_bridge.pipeline_bridge import BridgePipeline
from G_BRIDGE_VENDOR_LOCKIN import audit_vendor_lockin
from G_BRIDGE_DOCKER_OCI import audit_docker_oci
from G_BRIDGE_POSTGRESQL import audit_postgresql_script
from G_BRIDGE_VSA_COMPAT import audit_vsa_compat


def test_vsa_exporter_generates_quarteto_contracts():
    manifest = {
        "framework": "gestao-entregas",
        "routes": ["/", "/encomendas", "/frotas", "/perfil"],
        "pages": ["Index.tsx", "Encomendas.tsx", "Frotas.tsx", "Perfil.tsx"]
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = BridgeVSAExporter(manifest, tmpdir)
        contracts = exporter.export_quarteto_contracts()

        assert os.path.exists(contracts["swagger"])
        assert os.path.exists(contracts["webhooks"])
        assert os.path.exists(contracts["mcp"])
        assert os.path.exists(contracts["docs"])

        # Valida conteúdo do Swagger
        with open(contracts["swagger"], "r", encoding="utf-8") as f:
            swagger = json.load(f)
            assert swagger["openapi"] == "3.0.3"
            assert "/encomendas" in swagger["paths"]

        # Valida conteúdo dos Webhooks
        with open(contracts["webhooks"], "r", encoding="utf-8") as f:
            webhooks = json.load(f)
            assert webhooks["algorithm"] == "HMAC-SHA256"

        # Valida conteúdo do MCP
        with open(contracts["mcp"], "r", encoding="utf-8") as f:
            mcp = json.load(f)
            assert len(mcp["tools"]) >= 2

        # Valida gate VSA
        assert audit_vsa_compat(tmpdir) == 0


def test_gate_vendor_lockin_detects_supabase_cloud():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Cria arquivo com URL proprietária hardcoded
        bad_file = os.path.join(tmpdir, "client.ts")
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("const client = createClient('https://xyzabc123.supabase.co', 'chave');")

        # Deve falhar (Exit 1)
        assert audit_vendor_lockin(tmpdir) == 1

        # Limpa o arquivo usando variável de ambiente
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("const client = createClient(process.env.VITE_SUPABASE_URL, process.env.VITE_ANON_KEY);")

        # Deve passar (Exit 0)
        assert audit_vendor_lockin(tmpdir) == 0


def test_gate_docker_oci_validates_security():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Sem Dockerfile -> ignora (Exit 0)
        assert audit_docker_oci(tmpdir) == 0

        # Cria Dockerfile e Nginx com boas práticas
        docker_file = os.path.join(tmpdir, "Dockerfile")
        with open(docker_file, "w", encoding="utf-8") as f:
            f.write("FROM node:20-alpine AS builder\nWORKDIR /app\nFROM nginx:alpine\n")

        nginx_file = os.path.join(tmpdir, "nginx.conf")
        with open(nginx_file, "w", encoding="utf-8") as f:
            f.write("server { listen 80; add_header X-Content-Type-Options nosniff; add_header X-Frame-Options DENY; }\n")

        # Deve passar (Exit 0)
        assert audit_docker_oci(tmpdir) == 0


def test_gate_postgresql_script_validates_init_sql():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Sem arquivo -> passa
        assert audit_postgresql_script(tmpdir) == 0

        # Cria init-db.sql válido
        sql_file = os.path.join(tmpdir, "init-db.sql")
        with open(sql_file, "w", encoding="utf-8") as f:
            f.write("CREATE SCHEMA IF NOT EXISTS public;\nCREATE TABLE items (id SERIAL PRIMARY KEY);\n")

        assert audit_postgresql_script(tmpdir) == 0


def test_pipeline_bridge_execution():
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as out_dir:
        # Cria estrutura mínima de projeto Lovable mock
        src_pages = os.path.join(src_dir, "src", "pages")
        os.makedirs(src_pages, exist_ok=True)
        with open(os.path.join(src_pages, "Index.tsx"), "w", encoding="utf-8") as f:
            f.write("export default function Index() { return <div>Home</div>; }")
        with open(os.path.join(src_pages, "Dashboard.tsx"), "w", encoding="utf-8") as f:
            f.write("export default function Dashboard() { return <div>Dashboard</div>; }")

        # Cria package.json
        with open(os.path.join(src_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write('{"name": "mock-lovable-app", "dependencies": {"react": "^18.0.0"}}')

        # Executa pipeline da Bridge
        pipeline = BridgePipeline(src_dir, output_dir=out_dir, domain="app.empresa.com")
        status = pipeline.run()

        assert status == 0
        assert os.path.exists(os.path.join(out_dir, "bridge-manifest.json"))
        assert os.path.exists(os.path.join(out_dir, "init-db.sql"))
        assert os.path.exists(os.path.join(out_dir, "Dockerfile"))
        assert os.path.exists(os.path.join(out_dir, "nginx.conf"))
        assert os.path.exists(os.path.join(out_dir, "docker-compose.yml"))
        assert os.path.exists(os.path.join(out_dir, "quarteto_sine_qua_non", "swagger_spec.json"))
        assert os.path.exists(os.path.join(out_dir, "quarteto_sine_qua_non", "webhooks_contract.json"))
        assert os.path.exists(os.path.join(out_dir, "quarteto_sine_qua_non", "mcp_studio.json"))
        assert os.path.exists(os.path.join(out_dir, "quarteto_sine_qua_non", "USER_GUIDE.md"))
