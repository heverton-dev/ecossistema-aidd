#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP: Docker MCP (Inspeção e Validação Read-Only)

Servidor MCP que usa o SDK oficial do Model Context Protocol
(`modelcontextprotocol/python-sdk`). Expose tools exclusivamente de
validação e leitura:
- docker compose config (validação sintática de compose sem subir nada)
- docker ps (status de contêineres)
- docker logs (inspeção de logs de serviços)

NOTA DE ESCOPO: Operações destrutivas (down, rm, stop) NÃO são implementadas neste
pacote, seguindo estritamente a Definição de Pronto do Pacote 5.
"""

import os
import shutil
import subprocess
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

NOME_SERVIDOR = "docker-mcp"
DESCRICAO_SERVIDOR = "Servidor MCP para inspeção e validação determinística de contêineres e templates Docker Compose (Read-Only)."

mcp = FastMCP(NOME_SERVIDOR, instructions=DESCRICAO_SERVIDOR)


def _executar_cmd(cmd_list: list, cwd: Optional[str] = None) -> dict:
    """Executa um comando local com subprocess de forma segura sem shell livre."""
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return {
            "sucesso": False,
            "exit_code": 127,
            "erro": "Binário 'docker' não encontrado no PATH do sistema",
            "stdout": "",
            "stderr": "docker: command not found"
        }

    try:
        proc = subprocess.run(
            cmd_list,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "sucesso": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "sucesso": False,
            "exit_code": 124,
            "erro": "Timeout ao executar comando Docker",
            "stdout": "",
            "stderr": "Comando excedeu 30 segundos"
        }
    except Exception as exc:
        return {
            "sucesso": False,
            "exit_code": 1,
            "erro": str(exc),
            "stdout": "",
            "stderr": str(exc)
        }


def executar_tool(nome_tool: str, args: dict) -> dict:
    """Roteia as tools read-only do Docker MCP."""
    if nome_tool == "docker_compose_config":
        caminho = args.get("compose_path", "")
        if not caminho or not os.path.exists(caminho):
            return {"sucesso": False, "erro": f"Caminho não encontrado: {caminho}"}

        if os.path.isdir(caminho):
            cmd = ["docker", "compose", "config"]
            return _executar_cmd(cmd, cwd=caminho)
        else:
            cmd = ["docker", "compose", "-f", os.path.basename(caminho), "config"]
            return _executar_cmd(cmd, cwd=os.path.dirname(caminho) or ".")

    elif nome_tool == "docker_status_conteineres":
        compose_path = args.get("compose_path")
        if compose_path and os.path.exists(compose_path):
            cwd = compose_path if os.path.isdir(compose_path) else os.path.dirname(compose_path) or "."
            cmd = ["docker", "compose", "ps", "--format", "json"]
            return _executar_cmd(cmd, cwd=cwd)
        else:
            todos = args.get("todos", False)
            cmd = ["docker", "ps", "--format", "json"]
            if todos:
                cmd.append("-a")
            return _executar_cmd(cmd)

    elif nome_tool == "docker_logs":
        alvo = args.get("alvo", "")
        linhas = str(args.get("linhas", 100))
        compose_path = args.get("compose_path")

        if compose_path and os.path.exists(compose_path):
            cwd = compose_path if os.path.isdir(compose_path) else os.path.dirname(compose_path) or "."
            cmd = ["docker", "compose", "logs", "--tail", linhas, alvo]
            return _executar_cmd(cmd, cwd=cwd)
        else:
            cmd = ["docker", "logs", "--tail", linhas, alvo]
            return _executar_cmd(cmd)

    raise ValueError(f"Tool desconhecida: {nome_tool}")


@mcp.tool()
def docker_compose_config(compose_path: str) -> dict:
    """Valida a sintaxe e resolução de variáveis de um arquivo docker-compose.yml sem iniciar nenhum contêiner (read-only)."""
    return executar_tool("docker_compose_config", {"compose_path": compose_path})


@mcp.tool()
def docker_status_conteineres(compose_path: Optional[str] = None, todos: bool = False) -> dict:
    """Lista o status e saúde dos contêineres em execução ou associados a um compose."""
    return executar_tool("docker_status_conteineres", {"compose_path": compose_path or "", "todos": todos})


@mcp.tool()
def docker_logs(alvo: str, linhas: int = 100, compose_path: Optional[str] = None) -> dict:
    """Recupera as últimas linhas de log de um contêiner ou serviço compose."""
    return executar_tool("docker_logs", {"alvo": alvo, "linhas": linhas, "compose_path": compose_path or ""})


if __name__ == "__main__":
    mcp.run(transport="stdio")