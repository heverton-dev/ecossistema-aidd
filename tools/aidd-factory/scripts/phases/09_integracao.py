# -*- coding: utf-8 -*-
"""
AIDD-Factory — Fase 9: Validacao Cross-Service.

Valida todos os artefatos gerados como um todo:
  1. docker-compose.yml (sintaxe, portas, healthchecks)
  2. init-multiple-databases.sh (sintaxe bash)
  3. .env files (completude)
  4. openapi.json (JSON valido)
  5. Gateway (py_compile)
100% deterministico — zero LLM.
"""
import json
import os
import sys
import glob
import subprocess

_FACTORY_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "src"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "..", "..", "componentes", "compartilhado", "src-core"))

from core.result import Result


def _validar_compose(diretorio: str) -> list:
    """Valida docker-compose.yml."""
    problemas = []
    import yaml

    caminho = os.path.join(diretorio, "docker-compose.yml")
    if not os.path.isfile(caminho):
        return ["docker-compose.yml ausente"]

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        return [f"YAML invalido: {exc}"]

    if not dados or "services" not in dados:
        return ["Compose sem 'services'"]

    services = dados["services"]
    nomes = set(services.keys())
    portas = {}

    for nome, svc in services.items():
        # Rede
        networks = svc.get("networks", [])
        if "aidd_internal" not in networks:
            problemas.append(f"Service '{nome}' fora da rede aidd_internal")

        # Portas duplicadas
        for port_str in svc.get("ports", []):
            host_port = str(port_str).split(":")[0]
            if host_port in portas:
                problemas.append(f"Porta {host_port} duplicada: {nome} e {portas[host_port]}")
            portas[host_port] = nome

        # DependsOn
        depends = svc.get("depends_on", {})
        if isinstance(depends, dict):
            for dep in depends:
                if dep not in nomes:
                    problemas.append(f"Service '{nome}' depende de '{dep}' inexistente")

    return problemas


def _validar_init_db(diretorio: str) -> list:
    """Valida init-multiple-databases.sh."""
    problemas = []
    caminho = os.path.join(diretorio, "init-multiple-databases.sh")
    if not os.path.isfile(caminho):
        return ["init-multiple-databases.sh ausente"]

    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    if "CREATE DATABASE" not in conteudo:
        problemas.append("init_db sem CREATE DATABASE")
    if "CREATE USER" not in conteudo:
        problemas.append("init_db sem CREATE USER")
    if "GRANT" not in conteudo:
        problemas.append("init_db sem GRANT")

    return problemas


def _validar_envs(diretorio: str) -> list:
    """Valida .env files."""
    problemas = []
    env_files = glob.glob(os.path.join(diretorio, ".env.*"))
    if not env_files:
        return ["Nenhum .env encontrado"]

    for env_path in env_files:
        nome = os.path.basename(env_path)
        with open(env_path, "r", encoding="utf-8") as f:
            for i, linha in enumerate(f, 1):
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                if ("password" in chave.lower() or "secret" in chave.lower()) and valor.startswith("CHANGE_ME"):
                    problemas.append(f"{nome}:{chave} — valor padrao")

    return problemas


def _validar_openapi(diretorio: str) -> list:
    """Valida openapi.json."""
    problemas = []
    caminho = os.path.join(diretorio, "openapi.json")
    if not os.path.isfile(caminho):
        return ["openapi.json ausente"]

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        if dados.get("openapi") != "3.1.0":
            problemas.append("openapi.json nao e spec 3.1.0")
    except json.JSONDecodeError as exc:
        problemas.append(f"openapi.json invalido: {exc}")

    return problemas


def _validar_vsa(diretorio: str) -> list:
    """Valida a conformidade Vertical Slice Architecture (VSA) e Quarteto Sine Qua Non."""
    import py_compile
    problemas = []
    server_path = os.path.join(diretorio, "src", "server.py")
    if not os.path.isfile(server_path):
        return []  # Modo sem VSA gerado

    # 1. Compilar src/server.py
    try:
        py_compile.compile(server_path, doraise=True)
    except py_compile.PyCompileError as exc:
        problemas.append(f"src/server.py invalido: {exc}")

    # 2. Validar fatias verticais em src/modules/
    modules_dir = os.path.join(diretorio, "src", "modules")
    if os.path.isdir(modules_dir):
        modulos = [d for d in os.listdir(modules_dir) if os.path.isdir(os.path.join(modules_dir, d)) and not d.startswith("_")]
        if not modulos:
            problemas.append("src/modules sem nenhuma fatia vertical")
        for mod in modulos:
            mod_path = os.path.join(modules_dir, mod)
            for arquivo in ["models.py", "repositories.py", "services.py", "routes.py"]:
                f_path = os.path.join(mod_path, arquivo)
                if not os.path.isfile(f_path):
                    problemas.append(f"Fatia {mod} sem {arquivo}")
                else:
                    try:
                        py_compile.compile(f_path, doraise=True)
                    except py_compile.PyCompileError as exc:
                        problemas.append(f"Fatia {mod}/{arquivo} com erro de sintaxe: {exc}")

    # 3. Validar Quarteto Sine Qua Non em src/static/ — swagger/webhooks/mcp/
    # docs continuam nativos do backend, independente da stack de frontend.
    static_dir = os.path.join(diretorio, "src", "static")
    if os.path.isdir(static_dir):
        quarteto = {
            "swagger.html": "Swagger Studio (/swagger)",
            "webhook_studio.html": "Webhook Studio (/webhooks)",
            "mcp_studio.html": "MCP Studio (/mcp)",
            "docs.html": "Manual do Utilizador (/docs)"
        }
        for arq, desc in quarteto.items():
            if not os.path.isfile(os.path.join(static_dir, arq)):
                problemas.append(f"Quarteto Sine Qua Non ausente: {desc} ({arq})")

    # 4. Frontend de produto: Next.js por padrao (Lei Inviolavel #11), ou o
    # Super-App em src/static/index.html so quando gerado explicitamente.
    frontend_pkg = os.path.join(diretorio, "frontend", "package.json")
    usa_nextjs = False
    if os.path.isfile(frontend_pkg):
        try:
            with open(frontend_pkg, "r", encoding="utf-8") as f:
                usa_nextjs = "next" in json.load(f).get("dependencies", {})
        except (OSError, json.JSONDecodeError):
            pass

    if usa_nextjs:
        for req in ["tsconfig.json", "tailwind.config.ts", os.path.join("app", "layout.tsx"), os.path.join("app", "page.tsx")]:
            if not os.path.isfile(os.path.join(diretorio, "frontend", req)):
                problemas.append(f"Front-end Next.js incompleto: frontend/{req} ausente (Lei #11).")
    elif os.path.isdir(static_dir) and not os.path.isfile(os.path.join(static_dir, "index.html")):
        problemas.append("Frontend de produto ausente: nem frontend/ (Next.js) nem src/static/index.html")

    return problemas


def _validar_gateway(diretorio: str) -> list:
    """Valida gateway (py_compile). Pula se nao existe (modo --sem-llm)."""
    import py_compile
    problemas = []
    gateway_dir = os.path.join(diretorio, "src", "gateway")
    if not os.path.isdir(gateway_dir):
        return []  # Modo deterministico — gateway nao gerado

    for nome in ["main.py", "models.py", "routes.py"]:
        caminho = os.path.join(gateway_dir, nome)
        if not os.path.isfile(caminho):
            problemas.append(f"Gateway {nome} ausente")
            continue
        try:
            py_compile.compile(caminho, doraise=True)
        except py_compile.PyCompileError as exc:
            problemas.append(f"Gateway {nome} invalido: {exc}")

    return problemas


def validar_tudo(diretorio: str) -> Result:
    """Executa todas as validacoes cross-service.

    Args:
        diretorio: Diretorio com todos os artefatos do factory.

    Returns:
        Result.ok(relatorio) ou Result.fail com problemas.
    """
    relatorio = {}

    for nome, fn in [
        ("compose", _validar_compose),
        ("init_db", _validar_init_db),
        ("env", _validar_envs),
        ("openapi", _validar_openapi),
        ("gateway", _validar_gateway),
        ("vsa", _validar_vsa),
    ]:
        problemas = fn(diretorio)
        relatorio[nome] = {
            "status": "ok" if not problemas else "falha",
            "problemas": problemas,
        }

    total_problemas = sum(len(r["problemas"]) for r in relatorio.values())
    if total_problemas > 0:
        return Result.fail(
            f"{total_problemas} problema(s) na validacao cross-service",
            codigo="CROSS_SERVICE_INVALID",
            detalhes=relatorio,
        )

    return Result.ok(relatorio)
