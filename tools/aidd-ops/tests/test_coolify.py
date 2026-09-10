# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — Testes do cliente da API v1 do Coolify (Anti-NIH #19)
=============================================================================
Valida contra um servidor HTTP REAL local que implementa o contrato da API
v1 do Coolify (health público, Bearer auth 401, create app/public, envs,
deploy) — nada de mocks de rede. Também cobre os caminhos de erro
(401, 404, conexão recusada, token ausente, dry-run do CLI).
"""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_SCRIPT = os.path.join(TOOL_ROOT, "scripts", "pipeline_ops.py")

sys.path.insert(0, TOOL_ROOT)
sys.path.insert(0, os.path.join(TOOL_ROOT, "src"))

from src.core.coolify import CoolifyClient, CoolifyManager  # noqa: E402

TOKEN_TESTE = "teste-token-abc-123"


def _fabricar_servidor(payload_criar=None):
    """Sobe um http.server real implementando o contrato Coolify v1.

    Retorna (servidor, porta, requisicoes: list). Requisicoes registra
    (metodo, caminho, headers, body_json) de cada request para asserts.
    """
    requisicoes = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def _autorizado(self):
            return self.headers.get("Authorization", "") == f"Bearer {TOKEN_TESTE}"

        def _resposta(self, status, corpo, content_type="application/json"):
            if isinstance(corpo, (dict, list)):
                corpo_b = json.dumps(corpo).encode("utf-8")
            else:
                corpo_b = corpo.encode("utf-8") if isinstance(corpo, str) else corpo
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(corpo_b)))
            self.end_headers()
            self.wfile.write(corpo_b)

        def _nao_autorizado(self):
            self._resposta(401, {"message": "Invalid token."})

        def do_GET(self):
            requisicoes.append(("GET", self.path, dict(self.headers)))
            if self.path == "/api/v1/health":
                self._resposta(200, "OK", content_type="text/plain")
                return
            if not self._autorizado():
                self._nao_autorizado()
                return
            if self.path == "/api/v1/version":
                self._resposta(200, {"version": "4.0.4"})
            elif self.path == "/api/v1/servers":
                self._resposta(200, [{"uuid": "srv-1", "name": "lab-local", "ip": "10.0.0.5"}])
            elif self.path == "/api/v1/applications":
                self._resposta(200, [
                    {"uuid": "app-9", "name": "aidd-ops-intake", "domains": ["intake.test"]},
                ])
            elif self.path.startswith("/api/v1/applications/app-9"):
                self._resposta(200, {
                    "uuid": "app-9", "name": "aidd-ops-intake",
                    "status": "running", "fqdn": "intake.test",
                })
            else:
                self._resposta(404, {"message": "Resource not found."})

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            corpo_b = self.rfile.read(length) if length else b""
            body = json.loads(corpo_b.decode("utf-8")) if corpo_b else None
            requisicoes.append(("POST", self.path, dict(self.headers), body))
            if not self._autorizado():
                self._nao_autorizado()
                return
            if self.path == "/api/v1/applications/public":
                payload = payload_criar if payload_criar is not None else {"uuid": "app-novo-uuid-1"}
                self._resposta(201, payload)
            elif self.path == "/api/v1/applications/app-9/envs":
                self._resposta(201, {"uuid": "env-1"})
            elif self.path.split("?")[0] == "/api/v1/deploy":
                self._resposta(200, {"deployment_uuid": "dep-1"})
            else:
                self._resposta(404, {"message": "Resource not found."})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_port, requisicoes


@pytest.fixture()
def coolify_local():
    server, porta, requisicoes = _fabricar_servidor()
    yield {"porta": porta, "requisicoes": requisicoes, "server": server}
    server.shutdown()
    server.server_close()


def _url(porta: int) -> str:
    return f"http://127.0.0.1:{porta}"


# ── health (sem autenticação) ──

def test_health_ok_dispensa_token(coolify_local):
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]))
    res = cliente.checar_health()
    assert res.sucesso is True
    assert res.valor is not None
    assert res.valor["ok"] is True


def test_health_falha_conexao():
    cliente = CoolifyClient(base_url="http://127.0.0.1:59999")
    res = cliente.checar_health()
    assert res.sucesso is False
    assert res.codigo == "CONEXAO_RECUSADA"


def test_versao_exige_token():
    cliente = CoolifyClient(base_url="http://127.0.0.1:59999")
    res = cliente.obter_versao()
    assert res.sucesso is False
    assert res.codigo == "TOKEN_AUSENTE"


# ── endpoints autenticados ──

def test_versao_ok_com_token(coolify_local):
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]), api_token=TOKEN_TESTE)
    res = cliente.obter_versao()
    assert res.sucesso is True
    assert res.valor is not None
    assert "version" in res.valor


def test_token_invalido_retorna_401(coolify_local):
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]), api_token="token-errado")
    res = cliente.listar_servidores()
    assert res.sucesso is False
    assert res.codigo == "HTTP_401"


def test_listar_servidores(coolify_local):
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]), api_token=TOKEN_TESTE)
    res = cliente.listar_servidores()
    assert res.sucesso is True
    assert res.valor is not None
    assert res.valor[0]["uuid"] == "srv-1"


def test_listar_apps(coolify_local):
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]), api_token=TOKEN_TESTE)
    res = cliente.listar_apps()
    assert res.sucesso is True
    assert res.valor is not None
    assert res.valor[0]["name"] == "aidd-ops-intake"


def test_obter_app(coolify_local):
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]), api_token=TOKEN_TESTE)
    res = cliente.obter_app("app-9")
    assert res.sucesso is True
    assert res.valor is not None
    assert res.valor["status"] == "running"


# ── criar app dockerfile (POST /applications/public) ──

def test_criar_app_dockerfile_payload_contrato(coolify_local):
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]), api_token=TOKEN_TESTE)
    res = cliente.criar_app_dockerfile(
        project_uuid="proj-1",
        server_uuid="srv-1",
        environment_name="production",
        git_repository="https://github.com/org/ecossistema-aidd.git",
        base_directory="tools/aidd-ops",
        dockerfile_location="Dockerfile.intake",
        ports_exposes=[8501],
        domains=["intake.test"],
        nome="intake-prod",
    )
    assert res.sucesso is True
    assert res.valor == "app-novo-uuid-1"

    posts = [r for r in coolify_local["requisicoes"] if r[0] == "POST" and r[1] == "/api/v1/applications/public"]
    assert len(posts) == 1
    _, caminho, headers, body = posts[0]
    assert headers.get("Authorization") == f"Bearer {TOKEN_TESTE}"
    assert body["project_uuid"] == "proj-1"
    assert body["server_uuid"] == "srv-1"
    assert body["environment_name"] == "production"
    assert body["build_pack"] == "dockerfile"
    assert body["base_directory"] == "tools/aidd-ops"
    assert body["dockerfile_location"] == "Dockerfile.intake"
    assert body["ports_exposes"] == [8501]
    assert body["domains"] == ["intake.test"]
    assert body["instant_deploy"] is False


def test_criar_app_padroes_do_intake(coolify_local):
    """Sem base_dir/dockerfile/ports explicitos, usa convenção do Intake Web."""
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]), api_token=TOKEN_TESTE)
    res = cliente.criar_app_dockerfile("proj-1", "srv-1", "production", "https://git.repo/x.git")
    assert res.sucesso is True
    _, _, _, body = next(r for r in coolify_local["requisicoes"] if r[0] == "POST" and r[1].endswith("/public"))
    assert body["base_directory"] == "tools/aidd-ops"
    assert body["dockerfile_location"] == "Dockerfile.intake"
    assert body["ports_exposes"] == [8501]
    assert body["name"] == "aidd-ops-intake"


def test_criar_app_sem_uuid_na_resposta_fail():
    """Resposta 201 sem uuid → ERRO_RESPOSTA (nunca fabrica uuid)."""
    server, porta, _ = _servidor_sem_uuid()
    try:
        cliente = CoolifyClient(base_url=_url(porta), api_token=TOKEN_TESTE)
        res = cliente.criar_app_dockerfile("proj-1", "srv-1", "production", "https://git.repo/x.git")
        assert res.sucesso is False
        assert res.codigo == "ERRO_RESPOSTA"
    finally:
        server.shutdown()
        server.server_close()


def _servidor_sem_uuid():
    return _fabricar_servidor(payload_criar={})


# ── envs e deploy ──

def test_definir_env_cria_pares(coolify_local):
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]), api_token=TOKEN_TESTE)
    res = cliente.definir_env("app-9", [("CHAVE_A", "1"), ("STREAMLIT_SERVER_HEADLESS", "true")])
    assert res.sucesso is True
    assert res.valor == ["CHAVE_A", "STREAMLIT_SERVER_HEADLESS"]

    posts = [r for r in coolify_local["requisicoes"] if r[0] == "POST" and r[1] == "/api/v1/applications/app-9/envs"]
    assert len(posts) == 2
    assert posts[0][3]["key"] == "CHAVE_A"
    assert posts[1][3]["key"] == "STREAMLIT_SERVER_HEADLESS"
    assert posts[0][3]["is_literal"] is True
    assert posts[0][3]["is_preview"] is False


def test_definir_env_sin_pares_fail():
    cliente = CoolifyClient(base_url="http://127.0.0.1:1", api_token=TOKEN_TESTE)
    res = cliente.definir_env("app-9", [])
    assert res.sucesso is False
    assert res.codigo == "PARAM_INVALIDO"


def test_disparar_deploy_force(coolify_local):
    cliente = CoolifyClient(base_url=_url(coolify_local["porta"]), api_token=TOKEN_TESTE)
    res = cliente.disparar_deploy("app-9", force=True)
    assert res.sucesso is True
    assert res.valor is not None
    assert res.valor["deployment_uuid"] == "dep-1"
    quaisquer = [r for r in coolify_local["requisicoes"] if r[0] == "POST" and r[1].startswith("/api/v1/deploy")]
    assert len(quaisquer) == 1
    assert quaisquer[0][1] == "/api/v1/deploy?uuid=app-9&force=true"


# ── CLI pipeline_ops.py coolify ──

def _run_coolify(*args, env_extra=None):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, PIPELINE_SCRIPT, "coolify", *args],
        capture_output=True, text=True, timeout=30, cwd=TOOL_ROOT, env=env,
    )


def test_cli_health(coolify_local):
    res = _run_coolify("health", "--url", _url(coolify_local["porta"]))
    assert res.returncode == 0, res.stdout + res.stderr
    assert "OK" in res.stdout


def test_cli_version_usando_env(coolify_local):
    res = _run_coolify(
        "version",
        env_extra={"COOLIFY_BASE_URL": _url(coolify_local["porta"]), "COOLIFY_API_TOKEN": TOKEN_TESTE},
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "4.0.4" in res.stdout


def test_cli_url_ausente():
    res = _run_coolify("version")
    assert res.returncode == 1
    assert "URL base" in res.stdout


def test_cli_create_dry_run_padrao(coolify_local):
    """Sem --real o create NÃO toca na API (dry-run por padrão)."""
    antes = len(coolify_local["requisicoes"])
    res = _run_coolify(
        "create",
        "--url", _url(coolify_local["porta"]),
        "--token", TOKEN_TESTE,
        "--project-uuid", "proj-1",
        "--server-uuid", "srv-1",
        "--repo", "https://github.com/org/ecossistema-aidd.git",
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "DRY-RUN" in res.stdout
    assert len(coolify_local["requisicoes"]) == antes


def test_cli_create_real(coolify_local):
    res = _run_coolify(
        "create",
        "--url", _url(coolify_local["porta"]),
        "--token", TOKEN_TESTE,
        "--project-uuid", "proj-1",
        "--server-uuid", "srv-1",
        "--repo", "https://github.com/org/ecossistema-aidd.git",
        "--real",
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "app-novo-uuid-1" in res.stdout
    posts = [r for r in coolify_local["requisicoes"] if r[0] == "POST" and r[1] == "/api/v1/applications/public"]
    assert len(posts) == 1


def test_cli_deploy_dry_run(coolify_local):
    antes = len(coolify_local["requisicoes"])
    res = _run_coolify("deploy", "--url", _url(coolify_local["porta"]), "--token", TOKEN_TESTE, "--app", "app-9")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "DRY-RUN" in res.stdout
    assert len(coolify_local["requisicoes"]) == antes


# ── CoolifyManager (contrato de pipeline_ops — DeployOrchestrator) ──

_SERVICOS_STACK = [
    {"nome": "Twenty", "porta_interna": 3000, "cpus": "1.0", "memory": "1024M"},
    {"nome": "Postgres", "porta_interna": 5432, "cpus": "2.0", "memory": "4096M"},
]


def test_manager_orquestrar_stack_dry_run():
    manager = CoolifyManager(dry_run=True)
    res = manager.orquestrar_stack("AIDD-Lab", "lab", _SERVICOS_STACK, "lab.local")
    assert res.sucesso is True
    assert res.valor is not None
    assert res.valor["projeto"] == "AIDD-Lab"
    assert res.valor["ambiente"] == "lab"
    assert len(res.valor["apps"]) == 2
    app25 = res.valor["apps"][0]
    assert app25["nome_app"] == "aidd-lab-twenty"
    assert app25["ports_exposes"] == [3000]
    assert app25["dominios"] == ["twenty.lab.local"]
    assert app25["limits"]["memory"] == "1024M"


def test_manager_orquestrar_stack_servicos_invalidos():
    manager = CoolifyManager(dry_run=True)
    res = manager.orquestrar_stack("AIDD", "lab", [{"nome": "SemPorta"}], "lab.local")
    assert res.sucesso is False
    assert res.codigo == "PARAM_INVALIDO"


def test_manager_real_sem_credenciais_fail_honesto():
    manager = CoolifyManager(dry_run=False)
    res = manager.orquestrar_stack("AIDD", "lab", _SERVICOS_STACK, "lab.local")
    assert res.sucesso is False
    assert res.codigo == "TOKEN_AUSENTE"


def test_manager_verificar_isolamento_vps_ok():
    manager = CoolifyManager(dry_run=True)
    res_orq = manager.orquestrar_stack("AIDD", "lab", _SERVICOS_STACK, "lab.local")
    assert res_orq.valor is not None
    res_iso = manager.verificar_isolamento_vps(res_orq.valor)
    assert res_iso is not None and res_iso.sucesso is True
    assert res_iso.valor is not None
    assert res_iso.valor["apps_auditados"] == 2


def test_manager_verificar_isolamento_vps_violacao_porta_host():
    manager = CoolifyManager(dry_run=True)
    plano = {"apps": [{"nome_app": "app-critico", "ports_exposes": [80]}]}
    res = manager.verificar_isolamento_vps(plano)
    assert res.sucesso is False
    assert res.codigo == "ISOLAMENTO_VIOLADO"


def test_manager_appshell_whitelabel_dry_run():
    manager = CoolifyManager(dry_run=True)
    res = manager.configurar_appshell_whitelabel(
        nome_instancia="Portal Lab", marca="AIDD", logo_url="https://x/logo.svg",
        dashboard_fqdn="painel.lab.local",
    )
    assert res.sucesso is True
    assert res.valor is not None
    assert res.valor["marca"] == "AIDD"
    assert res.valor["dry_run"] is True