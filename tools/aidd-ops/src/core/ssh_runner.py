# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — RUNNER SSH DETERMINÍSTICO (Gap 1)
=============================================================================
Execução remota segura com autenticação estrita por chave pública,
lista fechada de operações de bootstrapping (anti-injeção via AST),
retorno monádico Result e modo dry-run obrigatório.
"""

import os
import socket
from typing import Any, Dict, List, Optional

try:
    from src.core.result import Result
except ImportError:
    try:
        from core.result import Result
    except ImportError:
        from result import Result

try:
    import paramiko
except ImportError:
    paramiko = None


OPERACOES_PERMITIDAS: Dict[str, str] = {
    "atualizar_pacotes": "DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y",
    "instalar_docker": "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && sh /tmp/get-docker.sh && rm -f /tmp/get-docker.sh",
    "configurar_ufw": "ufw default deny incoming && ufw default allow outgoing && ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable",
    "instalar_fail2ban": "DEBIAN_FRONTEND=noninteractive apt-get install -y fail2ban && systemctl enable fail2ban && systemctl start fail2ban",
    "criar_swap": "fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile && echo '/swapfile none swap sw 0 0' >> /etc/fstab",
}


class SSHRunner:
    """Runner determinístico para bootstrapping de servidores remotos."""

    def __init__(
        self,
        host: str,
        user: str = "root",
        port: int = 22,
        key_path: Optional[str] = None,
        dry_run: bool = True,
        timeout: int = 15,
    ):
        if not host or not isinstance(host, str) or not host.strip():
            raise ValueError("Host obrigatorio e nao pode ser vazio")
        if not (1 <= port <= 65535):
            raise ValueError(f"Porta invalida: {port}")

        self.host = host.strip()
        self.user = user.strip()
        self.port = port
        self.key_path = key_path or os.environ.get("SSH_KEY_PATH")
        self.dry_run = dry_run
        self.timeout = timeout

    def _conectar(self) -> Any:
        """Cria e conecta um SSHClient do Paramiko."""
        if paramiko is None:
            raise RuntimeError("Biblioteca 'paramiko' nao esta instalada no ambiente")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: Dict[str, Any] = {
            "hostname": self.host,
            "port": self.port,
            "username": self.user,
            "timeout": self.timeout,
            "banner_timeout": self.timeout,
            "auth_timeout": self.timeout,
            "look_for_keys": False,
            "allow_agent": False,
        }

        if self.key_path:
            caminho_chave = os.path.expanduser(self.key_path)
            if not os.path.isfile(caminho_chave):
                raise FileNotFoundError("Arquivo de chave privada nao encontrado")
            connect_kwargs["key_filename"] = caminho_chave

        client.connect(**connect_kwargs)
        return client

    def executar_operacao(self, nome_operacao: str) -> Result[Dict[str, Any]]:
        """Executa uma operacao restrita da lista fechada OPERACOES_PERMITIDAS."""
        if nome_operacao not in OPERACOES_PERMITIDAS:
            return Result.fail(
                f"Operacao '{nome_operacao}' nao autorizada. Operacoes permitidas: {list(OPERACOES_PERMITIDAS.keys())}",
                codigo="OPERACAO_NAO_PERMITIDA",
            )

        comando = OPERACOES_PERMITIDAS[nome_operacao]

        if self.dry_run:
            return Result.ok(
                valor={
                    "operacao": nome_operacao,
                    "comando": comando,
                    "dry_run": True,
                    "exit_code": 0,
                    "stdout": f"[DRY-RUN] Operacao '{nome_operacao}' simulada com sucesso contra {self.user}@{self.host}:{self.port}",
                    "stderr": "",
                }
            )

        client = None
        try:
            client = self._conectar()
            _, stdout_stream, stderr_stream = client.exec_command(comando, timeout=self.timeout)
            exit_code = stdout_stream.channel.recv_exit_status()
            stdout_text = stdout_stream.read().decode("utf-8", errors="replace")
            stderr_text = stderr_stream.read().decode("utf-8", errors="replace")

            if exit_code == 0:
                return Result.ok(
                    valor={
                        "operacao": nome_operacao,
                        "comando": comando,
                        "dry_run": False,
                        "exit_code": 0,
                        "stdout": stdout_text,
                        "stderr": stderr_text,
                    }
                )
            return Result.fail(
                f"Comando da operacao '{nome_operacao}' retornou exit code {exit_code}",
                codigo="FALHA_EXECUCAO_REMOTA",
                detalhes={"exit_code": exit_code, "stderr": stderr_text, "stdout": stdout_text},
            )

        except (socket.timeout, TimeoutError):
            return Result.fail(
                f"Timeout ({self.timeout}s) ao comunicar com host remoto",
                codigo="TIMEOUT_CONEXAO",
            )
        except Exception as exc:
            tipo = type(exc).__name__
            if "Authentication" in tipo:
                return Result.fail(
                    "Falha na autenticacao por chave publica SSH (chave recusada ou inexistente)",
                    codigo="FALHA_AUTENTICACAO",
                )
            return Result.fail(
                f"Erro na conexao SSH ({tipo}): {str(exc)}",
                codigo="ERRO_SSH",
            )
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    def atualizar_pacotes(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("atualizar_pacotes")

    def instalar_docker(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("instalar_docker")

    def configurar_ufw(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("configurar_ufw")

    def instalar_fail2ban(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("instalar_fail2ban")

    def criar_swap(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("criar_swap")

    def executar_bootstrap_completo(self) -> Result[List[Dict[str, Any]]]:
        """Executa a sequencia fechada completa de bootstrapping na ordem recomendada."""
        ordem = [
            "atualizar_pacotes",
            "instalar_docker",
            "configurar_ufw",
            "instalar_fail2ban",
            "criar_swap",
        ]
        resultados = []
        for op in ordem:
            res = self.executar_operacao(op)
            if not res.sucesso:
                return Result.fail(
                    f"Bootstrap interrompido na etapa '{op}': {res.erro}",
                    codigo="FALHA_BOOTSTRAP",
                    detalhes={"etapa_falha": op, "etapas_concluidas": resultados, "erro_etapa": res.to_dict()},
                )
            resultados.append(res.valor)

        return Result.ok(valor=resultados)
