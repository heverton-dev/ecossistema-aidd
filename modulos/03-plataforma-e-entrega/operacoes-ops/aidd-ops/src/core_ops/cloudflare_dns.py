# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — DNS DA BORDA NA CLOUDFLARE (registro A do subdomínio do app)
=============================================================================
`garantir_registro_a` é idempotente: lê o registro A do nome; cria se não existe, atualiza se o IP mudou e não
faz nada se já está certo. O token nunca aparece em resultado, log ou erro. A chamada HTTP é injetável
(`http(metodo, url, corpo, headers) -> (status, json)`); a API real da Cloudflare NÃO foi exercitada nesta etapa
(criar DNS no domínio do usuário é uma ação externa, só feita com `--real` e a decisão do usuário).
=============================================================================
"""

import ipaddress
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple

try:
    from src.core_ops.result import Result
except ImportError:
    from core_ops.result import Result

API = "https://api.cloudflare.com/client/v4"
_RE_NOME = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.IGNORECASE)
HttpFn = Callable[..., Tuple[int, Dict[str, Any]]]


def _http_padrao(metodo: str, url: str, corpo: Optional[dict] = None, headers: Optional[dict] = None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read().decode("utf-8") or "{}")
        except ValueError:
            return erro.code, {}
    except (urllib.error.URLError, OSError, ValueError):
        return 0, {}


def garantir_registro_a(token: str, zone_id: str, nome: str, ip: str, http: Optional[HttpFn] = None,
                        dry_run: bool = False) -> Result:
    if not _RE_NOME.match(nome or "") or not _ip_valido(ip):
        return Result.fail("Nome de host ou IP inválido para o registro A.", codigo="DNS_ENTRADA_INVALIDA",
                           detalhes={"nome": nome, "ip": ip})
    if dry_run:
        return Result.ok({"dry_run": True, "acao": "criaria_ou_atualizaria", "registro": {"type": "A", "name": nome, "content": ip}})

    http = http or _http_padrao
    cabecalhos = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base = f"{API}/zones/{zone_id}/dns_records"
    status, resposta = http("GET", f"{base}?{urllib.parse.urlencode({'type': 'A', 'name': nome})}", None, cabecalhos)
    if status != 200 or not resposta.get("success", False):
        return _falha("consultar", status, resposta)

    existentes = resposta.get("result") or []
    corpo = {"type": "A", "name": nome, "content": ip, "ttl": 1, "proxied": False}
    if not existentes:
        status, resposta = http("POST", base, corpo, cabecalhos)
        acao = "criado"
    elif existentes[0].get("content") != ip:
        status, resposta = http("PUT", f"{base}/{existentes[0].get('id')}", corpo, cabecalhos)
        acao = "atualizado"
    else:
        return Result.ok({"dry_run": False, "acao": "inalterado", "registro": {"type": "A", "name": nome, "content": ip}})
    if status != 200 or not resposta.get("success", False):
        return _falha("gravar", status, resposta)
    return Result.ok({"dry_run": False, "acao": acao, "registro": {"type": "A", "name": nome, "content": ip}})


def _ip_valido(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def _falha(passo: str, status: int, resposta: Dict[str, Any]) -> Result:
    mensagens = [str(e.get("message", "")) for e in (resposta.get("errors") or []) if isinstance(e, dict)]
    return Result.fail(f"A API da Cloudflare recusou ao {passo} o registro (HTTP {status}).", codigo="DNS_API_FALHOU",
                       detalhes={"http": status, "mensagens": mensagens})
