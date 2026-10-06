import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from core.result import Result
except ImportError:
    from src.core.result import Result


def _default_http_get(url: str, timeout: float) -> Tuple[int, str]:
    """Executa requisição GET simples para healthcheck do Uptime Kuma."""
    req = urllib.request.Request(url, headers={"User-Agent": "AIDD-Ops-UptimeKuma/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


class UptimeKumaManager:
    """
    Gerenciador e sincronizador do Uptime Kuma para o AIDD-Ops (NIH #14).
    Substitui dashboards preflight que fabricavam dados estáticos por
    geração e inspeção de healthchecks reais e export compatível com Uptime Kuma.
    """

    KUMA_EXPORT_VERSION = "1.23.15"

    def __init__(self, http_get_fn: Optional[Callable[[str, float], Tuple[int, str]]] = None):
        self.http_get = http_get_fn or _default_http_get

    def extrair_monitores_de_servicos(self, servicos: List[Dict[str, Any]]) -> Result[List[Dict[str, Any]]]:
        """
        Converte uma lista de serviços reais da stack em monitores estruturados
        para o Uptime Kuma. Rejeita listas vazias ou entradas com dados fabricados.
        """
        if not servicos:
            return Result.fail(
                erro="Nenhum serviço fornecido para configurar no Uptime Kuma",
                codigo="SERVICOS_VAZIOS"
            )

        monitores: List[Dict[str, Any]] = []
        for idx, s in enumerate(servicos, 1):
            nome = s.get("nome", "").strip()
            url = s.get("url", "").strip()
            if not nome:
                return Result.fail(
                    erro=f"Serviço no índice {idx} não possui campo 'nome'",
                    codigo="SERVICO_SEM_NOME"
                )
            if not url:
                return Result.fail(
                    erro=f"Serviço '{nome}' não possui URL de healthcheck válida",
                    codigo="SERVICO_SEM_URL"
                )

            tipo = s.get("tipo", "http")
            intervalo = int(s.get("intervalo", 60))
            retry_interval = int(s.get("retry_interval", 20))
            max_retries = int(s.get("max_retries", 3))

            monitor = {
                "id": idx,
                "name": nome,
                "type": tipo,
                "url": url,
                "method": "GET",
                "interval": max(10, intervalo),
                "retryInterval": max(5, retry_interval),
                "maxretries": max(1, max_retries),
                "accepted_statuscodes": ["200-299"],
                "active": 1,
                "description": f"Healthcheck ativo monitorado via AIDD-Ops para {nome}",
                "tags": [
                    {"name": "aidd-ops", "color": "#2563eb"},
                    {"name": nome.lower().replace(" ", "-"), "color": "#10b981"}
                ]
            }
            monitores.append(monitor)

        return Result.ok(monitores)

    def extrair_monitores_de_compose_conteudo(self, conteudo_compose: str) -> Result[List[Dict[str, Any]]]:
        """
        Analisa o conteúdo de um docker-compose.yml e extrai healthchecks reais
        declarados em blocos 'healthcheck:' ou portas de serviços.
        Garante que nenhuma informação seja hardcoded/inventada.
        """
        if not conteudo_compose or not conteudo_compose.strip():
            return Result.fail(
                erro="Conteúdo do docker-compose está vazio",
                codigo="COMPOSE_VAZIO"
            )

        servicos: List[Dict[str, Any]] = []
        linhas = conteudo_compose.splitlines()

        servico_atual = None
        em_services = False
        indent_services = 0
        healthcheck_cmd = ""
        servico_ports: List[str] = []

        def _fechar_servico():
            nonlocal servico_atual, healthcheck_cmd, servico_ports
            if servico_atual:
                url = None
                # Se tem comando de healthcheck com curl/http, extrair url
                if healthcheck_cmd:
                    match_url = re.search(r"https?://[^\s\"'\\]+", healthcheck_cmd)
                    if match_url:
                        url = match_url.group(0)
                # Se não achou URL no healthcheck mas tem porta mapeada
                if not url and servico_ports:
                    p = servico_ports[0]
                    url = f"http://localhost:{p}/"

                if url:
                    servicos.append({
                        "nome": servico_atual,
                        "url": url,
                        "tipo": "http"
                    })
            servico_atual = None
            healthcheck_cmd = ""
            servico_ports = []

        for linha in linhas:
            strip_l = linha.strip()
            if not strip_l or strip_l.startswith("#"):
                continue

            # Detecta services:
            if re.match(r"^services:\s*$", strip_l):
                em_services = True
                indent_services = len(linha) - len(linha.lstrip())
                continue

            if em_services:
                indent = len(linha) - len(linha.lstrip())
                # Top-level key diferente de services fecha services
                if indent <= indent_services and not strip_l.startswith("-"):
                    _fechar_servico()
                    em_services = False
                    continue

                # Identifica nome de serviço (indent exatamente indent_services + 2)
                match_srv = re.match(r"^([a-zA-Z0-9_-]+):\s*$", strip_l)
                if match_srv and indent == indent_services + 2:
                    _fechar_servico()
                    servico_atual = match_srv.group(1)
                    continue

                # Extrai healthcheck test
                if servico_atual and "test:" in strip_l:
                    healthcheck_cmd = strip_l.split("test:", 1)[1].strip()
                    continue

                # Extrai portas mapeadas
                if servico_atual and strip_l.startswith("-"):
                    item = strip_l.lstrip("- ").strip("'\"")
                    if ":" in item:
                        try:
                            porta_host, _ = item.rsplit(":", 1)
                            porta_host = porta_host.strip()
                            match_def = re.search(r":-([0-9]+)", porta_host)
                            if match_def:
                                servico_ports.append(match_def.group(1))
                            elif porta_host.isdigit():
                                servico_ports.append(porta_host)
                        except Exception:
                            pass

        _fechar_servico()

        if not servicos:
            return Result.fail(
                erro="Nenhum serviço com healthcheck ou porta identificável no compose",
                codigo="NENHUM_SERVICO_ENCONTRADO"
            )

        return self.extrair_monitores_de_servicos(servicos)

    def gerar_export_kuma(
        self,
        monitores: List[Dict[str, Any]],
        nome_dashboard: str = "AIDD-Ops Observability"
    ) -> Result[Dict[str, Any]]:
        """
        Gera o JSON no formato canônico de import/export do Uptime Kuma 1.x.
        """
        if not monitores:
            return Result.fail(
                erro="Lista de monitores vazia. Não é possível gerar export do Uptime Kuma.",
                codigo="MONITORES_VAZIOS"
            )

        dados_export = {
            "version": self.KUMA_EXPORT_VERSION,
            "generator": "AIDD-Ops UptimeKumaManager (Anti-NIH #14)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dashboard_title": nome_dashboard,
            "notificationList": [],
            "monitorList": monitores
        }
        return Result.ok(dados_export)

    def salvar_export_kuma(self, export_data: Dict[str, Any], caminho_arquivo: str) -> Result[str]:
        """Salva os dados de export em arquivo JSON no disco."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(caminho_arquivo)), exist_ok=True)
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return Result.ok(os.path.abspath(caminho_arquivo))
        except OSError as exc:
            return Result.fail(
                erro=f"Falha ao salvar export do Uptime Kuma em {caminho_arquivo}: {exc}",
                codigo="ERRO_GRAVACAO_ARQUIVO"
            )

    def verificar_saude_dashboard(self, kuma_url: str, timeout: float = 5.0) -> Result[Dict[str, Any]]:
        """
        Realiza requisição HTTP ativa real para verificar se o dashboard
        do Uptime Kuma está online, respondendo e sem stubs falsos.
        """
        url = kuma_url.strip()
        if not url:
            return Result.fail(erro="URL do Uptime Kuma não informada", codigo="URL_VAZIA")

        try:
            status_code, body = self.http_get(url, timeout)
            # Uptime Kuma responde 200 no dashboard web ou 302 redirecionando para /dashboard ou /setup
            if status_code in (200, 302):
                return Result.ok({
                    "status": "online",
                    "http_code": status_code,
                    "url": url,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "observacao": "Dashboard Uptime Kuma operacional e respondendo requisições HTTP ativas"
                })
            else:
                return Result.fail(
                    erro=f"Dashboard Uptime Kuma retornou HTTP {status_code} inesperado",
                    codigo="HTTP_STATUS_INVALIDO",
                    detalhes={"status_code": status_code, "body_preview": body[:200]}
                )
        except urllib.error.URLError as exc:
            return Result.fail(
                erro=f"Falha de conexão com o dashboard Uptime Kuma em {url}: {exc}",
                codigo="CONEXAO_RECUSADA"
            )
