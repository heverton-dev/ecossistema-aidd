# -*- coding: utf-8 -*-
import os
import json
import tempfile
import pytest
from aidd_bridge.scanner import LovableScanner
from aidd_bridge.data_bridge import DataBridge
from aidd_bridge.devops import DevOpsPackager
from aidd_bridge.unifier import MultiAppUnifier
from aidd_bridge.auth_migrator import plan_migration

@pytest.fixture
def mock_lovable_project(tmp_path):
    proj = tmp_path / "mock-app"
    proj.mkdir()
    
    # package.json
    pkg = {
        "name": "mock-lovable",
        "version": "1.0.0",
        "dependencies": {"react": "^18.2.0", "@supabase/supabase-js": "^2.39.0"}
    }
    (proj / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

    # src/App.tsx com rotas
    src = proj / "src"
    src.mkdir()
    (src / "App.tsx").write_text("""
    import { Route, Routes } from "react-router-dom";
    export default function App() {
        return (
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
        );
    }
    """, encoding="utf-8")

    # migrations
    mig = proj / "supabase" / "migrations"
    mig.mkdir(parents=True)
    (mig / "20260101_init.sql").write_text("""
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "supabase_vault";
    CREATE TABLE users (id UUID PRIMARY KEY, name TEXT);
    ALTER PUBLICATION supabase_realtime ADD TABLE users;
    """, encoding="utf-8")

    return str(proj)

def test_scanner(mock_lovable_project):
    scanner = LovableScanner(mock_lovable_project)
    manifest = scanner.scan()
    assert manifest["package_info"]["name"] == "mock-lovable"
    assert len(manifest["routes"]) == 2
    assert manifest["database"]["has_supabase"] is True
    assert len(manifest["database"]["migrations"]) == 1

def test_data_bridge(mock_lovable_project):
    scanner = LovableScanner(mock_lovable_project)
    manifest = scanner.scan()
    bridge = DataBridge(manifest["database"]["migrations"])
    sql = bridge.generate_consolidated_init_sql()
    assert "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" in sql
    assert "-- [AIDD-BRIDGE REMOVED PROPRIETARY CLOUD HOOK]" in sql
    assert "ALTER PUBLICATION supabase_realtime" in sql
    assert "CREATE TABLE IF NOT EXISTS auth.users" in sql
    # auth.uid()/role()/email() precisam ler tanto a GUC antiga por-claim
    # quanto a GUC JSON atual do PostgREST (>=11 removeu db-use-legacy-gucs);
    # depender só da antiga faz auth.uid() sempre voltar NULL e travar todo RLS.
    assert "request.jwt.claim.sub" in sql
    assert "request.jwt.claims" in sql

def test_data_bridge_with_real_auth_skips_fake_users_table(mock_lovable_project):
    scanner = LovableScanner(mock_lovable_project)
    manifest = scanner.scan()
    bridge = DataBridge(manifest["database"]["migrations"])
    sql = bridge.generate_consolidated_init_sql(with_real_auth=True)
    assert "CREATE TABLE IF NOT EXISTS auth.users" not in sql
    assert "GRANT SELECT ON auth.users" not in sql
    assert "CREATE SCHEMA IF NOT EXISTS auth;" in sql

def test_devops_packager(tmp_path):
    packager = DevOpsPackager(str(tmp_path), domain="app.meusite.com")
    files = packager.export_all()
    assert "Dockerfile" in files
    assert "docker-compose.yml" in files
    assert "Caddyfile" in files
    assert os.path.exists(files["docker-compose.yml"])
    
    compose_content = open(files["docker-compose.yml"], encoding="utf-8").read()
    assert "postgrest" in compose_content
    assert "postgres:16-alpine" in compose_content

def test_unifier(mock_lovable_project, tmp_path):
    out = tmp_path / "unified-app"
    unifier = MultiAppUnifier([mock_lovable_project], str(out))
    res = unifier.merge()
    assert res["status"] == "success"
    assert os.path.exists(out / "package.json")
    assert os.path.exists(out / "src" / "AppMasterRouter.tsx")

def test_devops_full_stack_uses_pinned_official_supabase_images(tmp_path):
    packager = DevOpsPackager(str(tmp_path), domain="app.meusite.com", stack="full")
    swarm_yaml = packager.generate_docker_compose_swarm()

    assert "supabase/postgres:15.14.1.170" in swarm_yaml
    assert "supabase/gotrue:v2.197.0" in swarm_yaml
    assert "kong:3.8.0" in swarm_yaml
    assert ":latest" not in swarm_yaml.split("web:")[1].split("kong:")[0]  # nunca :latest nas imagens do stack completo

def test_devops_full_stack_kong_routes_and_entrypoint_are_valid_yaml(tmp_path):
    import yaml

    packager = DevOpsPackager(str(tmp_path), domain="app.meusite.com", stack="full")
    compose = yaml.safe_load(packager.generate_docker_compose_swarm())
    kong_conf = yaml.safe_load(packager.generate_kong_config())

    assert set(compose["services"].keys()) == {"web", "kong", "auth", "rest", "db"}
    # entrypoint precisa sobreviver ao parse do YAML igual ao comando real
    # (verificado com um deploy descartavel real em 2026-09-10 — home do
    # usuario "kong" nao existe/nao e gravavel, por isso usa /tmp)
    assert compose["services"]["kong"]["entrypoint"] == (
        'bash -c \'eval "echo \\"$$(cat /tmp/temp.yml)\\"" > /tmp/kong.yml '
        "&& /docker-entrypoint.sh kong docker-start'"
    )
    assert compose["services"]["kong"]["environment"]["KONG_DECLARATIVE_CONFIG"] == "/tmp/kong.yml"

    route_names = [s["name"] for s in kong_conf["services"]]
    assert "auth-v1" in route_names
    assert "rest-v1" in route_names

def test_devops_lite_vs_full_stack_selection(tmp_path):
    lite = DevOpsPackager(str(tmp_path), domain="app.meusite.com").generate_docker_compose_swarm()
    full = DevOpsPackager(str(tmp_path), domain="app.meusite.com", stack="full").generate_docker_compose_swarm()
    assert "kong" not in lite
    assert "kong" in full

def test_plan_migration_inserts_only_new_accounts():
    source_users = [
        {"id": "u1", "email": "ja-existe@example.com"},
        {"id": "u2", "email": "conta-nova@example.com"},
    ]
    existing_target_ids = {"u1"}  # já migrado ou já criado manualmente no destino

    plan = plan_migration(source_users, existing_target_ids)

    assert plan["total_source"] == 2
    assert [u["id"] for u in plan["to_insert"]] == ["u2"]
    assert [u["id"] for u in plan["skipped_existing"]] == ["u1"]

def test_plan_migration_never_touches_existing_accounts_on_rerun():
    source_users = [{"id": "u1", "email": "a@example.com"}, {"id": "u2", "email": "b@example.com"}]
    # simula rodar a migração de novo depois que u2 já foi inserido
    plan_second_run = plan_migration(source_users, existing_target_ids={"u1", "u2"})
    assert plan_second_run["to_insert"] == []
    assert len(plan_second_run["skipped_existing"]) == 2

def test_plan_migration_supports_custom_id_key():
    # auth.identities usa "identity_id" em versões recentes do GoTrue, não "id"
    source_identities = [
        {"identity_id": "i1", "user_id": "u1", "provider": "email"},
        {"identity_id": "i2", "user_id": "u2", "provider": "email"},
    ]
    plan = plan_migration(source_identities, existing_target_ids={"i1"}, id_key="identity_id")
    assert [i["identity_id"] for i in plan["to_insert"]] == ["i2"]

def test_devops_swarm_postgrest_strips_rest_prefix(tmp_path):
    packager = DevOpsPackager(str(tmp_path), domain="app.meusite.com")
    swarm_yaml = packager.generate_docker_compose_swarm()
    assert "middlewares.app-meusite-com-api-strip.stripprefix.prefixes=/rest/v1" in swarm_yaml
    assert "traefik.http.routers.app-meusite-com-api.middlewares=app-meusite-com-api-strip" in swarm_yaml