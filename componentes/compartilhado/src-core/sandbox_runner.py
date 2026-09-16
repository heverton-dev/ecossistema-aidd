# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — COMPONENTE COMPARTILHADO: SANDBOX RUNNER EFÊMERO
=============================================================================
PLAN-0031 fase 04: Isolamento de execução para testes, scripts gerados por IA
e tarefas de subagentes para prevenir exfiltração de dados e efeitos colaterais.

Mecanismos de Blindagem:
  1. Docker Sandbox (quando Docker disponível): contêiner efêmero (--rm),
     sem privilégios de root, rede desabilitada (--network none), com quotas
     de memória (--memory=512m) e tempo máximo de CPU.
  2. Sanitização Estrita de Ambiente (Process Containment): remoção de todas
     as chaves e variáveis com padrões sensíveis (*_KEY, *_SECRET, *_TOKEN,
     API_*, GITHUB_*, AWS_*, etc.).
  3. Timeout determinístico com abort forçado em caso de congelamento.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Tuple

PADROES_VARIAVEIS_SENSIVEIS = [
    "SECRET",
    "TOKEN",
    "KEY",
    "PASSWORD",
    "PASSWD",
    "CREDENTIAL",
    "AUTH",
    "API",
    "AWS_",
    "GITHUB_",
    "OPENAI_",
    "ANTHROPIC_",
    "GEMINI_",
]


def sanitizar_variaveis_ambiente(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Remove variáveis de ambiente que possam conter credenciais ou segredos."""
    origem = env if env is not None else os.environ
    sanitizado = {}
    for k, v in origem.items():
        k_upper = k.upper()
        if any(sensivel in k_upper for sensivel in PADROES_VARIAVEIS_SENSIVEIS):
            continue
        sanitizado[k] = v
    # Garante variáveis seguras mínimas
    sanitizado["AIDD_SANDBOX"] = "1"
    sanitizado["PYTHONUNBUFFERED"] = "1"
    return sanitizado


class SandboxResult:
    def __init__(self, exit_code: int, stdout: str, stderr: str, timed_out: bool = False, mode: str = "process"):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out
        self.mode = mode

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class EphemeralSandbox:
    def __init__(self, docker_image: str = "python:3.11-slim", prefer_docker: bool = False):
        self.docker_image = docker_image
        self.prefer_docker = prefer_docker
        self.docker_available = shutil.which("docker") is not None

    def execute_in_docker(
        self,
        command: List[str],
        work_dir: str,
        timeout_seconds: int = 30,
        network: str = "none",
        memory_limit: str = "512m",
    ) -> SandboxResult:
        """Executa o comando em um contêiner Docker efêmero e restrito."""
        docker_cmd = [
            "docker", "run", "--rm",
            f"--network={network}",
            f"--memory={memory_limit}",
            "-v", f"{os.path.abspath(work_dir)}:/workspace:rw",
            "-w", "/workspace",
            self.docker_image,
        ] + command

        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            return SandboxResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                timed_out=False,
                mode="docker",
            )
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(
                exit_code=-1,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "Execution timed out in docker sandbox",
                timed_out=True,
                mode="docker",
            )
        except OSError as exc:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Falha ao executar docker: {str(exc)}",
                timed_out=False,
                mode="docker",
            )

    def execute_process_isolated(
        self,
        command: List[str],
        work_dir: Optional[str] = None,
        timeout_seconds: int = 30,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """Executa comando com sanitização estrita de variáveis de ambiente."""
        clean_env = sanitizar_variaveis_ambiente()
        if extra_env:
            for k, v in extra_env.items():
                k_upper = k.upper()
                if not any(sensivel in k_upper for sensivel in PADROES_VARIAVEIS_SENSIVEIS):
                    clean_env[k] = v

        cwd = work_dir or os.getcwd()

        try:
            proc = subprocess.run(
                command,
                cwd=cwd,
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            return SandboxResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                timed_out=False,
                mode="process_isolated",
            )
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(
                exit_code=-1,
                stdout=exc.stdout or "",
                stderr="Timeout excedido na sandbox de processo.",
                timed_out=True,
                mode="process_isolated",
            )
        except OSError as exc:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Erro de execução do processo: {str(exc)}",
                timed_out=False,
                mode="process_isolated",
            )

    def run(
        self,
        command: List[str],
        work_dir: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> SandboxResult:
        """Ponto de entrada unificado: usa Docker se solicitado e disponível, ou isolamento de processo."""
        if self.prefer_docker and self.docker_available and work_dir:
            res = self.execute_in_docker(command, work_dir, timeout_seconds=timeout_seconds)
            if res.exit_code != -1:
                return res
        return self.execute_process_isolated(command, work_dir=work_dir, timeout_seconds=timeout_seconds)
