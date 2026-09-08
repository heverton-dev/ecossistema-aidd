# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — RUNNER DE HARDENING VIA ANSIBLE + DEV-SEC.HARDENING (NIH #15)
=============================================================================
Bootstrap e hardening determinístico de VPS delegado a colecao Ansible
testada `devsec.hardening` (roles os_hardening, ssh_hardening) mais tasks
locais idempotentes (docker, firewall, fail2ban, swap) definidas em
ansible/playbooks/hardening.yml — nunca mais em uma string de shell montada
em Python.

Paramiko e mantido exclusivamente como camada de EXECUCAO/transporte:
1. Pre-voo de conectividade e autenticacao por chave publica (testar_conexao),
   antes de delegar a etapa real ao Ansible.
2. Connection plugin `paramiko` do proprio Ansible (ansible_connection=paramiko
   no inventario efemero gerado), no lugar do binario `ssh` do OpenSSH.

Retorno monadico Result, lista fechada de tags autorizadas (anti-tag
arbitraria) e modo dry-run obrigatorio sao preservados do runner anterior.
"""

import os
import shutil
import socket
import subprocess
import tempfile
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


_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOL_ROOT = os.path.dirname(os.path.dirname(_CORE_DIR))
ANSIBLE_DIR = os.path.join(_TOOL_ROOT, "ansible")
PLAYBOOK_PATH = os.path.join(ANSIBLE_DIR, "playbooks", "hardening.yml")


TAGS_PERMITIDAS: Dict[str, str] = {
    "atualizar_pacotes": "Atualizacao de indice e pacotes do SO (modulo ansible.builtin.apt)",
    "docker": "Instalacao do Docker Engine via script oficial get.docker.com (tasks idempotentes)",
    "firewall": "Firewall UFW minimo SSH/HTTP/HTTPS (modulo community.general.ufw)",
    "fail2ban": "Instalacao e ativacao do fail2ban (modulos apt/systemd)",
    "os_hardening": "Hardening geral do SO via colecao devsec.hardening.os_hardening",
    "ssh_hardening": "Hardening do daemon sshd via colecao devsec.hardening.ssh_hardening",
    "swap": "Provisionamento de swapfile de 2G (modulos command/lineinfile)",
}

ORDEM_BOOTSTRAP: List[str] = [
    "atualizar_pacotes",
    "docker",
    "firewall",
    "fail2ban",
    "os_hardening",
    "ssh_hardening",
    "swap",
]


class SSHRunner:
    """Runner determinístico de bootstrap + hardening de VPS via Ansible."""

    def __init__(
        self,
        host: str,
        user: str = "root",
        port: int = 22,
        key_path: Optional[str] = None,
        dry_run: bool = True,
        timeout: int = 15,
        playbook_path: str = PLAYBOOK_PATH,
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
        self.playbook_path = playbook_path

    # ------------------------------------------------------------------
    # Paramiko: camada de execucao/transporte (pre-voo de conectividade)
    # ------------------------------------------------------------------
    def _conectar(self) -> Any:
        """Cria e conecta um SSHClient do Paramiko (usado apenas no pre-voo)."""
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

    def testar_conexao(self) -> Result[Dict[str, Any]]:
        """Pre-voo: valida alcancabilidade e autenticacao por chave publica via
        Paramiko antes de delegar a execucao real do hardening ao Ansible."""
        if self.dry_run:
            return Result.ok({"dry_run": True, "host": self.host, "conectividade": "simulada"})

        client = None
        try:
            client = self._conectar()
            transport = client.get_transport()
            ativo = bool(transport is not None and transport.is_active())
            return Result.ok({
                "dry_run": False,
                "host": self.host,
                "conectividade": "ok" if ativo else "instavel",
            })
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

    # ------------------------------------------------------------------
    # Ansible: fonte unica de verdade da politica de hardening
    # ------------------------------------------------------------------
    def _montar_inventario(self) -> str:
        """Gera um inventario INI efemero com ansible_connection=paramiko, para
        que o proprio Ansible use o Paramiko como transporte de execucao (no
        lugar do binario `ssh` do OpenSSH)."""
        host_vars = [
            self.host,
            "ansible_user=" + self.user,
            "ansible_port=" + str(self.port),
            "ansible_connection=paramiko",
            "ansible_paramiko_look_for_keys=False",
        ]
        if self.key_path:
            host_vars.append("ansible_ssh_private_key_file=" + os.path.expanduser(self.key_path))
        return "[alvo]\n" + " ".join(host_vars) + "\n"

    def _executar_playbook(self, tag: str) -> Result[Dict[str, Any]]:
        """Invoca `ansible-playbook` restrito a uma unica tag da lista fechada.
        Argumentos sempre passados como lista (argv), nunca como string de
        shell montada por concatenacao ou f-string — sem shell=True."""
        binario = shutil.which("ansible-playbook")
        if binario is None:
            return Result.fail(
                "Binario 'ansible-playbook' nao encontrado no PATH do control node",
                codigo="ANSIBLE_NAO_INSTALADO",
            )
        if not os.path.isfile(self.playbook_path):
            return Result.fail(
                "Playbook de hardening nao encontrado: " + self.playbook_path,
                codigo="PLAYBOOK_NAO_ENCONTRADO",
            )

        arquivo_inventario = tempfile.NamedTemporaryFile(
            mode="w", suffix=".ini", delete=False, encoding="utf-8"
        )
        try:
            arquivo_inventario.write(self._montar_inventario())
            arquivo_inventario.close()

            argv: List[str] = [
                binario,
                "-i",
                arquivo_inventario.name,
                self.playbook_path,
                "--tags",
                tag,
            ]
            processo = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=max(self.timeout * 20, 300),
            )
            if processo.returncode == 0:
                return Result.ok({
                    "operacao": tag,
                    "engine": "ansible",
                    "dry_run": False,
                    "exit_code": 0,
                    "stdout": processo.stdout,
                    "stderr": processo.stderr,
                })
            return Result.fail(
                "ansible-playbook retornou exit code "
                + str(processo.returncode)
                + " na tag '"
                + tag
                + "'",
                codigo="FALHA_EXECUCAO_REMOTA",
                detalhes={
                    "exit_code": processo.returncode,
                    "stdout": processo.stdout,
                    "stderr": processo.stderr,
                },
            )
        except subprocess.TimeoutExpired:
            return Result.fail(
                "Timeout ao executar ansible-playbook (tag '" + tag + "')",
                codigo="TIMEOUT_CONEXAO",
            )
        finally:
            try:
                os.unlink(arquivo_inventario.name)
            except OSError:
                pass

    def executar_operacao(self, nome_operacao: str) -> Result[Dict[str, Any]]:
        """Executa uma tag Ansible restrita da lista fechada TAGS_PERMITIDAS."""
        if nome_operacao not in TAGS_PERMITIDAS:
            return Result.fail(
                f"Operacao '{nome_operacao}' nao autorizada. Operacoes permitidas: {list(TAGS_PERMITIDAS.keys())}",
                codigo="OPERACAO_NAO_PERMITIDA",
            )

        descricao = TAGS_PERMITIDAS[nome_operacao]

        if self.dry_run:
            return Result.ok({
                "operacao": nome_operacao,
                "engine": "ansible",
                "descricao": descricao,
                "dry_run": True,
                "exit_code": 0,
                "stdout": f"[DRY-RUN] tag '{nome_operacao}' simulada via ansible-playbook contra {self.user}@{self.host}:{self.port}",
                "stderr": "",
            })

        pre_voo = self.testar_conexao()
        if not pre_voo.sucesso:
            return pre_voo

        return self._executar_playbook(nome_operacao)

    def atualizar_pacotes(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("atualizar_pacotes")

    def instalar_docker(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("docker")

    def configurar_ufw(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("firewall")

    def instalar_fail2ban(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("fail2ban")

    def aplicar_os_hardening(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("os_hardening")

    def aplicar_ssh_hardening(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("ssh_hardening")

    def criar_swap(self) -> Result[Dict[str, Any]]:
        return self.executar_operacao("swap")

    def executar_bootstrap_completo(self) -> Result[List[Dict[str, Any]]]:
        """Executa a sequencia fechada completa de bootstrap+hardening via Ansible."""
        resultados = []
        for op in ORDEM_BOOTSTRAP:
            res = self.executar_operacao(op)
            if not res.sucesso:
                return Result.fail(
                    f"Bootstrap interrompido na etapa '{op}': {res.erro}",
                    codigo="FALHA_BOOTSTRAP",
                    detalhes={"etapa_falha": op, "etapas_concluidas": resultados, "erro_etapa": res.to_dict()},
                )
            resultados.append(res.valor)

        return Result.ok(valor=resultados)
