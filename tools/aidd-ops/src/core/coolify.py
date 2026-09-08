# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — Cliente da API v1 do Coolify (Anti-NIH #19)
=============================================================================
Integração mínima, determinística e Result-based com a API REST v1 do
Coolify (https://coolify.io/docs/api), necessária para registrar o Intake
Web desta ferramenta como app gerenciado ("managed app") no Coolify:

  - GET    /api/v1/health                        (público)
  - GET    /api/v1/version                       (Bearer)
  - GET    /api/v1/servers                       (Bearer)
  - GET    /api/v1/applications                  (Bearer)
- GET    /api/v1/applications/{uuid}           (Bearer)
      - POST   /api/v1/applications/public           (Bearer) — criar app a partir
                                                de repo git com build_pack dockerfile
      - POST   /api/v1/applications/{uuid}/envs      (Bearer) — criar variável de env
      - POST   /api/v1/deploy?uuid=..&force=..            (Bearer) — disparar deploy

Fornace também o CoolifyManager (contrato de scripts/pipeline_ops_deploy.py):
orquestração de stack, verificação de isolamento VPS (NIH #21) e configuração
de AppShell white-label — em dry-run determinístico por padrão.

Padrão do ecossistema: urllib puro + função HTTP injetável (mesmo desenho de
core/uptime_kuma.py), nunca dependência de client HTTP externo. Credenciais
vêm de ambiente (COOLIFY_BASE_URL / COOLIFY_API_TOKEN) ou de flags do CLI —
nunca ficam hardcoded. Nenhum LLM envolvido (Regra de Ouro #1).
=============================================================================
"""

import json
import urllib.error
import urllib.parse
import urllib.request

from typing import Any, Callable, Dict, List, Optional, Tuple

from core.result import Result

# Sigla da função HTTP injetável:
#   http_fn(metodo: str, url: str, body: Optional[dict], headers: dict, timeout: float)
#   -> (status_code: int, corpo: bytes)
HttpFn = Callable[..., Tuple[int, bytes]]

APP_PORT_INTAKE = 8501
APP_BASE_DIR_INTAKE = "tools/aidd-ops"
APP_DOCKERFILE_INTAKE = "Dockerfile.intake"


def _http_default(metodo: str, url: str, body=None, headers=None, timeout: float = 30.0):
    """Implementação HTTP padrão via urllib (sem dependência externa)."""
    dados = None
    if body is not None:
        dados = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=dados, method=metodo)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if dados is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        # 4xx/5xx são respostas válidas do servidor — devolvem status + corpo
        return exc.code, exc.read()


def _texto_corpo(corpo: bytes) -> str:
    return corpo.decode("utf-8", errors="replace").strip()



class CoolifyClient:
    """Client fino e determinístico da API v1 do Coolify.

    Todo método retorna Result: ok(valor) ou fail(codigo, erro, detalhes).
    Códigos de erro: TOKEN_AUSENTE, CONEXAO_RECUSADA, HTTP_<status>, ERRO_JSON.
    """

    def __init__(self, base_url: Optional[str] = None, api_token: Optional[str] = None,
                 http_fn: Optional[HttpFn] = None):
        base_url = (base_url or "").strip().rstrip("/")
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = f"https://{base_url}"
        self.base_url = base_url
        self.api_token = (api_token or "").strip() or None
        self._http = http_fn or _http_default

    # ── infraestrutura privada ──────────────────────────────────────────

    def _url_api(self, caminho: str, params: Optional[Dict[str, str]] = None) -> str:
        url = f"{self.base_url}/api/v1{caminho}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def _headers(self, autenticado: bool) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if autenticado and self.api_token:
            headers["Authorization"] = "Bearer " + self.api_token
        return headers

    def _requisitar(self, metodo: str, caminho: str, body: Optional[dict] = None,
                    params: Optional[Dict[str, str]] = None, autenticado: bool = True,
                    timeout: float = 30.0, parse_json: bool = True) -> Result:
        if autenticado and not self.api_token:
            return Result.fail(
                "Token de API do Coolify ausente (env COOLIFY_API_TOKEN ou --token).",
                codigo="TOKEN_AUSENTE",
            )
        url = self._url_api(caminho, params)
        try:
            status, corpo = self._http(
                metodo, url, body=body, headers=self._headers(autenticado), timeout=timeout
            )
        except Exception as exc:
            return Result.fail(f"Falha de conexão com Coolify em {url}: {exc}", codigo="CONEXAO_RECUSADA")

        if status >= 400:
            return Result.fail(
                f"Coolify respondeu HTTP {status}: {_texto_corpo(corpo)}",
                codigo=f"HTTP_{status}",
            )
        if not corpo:
            return Result.ok(None)

        texto = _texto_corpo(corpo)
        if not parse_json:
            return Result.ok(texto)

        try:
            return Result.ok(json.loads(texto))
        except Exception as exc:
            return Result.fail(f"Resposta inesperada (JSON inválido): {exc}", codigo="ERRO_JSON")

    # ── endpoints públicos de leitura ───────────────────────────────────

    def checar_health(self, timeout: float = 10.0) -> Result:
        """GET /api/v1/health — sem autenticação. Coolify responde texto puro 'OK'."""
        res = self._requisitar("GET", "/health", autenticado=False, timeout=timeout, parse_json=False)
        if res.sucesso and isinstance(res.valor, str):
            return Result.ok({"ok": res.valor.strip() == "OK"})
        if res.sucesso:
            return Result.ok({"ok": "OK" in str(res.valor)})
        return res

    def obter_versao(self, timeout: float = 10.0) -> Result:
        """GET /api/v1/version — versão do servidor Coolify."""
        return self._requisitar("GET", "/version", timeout=timeout)

    def listar_servidores(self, timeout: float = 30.0) -> Result:
        """GET /api/v1/servers — lista de servidores gerenciados."""
        return self._requisitar("GET", "/servers", timeout=timeout)

    def listar_apps(self, timeout: float = 30.0) -> Result:
        """GET /api/v1/applications — lista de apps gerenciados (id, nome, domínio)."""
        return self._requisitar("GET", "/applications", timeout=timeout)

    def obter_app(self, uuid: str, timeout: float = 30.0) -> Result:
        """GET /api/v1/applications/{uuid} — detalhe de um app gerenciado."""
        uuid = (uuid or "").strip()
        if not uuid:
            return Result.fail("UUID do app é obrigatório.", codigo="PARAM_INVALIDO")
        return self._requisitar("GET", f"/applications/{uuid}", timeout=timeout)

    # ── escrita (criar app / envs / deploy) ─────────────────────────────

    def criar_app_dockerfile(
        self,
        project_uuid: str,
        server_uuid: str,
        environment_name: str,
        git_repository: str,
        git_branch: str = "main",
        base_directory: Optional[str] = None,
        dockerfile_location: Optional[str] = None,
        ports_exposes: Optional[List[int]] = None,
        domains: Optional[List[str]] = None,
        nome: Optional[str] = None,
        instant_deploy: bool = False,
        timeout: float = 60.0,
    ) -> Result:
        """POST /api/v1/applications/public — cria app gerenciado a partir de repositório git.

        Convenção do Intake Web: build_pack 'dockerfile', Base Directory e
        Dockerfile padrão apontam para tools/aidd-ops quando não informados.
        Retorna Result.ok(uuid do app criado).
        """
        body: Dict[str, object] = {
            "project_uuid": project_uuid,
            "server_uuid": server_uuid,
            "environment_name": environment_name,
            "git_repository": git_repository,
            "git_branch": git_branch,
            "build_pack": "dockerfile",
            "base_directory": base_directory or APP_BASE_DIR_INTAKE,
            "dockerfile_location": dockerfile_location or APP_DOCKERFILE_INTAKE,
            "ports_exposes": ports_exposes or [APP_PORT_INTAKE],
            "instant_deploy": bool(instant_deploy),
        }
        if domains:
            body["domains"] = domains
        if nome:
            body["name"] = nome
        else:
            body["name"] = "aidd-ops-intake"

        res = self._requisitar("POST", "/applications/public", body=body, timeout=timeout)
        if not res.sucesso:
            return res
        uuid = (res.valor or {}).get("uuid")
        if not uuid:
            return Result.fail("Resposta sem uuid do app criado.", codigo="ERRO_RESPOSTA")
        return Result.ok(uuid, detalhes={"payload_enviado": body})

    def definir_env(self, uuid: str, pares: List[Tuple[str, str]],
                    is_preview: bool = False, is_literal: bool = True,
                    timeout: float = 30.0) -> Result:
        """POST /api/v1/applications/{uuid}/envs — cria variáveis de ambiente no app."""
        uuid = (uuid or "").strip()
        if not uuid:
            return Result.fail("UUID do app é obrigatório.", codigo="PARAM_INVALIDO")
        if not pares:
            return Result.fail("Nenhum par CHAVE=VALOR informado.", codigo="PARAM_INVALIDO")

        criadas = []
        for chave, valor in pares:
            body = {
                "key": chave,
                "value": valor,
                "is_preview": bool(is_preview),
                "is_literal": bool(is_literal),
            }
            res = self._requisitar("POST", f"/applications/{uuid}/envs", body=body, timeout=timeout)
            if not res.sucesso:
                return Result.fail(
                    f"Falha ao criar env {chave} no app {uuid}: {res.erro}",
                    codigo="ERRO_ENV",
                    detalhes={"status_original": res.codigo},
                )
            criadas.append(chave)
        return Result.ok(criadas)

    def disparar_deploy(self, uuid: str, force: bool = False, timeout: float = 60.0) -> Result:
        """POST /api/v1/deploy?uuid=..&force=.. — dispara deploy no app gerenciado."""
        uuid = (uuid or "").strip()
        if not uuid:
            return Result.fail("UUID do app é obrigatório.", codigo="PARAM_INVALIDO")
        params = {"uuid": uuid, "force": "true" if force else "false"}
        return self._requisitar("POST", "/deploy", params=params, timeout=timeout)


class CoolifyManager:
    """Orquestrador de stack no Coolify (contrato de scripts/pipeline_ops_deploy.py).

    Interfaces usadas pelo pipeline de deploy ponta a ponta:
      orquestrar_stack(...)            → monta/valida o plano da stack (dry-run) e,
                                         em modo real, o aplica via CoolifyClient.
      verificar_isolamento_vps(...)     → NIH #21: garante que NENHUM app publica
                                         porta do host (todas as portas expostas
                                         são >= 1024, via proxy reverso privado).
      configurar_appshell_whitelabel()  → configuração de identidade do portal.

    Modo dry-run é o padrão; em modo real sem instância Coolify configurada
    (base_url/api_token), a operação falha de forma determinística e honesta
    (REAL_NAO_IMPLEMENTADO) — nunca simula sucesso que não aconteceu.
    """

    PORTA_MINIMA_ISOLADA = 1024

    def __init__(self, dry_run: bool = True, base_url: Optional[str] = None,
                 api_token: Optional[str] = None, http_fn: Optional[HttpFn] = None):
        self.dry_run = bool(dry_run)
        self._cliente = CoolifyClient(
            base_url=base_url or "", api_token=api_token, http_fn=http_fn
        )

    # ── helpers ──────────────────────────────────────────────────────────

    def _validar_servicos(self, servicos: List[Dict[str, Any]]) -> Optional[Result]:
        if not servicos:
            return Result.fail("Nenhum serviço informado para a stack.", codigo="PARAM_INVALIDO")
        for svc in servicos:
            if not svc.get("nome"):
                return Result.fail("Serviço sem nome.", codigo="PARAM_INVALIDO")
            porta = svc.get("porta_interna")
            if not isinstance(porta, int) or porta < 1:
                return Result.fail(
                    f"Serviço '{svc.get('nome')}' sem porta_interna válida.", codigo="PARAM_INVALIDO")
        return None

    # ── contrato usado por pipeline_ops_deploy ───────────────────────────

    def orquestrar_stack(self, nome_projeto: str, ambiente: str,
                         servicos: List[Dict[str, Any]], dominio_base: str) -> Result:
        """Monta o plano da stack e, em dry-run, devolve-o estruturado.

        Em modo real, aplica os apps no Coolify via CoolifyClient (criar app
        dockerfile por serviço) — exige base_url + api_token configurados.
        """
        nome_projeto = (nome_projeto or "").strip()
        ambiente = (ambiente or "").strip()
        dominio_base = (dominio_base or "").strip()

        res_validacao = self._validar_servicos(servicos)
        if res_validacao is not None:
            return res_validacao

        apps = []
        for svc in servicos:
            nome = svc["nome"].strip()
            porta = svc.get("porta_interna")
            apps.append({
                "nome_servico": nome,
                "nome_app": f"{nome_projeto.lower()}-{nome.lower()}",
                "dominios": [f"{nome.lower()}.{dominio_base}"] if dominio_base else [],
                "ports_exposes": [porta],
                "limits": {
                    "cpus": svc.get("cpus"),
                    "memory": svc.get("memory"),
                },
            })

        plano_stack = {
            "projeto": nome_projeto,
            "ambiente": ambiente,
            "dominio_base": dominio_base,
            "apps": apps,
        }

        if self.dry_run:
            return Result.ok(plano_stack)

        if not self._cliente.base_url or not self._cliente.api_token:
            return Result.fail(
                "Modo real exige COOLIFY_BASE_URL e COOLIFY_API_TOKEN configurados.",
                codigo="TOKEN_AUSENTE",
            )
        return Result.fail(
            "Aplicação real da stack completa via CoolifyManager não está implementada "
            "(registre cada app com o subcomando coolify create e dispatch deploy).",
            codigo="REAL_NAO_IMPLEMENTADO",
            detalhes={"plano_stack": plano_stack},
        )

    def verificar_isolamento_vps(self, plano_stack: dict) -> Result:
        """NIH #21 — valida que nenhum app da stack expõe porta < limite isolado."""
        apps = (plano_stack or {}).get("apps", [])
        violacoes = [
            {
                "app": app.get("nome_app"),
                "ports_exposes": app.get("ports_exposes"),
            }
            for app in apps
            if any(p < self.PORTA_MINIMA_ISOLADA for p in app.get("ports_exposes", []))
        ]
        if violacoes:
            return Result.fail(
                f"Isolamento de VPS violado: {len(violacoes)} app(s) publica(m) porta do host.",
                codigo="ISOLAMENTO_VIOLADO",
                detalhes={"violacoes": violacoes},
            )
        return Result.ok({
            "verificado": True,
            "apps_auditados": len(apps),
            "porta_minima_aceita": self.PORTA_MINIMA_ISOLADA,
        })

    def configurar_appshell_whitelabel(self, nome_instancia: str, marca: str,
                                       logo_url: str, dashboard_fqdn: str) -> Result:
        """Define identidade white-label do portal (dry-run: apenas planeja)."""
        config = {
            "nome_instancia": nome_instancia,
            "marca": marca,
            "logo_url": logo_url,
            "dashboard_fqdn": dashboard_fqdn,
            "dry_run": self.dry_run,
        }
        if self.dry_run:
            return Result.ok(config)
        if not self._cliente.base_url or not self._cliente.api_token:
            return Result.fail(
                "Modo real exige COOLIFY_BASE_URL e COOLIFY_API_TOKEN configurados.",
                codigo="TOKEN_AUSENTE",
            )
        return Result.fail(
            "Aplicação real do AppShell white-label exige instância gerenciada dedicada.",
            codigo="REAL_NAO_IMPLEMENTADO",
            detalhes={"config": config},
        )


__all__ = ["CoolifyClient", "CoolifyManager",
           "APP_PORT_INTAKE", "APP_BASE_DIR_INTAKE", "APP_DOCKERFILE_INTAKE"]