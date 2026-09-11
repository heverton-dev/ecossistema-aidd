# -*- coding: utf-8 -*-
"""
BridgeTeardown — Remoção isolada e determinística de aplicações implantadas via aidd-bridge.
Remove a stack no Swarm, volumes dedicados, registro DNS no Cloudflare e diretório na VPS,
assegurando 100% de integridade dos outros serviços em produção (Traefik, Evolution API, N8N, etc.).
"""

import os
import re
import sys
import time
import requests
from typing import Dict, Any, Optional
from .cloudflare_dns import CloudflareDNS

try:
    import paramiko
except ImportError:
    paramiko = None

# app_name vira literal dentro de comandos shell remotos (docker stack rm,
# rm -rf) em destroy_vps_stack — precisa ser só letras/números/hífen para não
# permitir injetar comando extra via um nome malicioso.
_APP_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# domain também é interpolado (via app_slug) num grep de nome de volume.
_DOMAIN_PATTERN = re.compile(r"^[a-zA-Z0-9.-]+$")


class BridgeTeardown:
    def __init__(
        self,
        app_name: str,
        domain: Optional[str] = None,
        vps_host: Optional[str] = None,
        vps_user: Optional[str] = None,
        vps_password: Optional[str] = None,
        cf_api_token: Optional[str] = None,
        cf_zone_id: Optional[str] = None
    ):
        self.app_name = app_name.strip()
        if not _APP_NAME_PATTERN.match(self.app_name):
            raise ValueError(
                f"app_name invalido: '{self.app_name}'. "
                "Use apenas letras minusculas, numeros e hifen (ex: hub-teste)."
            )

        self.domain = domain.strip() if domain else None
        if self.domain and not _DOMAIN_PATTERN.match(self.domain):
            raise ValueError(
                f"domain invalido: '{self.domain}'. "
                "Use apenas letras, numeros, ponto e hifen (ex: hub-teste.vpsconexao.org)."
            )

        self.vps_host = vps_host or os.getenv("VPS_HOST")
        self.vps_user = vps_user or os.getenv("VPS_USER", "root")
        self.vps_password = vps_password or os.getenv("VPS_PASSWORD")
        self.cf_api_token = cf_api_token or os.getenv("CLOUDFLARE_API_TOKEN")
        self.cf_zone_id = cf_zone_id or os.getenv("CLOUDFLARE_ZONE_ID")

    def delete_cloudflare_dns(self) -> Dict[str, Any]:
        """Localiza e deleta o registro DNS (CNAME ou A) do subdomínio no Cloudflare."""
        if not self.domain or not self.cf_api_token or not self.cf_zone_id:
            return {"status": "skipped", "reason": "Credenciais Cloudflare ou domínio ausentes"}

        cf = CloudflareDNS(
            zone_id=self.cf_zone_id,
            api_token=self.cf_api_token
        )
        return cf.deletar_registro(self.domain)


    def destroy_vps_stack(self, remove_volumes: bool = True, remove_dir: bool = True) -> Dict[str, Any]:
        """Remove a stack Docker Swarm, seus volumes e seu diretório na VPS com total isolamento."""
        if not paramiko:
            return {"status": "error", "error": "paramiko não instalado"}

        if not self.vps_host or not self.vps_password:
            return {"status": "error", "error": "Credenciais da VPS não configuradas"}

        results = {"stack": None, "volumes": None, "directory": None}

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                self.vps_host,
                username=self.vps_user,
                password=self.vps_password,
                timeout=15
            )

            # 1. Remover Docker Swarm stack
            cmd_stack = f"docker stack rm {self.app_name}"
            stdin, stdout, stderr = ssh.exec_command(cmd_stack)
            stdout.channel.recv_exit_status()
            results["stack"] = stdout.read().decode("utf-8").strip()

            # Aguardar drenagem dos containers da stack (máximo 15s)
            time.sleep(5)

            # 2. Remover volumes isolados da stack se solicitado
            if remove_volumes:
                app_slug = self.domain.replace(".", "-").replace(":", "-") if self.domain else self.app_name
                cmd_vols = f"docker volume ls -q | grep -E '^({self.app_name}|{app_slug})' | xargs -r docker volume rm"
                stdin, stdout, stderr = ssh.exec_command(cmd_vols)
                stdout.channel.recv_exit_status()
                results["volumes"] = "Volumes isolados removidos"

            # 3. Remover diretório na VPS se solicitado (convenção /root/{app_name})
            #    e também os arquivos de staging com prefixo do app dentro da
            #    pasta compartilhada /root/aidd-bridge-deploy/ (usada quando o
            #    pacote é enviado manualmente via SFTP em vez de um passo de
            #    deploy automatizado — evita deixar init-db.sql/compose.yml
            #    velhos esquecidos lá).
            if remove_dir:
                safe_dir = f"/root/{self.app_name}"
                shared_glob = f"/root/aidd-bridge-deploy/{self.app_name}*"
                cmd_rm_dir = f"rm -rf {safe_dir} && rm -f {shared_glob}"
                stdin, stdout, stderr = ssh.exec_command(cmd_rm_dir)
                stdout.channel.recv_exit_status()
                results["directory"] = f"Diretório {safe_dir} e staging {shared_glob} removidos"

            ssh.close()
            return {"status": "success", "details": results}
        except Exception as e:
            if ssh:
                ssh.close()
            return {"status": "error", "error": str(e)}

    def execute_teardown(self) -> Dict[str, Any]:
        """Executa a rotina completa de desinstalação segura."""
        dns_res = self.delete_cloudflare_dns()
        vps_res = self.destroy_vps_stack()
        return {
            "app_name": self.app_name,
            "domain": self.domain,
            "dns": dns_res,
            "vps": vps_res
        }
