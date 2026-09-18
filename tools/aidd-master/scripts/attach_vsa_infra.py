# -*- coding: utf-8 -*-
"""
Conecta o backend VSA (gerado por provision_backend_only) a infraestrutura
Docker/Caddy JA existente no diretorio do projeto -- tipicamente a saida do
aidd-bridge (FLUXO 03), que preserva o frontend original e ja definiu seus
proprios servicos (web, db, postgrest, storage, caddy). Nunca regenera esses
arquivos do zero: so acrescenta o servico "api" (backend Python VSA) e as
rotas do Quarteto Sine Qua Non (/docs, /webhooks, /mcp, /metrics) por cima.
"""

import os
import re

import yaml

API_SERVICE_NAME = "api"
API_PORT = 3000


def write_api_dockerfile(project_dir: str) -> str:
    """Copia o Dockerfile core (non-root, healthcheck real) como Dockerfile.api,
    isolado do Dockerfile do frontend que o aidd-bridge ja escreveu na raiz.
    O build context continua sendo a raiz do projeto (igual ao Dockerfile do
    frontend), entao as instrucoes COPY sao reescritas com o prefixo
    "backend/" -- e la que provision_backend_only() gera requirements.txt/src/."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template = os.path.join(repo_root, "templates", "core", "Dockerfile")
    if not os.path.exists(template):
        template = os.path.join(repo_root, "templates", "v2", "Dockerfile")

    with open(template, "r", encoding="utf-8") as f:
        conteudo = f.read()
    conteudo = conteudo.replace("COPY requirements.txt", "COPY backend/requirements.txt")
    conteudo = conteudo.replace("COPY --chown=aidduser:aiddgroup src/", "COPY --chown=aidduser:aiddgroup backend/src/")

    dest = os.path.join(project_dir, "Dockerfile.api")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return dest


def merge_backend_service_into_compose(project_dir: str) -> str:
    compose_path = os.path.join(project_dir, "docker-compose.yml")
    with open(compose_path, "r", encoding="utf-8") as f:
        compose = yaml.safe_load(f) or {}

    compose.setdefault("services", {})
    compose["services"][API_SERVICE_NAME] = {
        "build": {"context": ".", "dockerfile": "Dockerfile.api"},
        "container_name": "aidd_vsa_backend",
        "restart": "unless-stopped",
        "environment": {
            "DB_PATH": "/app/data/suite.db",
        },
        "volumes": ["backend_data:/app/data"],
        "expose": [str(API_PORT)],
    }

    compose.setdefault("volumes", {})
    compose["volumes"].setdefault("backend_data", None)

    with open(compose_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(compose, f, sort_keys=False, default_flow_style=False)

    return compose_path


QUARTETO_PATHS = ["/docs*", "/webhooks*", "/mcp*", "/metrics*", "/openapi.json", "/health"]


def _quarteto_handle_blocks() -> str:
    blocks = []
    for path in QUARTETO_PATHS:
        blocks.append(
            f"    handle {path} {{\n        reverse_proxy {API_SERVICE_NAME}:{API_PORT}\n    }}\n"
        )
    return "".join(blocks)


def merge_backend_routes_into_caddyfile(project_dir: str) -> str:
    """Insere as rotas nativas do Quarteto Sine Qua Non no Caddyfile que o
    aidd-bridge ja gerou, sempre ANTES do "handle {}" catch-all do frontend
    (Caddy usa a primeira "handle" que casar; um catch-all antes das rotas
    especificas as engoliria)."""
    caddyfile_path = os.path.join(project_dir, "Caddyfile")
    with open(caddyfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    if any(path in content for path in QUARTETO_PATHS):
        return caddyfile_path  # ja mesclado (idempotente)

    catchall_pattern = re.compile(r"(\n)(    handle \{\n        reverse_proxy web:80\n    \}\n\})")
    novo_conteudo, n = catchall_pattern.subn(
        lambda m: m.group(1) + _quarteto_handle_blocks() + m.group(2), content, count=1
    )
    if n == 0:
        raise ValueError(
            f"Nao encontrei o bloco catch-all do frontend em {caddyfile_path} "
            "para inserir as rotas do Quarteto Sine Qua Non antes dele."
        )

    with open(caddyfile_path, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)

    return caddyfile_path


def attach_infra(project_dir: str) -> dict:
    """Roda os 3 passos de conexao (Dockerfile.api + compose + Caddyfile) se
    -- e somente se -- o projeto ja tiver uma stack Docker/Caddy previa (ex:
    saida do aidd-bridge). Sem isso, e um monolito puro do Fluxo 01/02 que ja
    gera seu proprio Dockerfile/compose via `master init` -- nao ha nada a
    conectar aqui."""
    compose_path = os.path.join(project_dir, "docker-compose.yml")
    caddyfile_path = os.path.join(project_dir, "Caddyfile")
    if not (os.path.exists(compose_path) and os.path.exists(caddyfile_path)):
        return {"conectado": False, "motivo": "sem docker-compose.yml/Caddyfile previos (nao e saida do bridge)"}

    dockerfile_api = write_api_dockerfile(project_dir)
    merge_backend_service_into_compose(project_dir)
    merge_backend_routes_into_caddyfile(project_dir)
    return {
        "conectado": True,
        "dockerfile_api": dockerfile_api,
        "compose": compose_path,
        "caddyfile": caddyfile_path,
    }
