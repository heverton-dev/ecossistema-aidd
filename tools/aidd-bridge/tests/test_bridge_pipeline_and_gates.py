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

from aidd_bridge.devops import DevOpsPackager
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


def test_vsa_exporter_aceita_manifesto_real_do_scanner_com_rotas_dict():
    """Reproduz bug real: BridgeVSAExporter quebrava com
    'TypeError: cannot use dict as a dict key' porque LovableScanner (real,
    nao o mock do teste acima) devolve manifest['routes'] como lista de
    dicts ({"path", "component", "source_file", "type"}), nao strings."""
    manifest = {
        "package_info": {"name": "gestao-tarefas-lovable"},
        "routes": [
            {"path": "/", "component": "Index", "source_file": "App.tsx", "type": "react-router"},
            {"path": "/tarefas", "component": "Tarefas", "source_file": "App.tsx", "type": "react-router"},
        ],
        "pages": ["src/pages/Index.tsx", "src/pages/Tarefas.tsx"],
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = BridgeVSAExporter(manifest, tmpdir)
        contracts = exporter.export_quarteto_contracts()

        with open(contracts["swagger"], "r", encoding="utf-8") as f:
            swagger = json.load(f)
        assert "/tarefas" in swagger["paths"]
        assert swagger["info"]["title"].lower().startswith("gestao-tarefas-lovable")


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


def test_pipeline_bridge_copies_and_liberates_frontend_when_output_differs():
    """
    Reproduz bug real: quando --output aponta para um diretorio diferente do
    projeto de origem (uso normal, para nao mutar o export Lovable original),
    o pipeline nunca copiava o codigo-fonte do frontend para o destino, e o
    unico arquivo com a URL hardcoded do Supabase Cloud (client.ts) nunca era
    sanitizado nem auditado pelo G_BRIDGE_VENDOR_LOCKIN (que so varre out_dir).
    Isso fazia o Docker build do output falhar (sem package.json/src/) e o
    gate de vendor lock-in aprovar (falso negativo) um projeto ainda preso ao
    Supabase Cloud.
    """
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as out_dir:
        src_pages = os.path.join(src_dir, "src", "pages")
        os.makedirs(src_pages, exist_ok=True)
        with open(os.path.join(src_pages, "Index.tsx"), "w", encoding="utf-8") as f:
            f.write("export default function Index() { return <div>Tarefas</div>; }")

        integ_dir = os.path.join(src_dir, "src", "integrations", "supabase")
        os.makedirs(integ_dir, exist_ok=True)
        client_ts = os.path.join(integ_dir, "client.ts")
        with open(client_ts, "w", encoding="utf-8") as f:
            f.write(
                'import { createClient } from "@supabase/supabase-js";\n'
                'const SUPABASE_URL = "https://abcdefghijk.supabase.co";\n'
                'const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiJ9.fake.sig";\n'
                'export const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);\n'
            )

        with open(os.path.join(src_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write('{"name": "gestao-tarefas-lovable", "dependencies": {"react": "^18.0.0"}}')

        pipeline = BridgePipeline(src_dir, output_dir=out_dir, domain="app.empresa.com")
        status = pipeline.run()

        assert status == 0

        out_client = os.path.join(out_dir, "src", "integrations", "supabase", "client.ts")
        assert os.path.exists(out_client), "frontend nao foi copiado para o diretorio de saida"

        with open(out_client, "r", encoding="utf-8") as f:
            liberated = f.read()
        assert "supabase.co" not in liberated
        assert "eyJhbGciOiJIUzI1NiJ9.fake.sig" not in liberated
        assert "import.meta.env.VITE_SUPABASE_URL" in liberated
        assert "import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY" in liberated

        # Fonte original nunca deve ser mutada (preview/copia, nao in-place)
        with open(client_ts, "r", encoding="utf-8") as f:
            original_untouched = f.read()
        assert "abcdefghijk.supabase.co" in original_untouched

        assert audit_vendor_lockin(out_dir) == 0


def test_caddyfile_localhost_remove_prefixo_rest_e_storage_antes_do_proxy():
    """Reproduz bug real (achado com curl de verdade contra a stack subida):
    o Caddyfile gerado para dominio "localhost" usava "reverse_proxy" puro
    para /rest/v1/* e /storage/v1/*, que NAO remove o prefixo do caminho --
    PostgREST/Storage recebiam "/rest/v1/tarefas" e devolviam 404, porque
    essas APIs so conhecem o caminho sem o prefixo (ex: "/tarefas")."""
    with tempfile.TemporaryDirectory() as tmpdir:
        packager = DevOpsPackager(tmpdir, domain="localhost")
        caddyfile = packager.generate_caddyfile()
        assert "handle_path /rest/v1/*" in caddyfile
        assert "handle_path /storage/v1/*" in caddyfile
        assert "reverse_proxy /rest/v1/*" not in caddyfile
        assert "reverse_proxy /storage/v1/*" not in caddyfile


def test_pipeline_bridge_stack_lite_padrao_cria_auth_users_emulado():
    """Reproduz bug real (achado rodando `docker compose up` de verdade): o
    pipeline sempre gerava init-db.sql com with_real_auth=True (assumindo
    GoTrue real), mas empacotava a stack Docker "lite" por padrao -- que NAO
    tem GoTrue. Qualquer migracao com FK para auth.users (padrao universal em
    apps Supabase/Lovable) derrubava a inicializacao real do Postgres com
    "relation auth.users does not exist", porque a tabela emulada nunca era
    criada e nenhum GoTrue existia pra cria-la de verdade."""
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as out_dir:
        migrations_dir = os.path.join(src_dir, "supabase", "migrations")
        os.makedirs(migrations_dir, exist_ok=True)
        migration_path = os.path.join(migrations_dir, "0001_tarefas.sql")
        with open(migration_path, "w", encoding="utf-8") as f:
            f.write(
                "create table public.tarefas (\n"
                "  id uuid primary key default gen_random_uuid(),\n"
                "  user_id uuid not null references auth.users(id)\n"
                ");\n"
            )
        with open(os.path.join(src_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write('{"name": "gestao-tarefas-lovable"}')

        pipeline = BridgePipeline(src_dir, output_dir=out_dir, domain="localhost")
        assert pipeline.stack == "lite"
        assert pipeline.run() == 0

        with open(os.path.join(out_dir, "init-db.sql"), "r", encoding="utf-8") as f:
            init_sql = f.read()
        assert "CREATE TABLE IF NOT EXISTS auth.users" in init_sql
        # docker-compose.yml (stack lite) nao deve ter servico "auth"/GoTrue
        with open(os.path.join(out_dir, "docker-compose.yml"), "r", encoding="utf-8") as f:
            compose = f.read()
        assert "supabase/gotrue" not in compose and "supabase/auth" not in compose


def test_pipeline_bridge_liberates_frontend_in_place_when_no_output_dir():
    """Modo padrao (sem --output): pipeline roda no proprio diretorio do projeto,
    e o client.ts la dentro precisa ficar liberado de verdade (nao so o manifesto)."""
    with tempfile.TemporaryDirectory() as project_dir:
        integ_dir = os.path.join(project_dir, "src", "integrations", "supabase")
        os.makedirs(integ_dir, exist_ok=True)
        with open(os.path.join(integ_dir, "client.ts"), "w", encoding="utf-8") as f:
            f.write(
                'const SUPABASE_URL = "https://minhaempresa.supabase.co";\n'
                'export const supabase = createClient(SUPABASE_URL, "chave-anon-fake");\n'
            )
        with open(os.path.join(project_dir, "package.json"), "w", encoding="utf-8") as f:
            f.write('{"name": "gestao-tarefas-lovable"}')

        pipeline = BridgePipeline(project_dir, domain="localhost")
        assert pipeline.run() == 0

        with open(os.path.join(integ_dir, "client.ts"), "r", encoding="utf-8") as f:
            content = f.read()
        assert "supabase.co" not in content
        assert audit_vendor_lockin(project_dir) == 0
