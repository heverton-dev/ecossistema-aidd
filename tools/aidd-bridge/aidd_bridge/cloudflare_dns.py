# -*- coding: utf-8 -*-
"""
CloudflareDNS — Gerenciamento determinístico de registros DNS no Cloudflare.

Estratégia de tipos:
- CNAME → para subdomínios novos (apontam para o domínio raiz já mapeado à VPS)
- A     → NUNCA criado pelo bridge (o registro A raiz já existe no Cloudflare)

Exemplo:
  Existente: vpsconexao.org A → 167.86.69.79
  Criado:    hub-teste.vpsconexao.org CNAME → vpsconexao.org (proxied=True)
"""

import os
import requests
from typing import Dict, Any, Optional


class CloudflareDNS:
    CF_API = "https://api.cloudflare.com/client/v4"

    def __init__(
        self,
        zone_id: Optional[str] = None,
        api_token: Optional[str] = None,
        root_domain: Optional[str] = None
    ):
        self.zone_id = zone_id or os.getenv("CLOUDFLARE_ZONE_ID")
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN")
        # Domínio raiz para o qual o CNAME vai apontar (ex: "vpsconexao.org")
        # Se não informado, extrai do CF_ROOT_DOMAIN ou deduz do subdomínio
        self.root_domain = root_domain or os.getenv("CF_ROOT_DOMAIN", "")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def _records_url(self) -> str:
        return f"{self.CF_API}/zones/{self.zone_id}/dns_records"

    def _deduce_root(self, subdomain: str) -> str:
        """
        Se root_domain não foi configurado, deduz a partir do subdomínio.
        Ex: 'hub-teste.vpsconexao.org' → 'vpsconexao.org'
        """
        if self.root_domain:
            return self.root_domain
        parts = subdomain.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return subdomain

    def criar_cname(self, subdomain: str, proxied: bool = True) -> Dict[str, Any]:
        """
        Cria um registro CNAME para o subdomínio apontando para o domínio raiz.
        Se já existir, retorna o registro existente sem duplicar.

        Args:
            subdomain: ex: 'hub-teste.vpsconexao.org'
            proxied: True = proxy Cloudflare ativo (laranja), False = DNS only

        Returns:
            dict com status, id e name do registro
        """
        if not self.zone_id or not self.api_token:
            return {"status": "error", "error": "CF_ZONE_ID ou CF_API_TOKEN não configurados"}

        root = self._deduce_root(subdomain)
        headers = self._headers()

        # Verificar se já existe registro com esse nome
        existing = self._buscar_registro(subdomain)
        if existing:
            return {
                "status": "already_exists",
                "type": existing.get("type"),
                "id": existing.get("id"),
                "name": existing.get("name"),
                "content": existing.get("content")
            }

        payload = {
            "type": "CNAME",
            "name": subdomain,
            "content": root,
            "proxied": proxied,
            "ttl": 1  # ttl=1 = Auto quando proxied=True
        }

        try:
            resp = requests.post(self._records_url(), headers=headers, json=payload, timeout=10)
            data = resp.json()
            if data.get("success"):
                rec = data["result"]
                return {
                    "status": "created",
                    "type": rec["type"],
                    "id": rec["id"],
                    "name": rec["name"],
                    "content": rec["content"],
                    "proxied": rec["proxied"]
                }
            return {"status": "error", "error": data.get("errors")}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _buscar_registro(self, name: str) -> Optional[Dict[str, Any]]:
        """Busca qualquer registro DNS com o nome exato (A ou CNAME)."""
        try:
            resp = requests.get(
                self._records_url(),
                headers=self._headers(),
                params={"name": name},
                timeout=10
            )
            data = resp.json()
            if data.get("success") and data.get("result"):
                return data["result"][0]
        except Exception:
            pass
        return None

    def deletar_registro(self, subdomain: str) -> Dict[str, Any]:
        """
        Deleta qualquer registro DNS (CNAME ou A) com o nome exato do subdomínio.
        Seguro: só deleta registros cujo nome = subdomain exato.
        """
        if not self.zone_id or not self.api_token:
            return {"status": "error", "error": "CF_ZONE_ID ou CF_API_TOKEN não configurados"}

        headers = self._headers()
        url = self._records_url()

        try:
            resp = requests.get(url, headers=headers, params={"name": subdomain}, timeout=10)
            data = resp.json()
            if not data.get("success"):
                return {"status": "error", "error": data.get("errors")}

            records = data.get("result", [])
            if not records:
                return {"status": "not_found", "message": f"Nenhum registro encontrado para '{subdomain}'"}

            deleted = []
            for rec in records:
                del_resp = requests.delete(f"{url}/{rec['id']}", headers=headers, timeout=10)
                if del_resp.json().get("success"):
                    deleted.append({"id": rec["id"], "type": rec["type"], "name": rec["name"]})

            return {"status": "success", "deleted": deleted}
        except Exception as e:
            return {"status": "error", "error": str(e)}
