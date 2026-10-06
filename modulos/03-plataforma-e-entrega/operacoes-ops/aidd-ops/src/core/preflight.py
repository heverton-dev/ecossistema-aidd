# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — Pre-Flight E2E Runner (Gap 4 da proposta)
=============================================================================
Bateria de testes pré-produção determinística contra um deploy já realizado:
1. Healthcheck HTTP (/healthz de cada serviço, status 200 obrigatório).
2. Validação de certificado SSL/TLS (emissor, vigência, cadeia).
3. Resolução DNS de subdomínios da topologia (com resolver injetável).
4. Simulação de 1 webhook de ponta a ponta (disparo sintético no gateway).

Suporta dependency injection para execução hermética em testes unitários.
Retorna Result monad com relatório estruturado em JSON.
=============================================================================
"""

import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from core.result import Result
except ImportError:
    from src.core.result import Result


def _default_http_get(url: str, timeout: float) -> Tuple[int, str]:
    """Executa requisição GET simples usando urllib."""
    req = urllib.request.Request(url, headers={"User-Agent": "AIDD-Ops-Preflight/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def _default_http_post(url: str, payload: dict, timeout: float) -> Tuple[int, str]:
    """Executa POST de webhook usando urllib."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AIDD-Ops-Preflight/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def _default_dns_resolver(hostname: str) -> List[str]:
    """Resolve IPs para o hostname usando socket."""
    res = socket.getaddrinfo(hostname, None)
    ips = list({item[4][0] for item in res})
    return ips


def _default_ssl_validator(hostname: str, port: int = 443, timeout: float = 5.0) -> Dict[str, Any]:
    """Conecta via TLS e inspeciona o certificado do servidor."""
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            return {
                "valido": True,
                "emissor": dict(x[0] for x in cert.get("issuer", ())),
                "sujeito": dict(x[0] for x in cert.get("subject", ())),
                "notBefore": cert.get("notBefore"),
                "notAfter": cert.get("notAfter"),
                "versao": ssock.version(),
            }


class PreflightRunner:
    """Executor da bateria de testes pré-voo (Pre-Flight E2E)."""

    def __init__(
        self,
        alvo: str,
        timeout: float = 5.0,
        retries: int = 3,
        retry_interval: float = 0.5,
        http_get_fn: Optional[Callable[[str, float], Tuple[int, str]]] = None,
        http_post_fn: Optional[Callable[[str, dict, float], Tuple[int, str]]] = None,
        dns_resolver_fn: Optional[Callable[[str], List[str]]] = None,
        ssl_validator_fn: Optional[Callable[[str, int, float], Dict[str, Any]]] = None,
    ):
        self.alvo = alvo.strip()
        self.timeout = timeout
        self.retries = retries
        self.retry_interval = retry_interval

        self.http_get = http_get_fn or _default_http_get
        self.http_post = http_post_fn or _default_http_post
        self.dns_resolver = dns_resolver_fn or _default_dns_resolver
        self.ssl_validator = ssl_validator_fn or _default_ssl_validator

    def checar_healthz(self, servicos: List[Dict[str, str]]) -> Dict[str, Any]:
        """Testa o endpoint /healthz para cada serviço configurado."""
        if not servicos:
            return {"nome": "healthz", "status": "nao_aplicavel", "detalhes": "Nenhum serviço com healthz especificado"}

        sucessos = []
        falhas = []

        for s in servicos:
            nome = s.get("nome", "desconhecido")
            url = s.get("url")
            if not url:
                continue

            ok = False
            ultimo_status = 0
            ultimo_erro = ""

            for tentativa in range(self.retries):
                try:
                    status_code, body = self.http_get(url, self.timeout)
                    if status_code == 200:
                        ok = True
                        sucessos.append({"servico": nome, "url": url, "status": 200})
                        break
                    else:
                        ultimo_status = status_code
                        ultimo_erro = f"HTTP {status_code}"
                except OSError as exc:
                    ultimo_erro = str(exc)

                if tentativa < self.retries - 1:
                    time.sleep(self.retry_interval)

            if not ok:
                falhas.append({"servico": nome, "url": url, "status": ultimo_status, "erro": ultimo_erro})

        status_geral = "passou" if not falhas else "falhou"
        return {
            "nome": "healthz",
            "status": status_geral,
            "detalhes": {
                "total_servicos": len(servicos),
                "sucessos": sucessos,
                "falhas": falhas,
            }
        }

    def checar_ssl(self, hostname: str, port: int = 443) -> Dict[str, Any]:
        """Testa e valida certificado TLS do host."""
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0") or not hostname:
            return {"nome": "ssl", "status": "nao_aplicavel", "detalhes": f"Host '{hostname}' opera em HTTP local/desenvolvimento"}

        for tentativa in range(self.retries):
            try:
                info_ssl = self.ssl_validator(hostname, port, self.timeout)
                return {
                    "nome": "ssl",
                    "status": "passou",
                    "detalhes": info_ssl,
                }
            except OSError as exc:
                if tentativa == self.retries - 1:
                    return {
                        "nome": "ssl",
                        "status": "falhou",
                        "detalhes": {"erro": str(exc), "hostname": hostname, "porta": port},
                    }
                time.sleep(self.retry_interval)

        return {"nome": "ssl", "status": "falhou", "detalhes": "Esgotadas tentativas de conexão SSL"}

    def checar_dns(self, hostnames: List[str]) -> Dict[str, Any]:
        """Verifica a resolução de DNS de cada subdomínio/hostname."""
        if not hostnames:
            return {"nome": "dns", "status": "nao_aplicavel", "detalhes": "Nenhum subdomínio para resolver"}

        resolvidos = {}
        falhas = {}

        for host in hostnames:
            for tentativa in range(self.retries):
                try:
                    ips = self.dns_resolver(host)
                    if ips:
                        resolvidos[host] = ips
                        break
                    else:
                        if tentativa == self.retries - 1:
                            falhas[host] = "Nenhum IP retornado"
                except OSError as exc:
                    if tentativa == self.retries - 1:
                        falhas[host] = str(exc)
                if tentativa < self.retries - 1:
                    time.sleep(self.retry_interval)

        status_geral = "passou" if not falhas else "falhou"
        return {
            "nome": "dns",
            "status": status_geral,
            "detalhes": {
                "resolvidos": resolvidos,
                "falhas": falhas,
            }
        }

    def checar_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Dispara um evento sintético contra o gateway para testar conectividade ponta a ponta."""
        if not webhook_url:
            return {"nome": "webhook", "status": "nao_aplicavel", "detalhes": "URL de webhook não configurada"}

        payload = {
            "origem": "aidd-ops-preflight",
            "evento": "ping_sintetico",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for tentativa in range(self.retries):
            try:
                status_code, body = self.http_post(webhook_url, payload, self.timeout)
                # Aceita códigos 2xx como sucesso de entrega
                if 200 <= status_code < 300:
                    return {
                        "nome": "webhook",
                        "status": "passou",
                        "detalhes": {"status_code": status_code, "url": webhook_url},
                    }
            except OSError as exc:
                if tentativa == self.retries - 1:
                    return {
                        "nome": "webhook",
                        "status": "falhou",
                        "detalhes": {"erro": str(exc), "url": webhook_url},
                    }
            if tentativa < self.retries - 1:
                time.sleep(self.retry_interval)

        return {"nome": "webhook", "status": "falhou", "detalhes": f"HTTP {status_code} recebido de {webhook_url}"}

    def executar_bateria(
        self,
        servicos_healthz: Optional[List[Dict[str, str]]] = None,
        subdominios_dns: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        hostname_ssl: Optional[str] = None,
    ) -> Result[Dict[str, Any]]:
        """Executa a bateria de testes completa e consolida o relatório."""
        subdominios = subdominios_dns or ([self.alvo] if self.alvo else [])
        host_ssl = hostname_ssl or (self.alvo if self.alvo else None)

        c_healthz = self.checar_healthz(servicos_healthz or [])
        c_ssl = self.checar_ssl(host_ssl) if host_ssl else {"nome": "ssl", "status": "nao_aplicavel", "detalhes": "Host SSL não definido"}
        c_dns = self.checar_dns(subdominios)
        c_webhook = self.checar_webhook(webhook_url or "")

        checagens = [c_healthz, c_ssl, c_dns, c_webhook]

        total_passou = sum(1 for c in checagens if c["status"] == "passou")
        total_falhou = sum(1 for c in checagens if c["status"] == "falhou")
        total_na = sum(1 for c in checagens if c["status"] == "nao_aplicavel")

        sucesso_geral = total_falhou == 0

        relatorio = {
            "sucesso": sucesso_geral,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alvo": self.alvo,
            "resumo": {
                "total": len(checagens),
                "passou": total_passou,
                "falhou": total_falhou,
                "nao_aplicavel": total_na,
            },
            "checagens": checagens,
        }

        if sucesso_geral:
            return Result.ok(relatorio)
        else:
            return Result.fail(
                codigo="PREFLIGHT_FAILED",
                erro=f"Bateria Pre-Flight reprovou: {total_falhou} checagem(ns) falharam.",
                detalhes=relatorio
            )
