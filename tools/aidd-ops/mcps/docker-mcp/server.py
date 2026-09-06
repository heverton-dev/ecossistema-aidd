#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP: Docker MCP (Inspeção e Validação Read-Only)

Servidor MCP mínimo (JSON-RPC 2.0 sobre stdio, biblioteca padrão apenas subprocess/shutil).
Expõe tools exclusivamente de validação e leitura:
- docker compose config (validação sintática de compose sem subir nada)
- docker ps (status de contêineres)
- docker logs (inspeção de logs de serviços)

NOTA DE ESCOPO: Operações destrutivas (down, rm, stop) NÃO são implementadas neste
pacote, seguindo estritamente a Definição de Pronto do Pacote 5.
"""

import json
import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List

NOME_SERVIDOR = "docker-mcp"
DESCRICAO_SERVIDOR = "Servidor MCP para inspeção e validação determinística de contêineres e templates Docker Compose (Read-Only)."

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "docker_compose_config",
        "description": "Valida a sintaxe e resolução de variáveis de um arquivo docker-compose.yml sem iniciar nenhum contêiner (read-only).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "compose_path": {"type": "string", "description": "Caminho do arquivo docker-compose.yml ou diretório contendo-o"}
            },
            "required": ["compose_path"]
        }
    },
    {
        "name": "docker_status_conteineres",
        "description": "Lista o status e saúde dos contêineres em execução ou associados a um compose.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "compose_path": {"type": "string", "description": "Caminho opcional do docker-compose para filtrar apenas os serviços dele"},
                "todos": {"type": "boolean", "description": "Se verdadeiro, lista inclusive contêineres parados (default: false)", "default": False}
            }
        }
    },
    {
        "name": "docker_logs",
        "description": "Recupera as últimas linhas de log de um contêiner ou serviço compose.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "alvo": {"type": "string", "description": "Nome do contêiner ou serviço compose"},
                "linhas": {"type": "integer", "description": "Número de linhas recentes a recuperar (default: 100)", "default": 100},
                "compose_path": {"type": "string", "description": "Caminho opcional do compose caso alvo seja um serviço"}
            },
            "required": ["alvo"]
        }
    }
]


def _executar_cmd(cmd_list: list, cwd: str = None) -> dict:
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


def processar_requisicao(req: dict) -> dict:
    metodo = req.get("method")
    req_id = req.get("id")

    if metodo == "initialize":
        resultado = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": NOME_SERVIDOR, "version": "1.0"},
            "capabilities": {"tools": {}},
        }
    elif metodo == "tools/list":
        resultado = {"tools": TOOLS}
    elif metodo == "tools/call":
        params = req.get("params", {})
        resultado = executar_tool(params.get("name"), params.get("arguments", {}))
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Método não suportado: {metodo}"},
        }

    return {"jsonrpc": "2.0", "id": req_id, "result": resultado}


def main():
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            req = json.loads(linha)
            resp = processar_requisicao(req)
        except Exception as exc:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
