# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — Infra pelo perfil do app (Ticket 16, D1 / DoD 7, contrato C2)
=============================================================================
O ops deixa de adivinhar um nicho pelo texto. Quando a pasta do projeto tem a
planta do planner (`HANDOFF_PLANNER_ENGINE.json`), o ops:

1. valida os PRÓPRIOS tickets (`ferramenta_destino == "aidd-ops"`) e o
   `perfil_app` contra a fonte única `componentes/compartilhado/specs/`, e
   confere que toda peça citada existe no almoxarifado;
2. deriva os serviços do que o app realmente tem: `app` + `nginx` sempre;
   `web` só se o projeto tem `frontend/Dockerfile`; `db` se a persistência é
   PostgreSQL; `fila` se a planta declarou fila;
3. busca as receitas `moldes/infra/*` no almoxarifado (`obter_peca`, com
   conferência de sha256) e as ajusta ao perfil (porta da API, banco, fila,
   upstreams e rotas do Quarteto).

O nicho vira atalho opcional (`--nicho`): sem planta na pasta, o caminho antigo
(casamento de texto contra os 5 nichos) continua igual.

Determinismo (Lei #1): função pura da planta + peças do catálogo. Nenhuma LLM.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import yaml
from jsonschema import ValidationError, validate

def _achar_raiz_repo(inicio: str) -> str:
    curr = inicio
    while curr and os.path.dirname(curr) != curr:
        if os.path.isfile(os.path.join(curr, "ecossistema.py")):
            return curr
        curr = os.path.dirname(curr)
    return os.path.normpath(os.path.join(inicio, "..", "..", "..", ".."))


_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOL_ROOT = os.path.dirname(_SCRIPTS_DIR)
RAIZ_ECOSSISTEMA = _achar_raiz_repo(_TOOL_ROOT)
_VSA_FORGE = os.path.join(RAIZ_ECOSSISTEMA, "modulos", "01-governanca-e-qualidade", "core", "aidd-forge")
_FORGE_DIR = _VSA_FORGE if os.path.isdir(_VSA_FORGE) else os.path.join(RAIZ_ECOSSISTEMA, "modulos", "01-governanca-e-qualidade", "core", "aidd-forge")

for _p in (os.path.join(_TOOL_ROOT, "src"), _FORGE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core_ops.result import Result  # noqa: E402
from aidd_forge.core.almoxarifado import carregar_catalogo, obter_peca  # noqa: E402

ENTRADA_C2 = "HANDOFF_PLANNER_ENGINE.json"
SCHEMA_C2 = os.path.join(
    RAIZ_ECOSSISTEMA, "componentes", "compartilhado", "specs",
    "handoff-planner-to-engine.schema.json",
)
FERRAMENTA_OPS = "aidd-ops"

# Discriminador do caminho "perfil do app" no PLANO-INFRAESTRUTURA.json
# (mesmo espírito de `monolito_customizado` e `dinamico_`): prefixo que nunca
# colide com um slug real do catálogo de nichos.
PERFIL_PREFIXO_SLUG = "perfil"

PORTA_MOLDE = 3000
PORTA_BANCO = 5432
PORTA_FILA = 6379
IMAGEM_BANCO = "postgres:16-alpine"
IMAGEM_FILA = "redis:7-alpine"
USUARIO_BANCO = "aidd"
SENHA_BANCO = "${POSTGRES_PASSWORD:?defina POSTGRES_PASSWORD no .env}"

PECA_DOCKERFILE = "moldes/infra/Dockerfile"
PECA_COMPOSE = "moldes/infra/docker-compose.yml"
PECA_DEPLOY = "moldes/infra/deploy.sh"
PECA_NGINX = "moldes/infra/nginx/nginx.conf"
PECA_SSL = "moldes/infra/nginx/ssl/generate_ssl.py"

# peça -> pasta de destino relativa ao projeto (o deploy.sh chama o generate_ssl.py)
PECAS_INFRA: Tuple[Tuple[str, str], ...] = (
    (PECA_DOCKERFILE, "."),
    (PECA_COMPOSE, "."),
    (PECA_DEPLOY, "."),
    (PECA_NGINX, "nginx"),
    (PECA_SSL, os.path.join("nginx", "ssl")),
)


def eh_origem_perfil(nicho_slug: str) -> bool:
    """True quando o plano veio do perfil do app (planta), não de um nicho."""
    return bool(nicho_slug) and nicho_slug.startswith(f"{PERFIL_PREFIXO_SLUG}_")


def _slug_python(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(texto or "").lower()).strip("_") or "app"


# ---------------------------------------------------------------------------
# Entrada: tickets de ops + perfil_app (contrato C2)
# ---------------------------------------------------------------------------

def _subschemas_c2() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with open(SCHEMA_C2, "r", encoding="utf-8") as f:
        schema = json.load(f)
    propriedades = schema["properties"]
    return propriedades["perfil_app"], propriedades["tickets"]["items"]


def ler_entrada_ops(pasta_projeto: str) -> Optional[Result]:
    """Lê e valida a entrada do ops na planta do projeto.

    Returns:
        None quando a pasta não tem planta (caminho antigo por nicho);
        Result.ok({pasta_projeto, projeto, tickets, perfil_app}) quando a entrada é válida;
        Result.fail(TICKET_OPS_AUSENTE | TICKET_OPS_INVALIDO | PERFIL_APP_INVALIDO
        | PLANTA_ILEGIVEL) quando a planta existe mas não serve ao ops.
    """
    caminho = os.path.join(pasta_projeto, ENTRADA_C2)
    if not os.path.isfile(caminho):
        return None
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            planta = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return Result.fail(
            f"Planta ilegível em {ENTRADA_C2}: {exc}",
            codigo="PLANTA_ILEGIVEL",
            detalhes={"caminho": caminho},
        )

    tickets = [
        t for t in planta.get("tickets") or []
        if isinstance(t, dict) and t.get("ferramenta_destino") == FERRAMENTA_OPS
    ]
    if not tickets:
        return Result.fail(
            f"A planta ({ENTRADA_C2}) não roteou nenhum ticket para {FERRAMENTA_OPS}.",
            codigo="TICKET_OPS_AUSENTE",
            detalhes={"caminho": caminho},
        )

    schema_perfil, schema_ticket = _subschemas_c2()
    nomes_catalogo = {p.get("nome") for p in carregar_catalogo(RAIZ_ECOSSISTEMA).get("pecas", [])}
    for ticket in tickets:
        try:
            validate(instance=ticket, schema=schema_ticket)
        except ValidationError as exc:
            return Result.fail(
                f"Ticket {ticket.get('id', '?')} fora do contrato C2: {exc.message}",
                codigo="TICKET_OPS_INVALIDO",
                detalhes={"ticket": ticket.get("id"), "caminho": list(exc.path)},
            )
        fantasmas = [p for p in ticket["pecas_do_almoxarifado"] if p not in nomes_catalogo]
        if fantasmas:
            return Result.fail(
                f"Ticket {ticket['id']} cita peça(s) fora do almoxarifado: {', '.join(fantasmas)}",
                codigo="TICKET_OPS_INVALIDO",
                detalhes={"ticket": ticket["id"], "pecas_ausentes": fantasmas},
            )

    # O perfil do ticket de ops tem precedência: é a entrada roteada para cá.
    perfil = (tickets[0].get("entrada") or {}).get("perfil_app") or planta.get("perfil_app")
    try:
        validate(instance=perfil, schema=schema_perfil)
    except ValidationError as exc:
        return Result.fail(
            f"perfil_app fora do contrato C2: {exc.message}",
            codigo="PERFIL_APP_INVALIDO",
            detalhes={"caminho": list(exc.path)},
        )

    projeto = planta.get("metadados_projeto") or {}
    nome = str(projeto.get("nome") or os.path.basename(os.path.normpath(pasta_projeto)))
    return Result.ok({
        "pasta_projeto": pasta_projeto,
        "projeto": {"nome": nome, "slug": str(projeto.get("slug") or nome)},
        "tickets": [t["id"] for t in tickets],
        "perfil_app": perfil,
    })


# ---------------------------------------------------------------------------
# Serviços derivados do perfil
# ---------------------------------------------------------------------------

def projeto_usa_sqlite_wal(pasta_projeto: str, perfil: Optional[Dict[str, Any]] = None) -> bool:
    """Detecta se o projeto adota arquitetura soberana baseada em SQLite WAL (T-005)."""
    banco_perfil = str((perfil or {}).get("banco") or "").lower()
    if "sqlite" in banco_perfil:
        return True

    server_py = os.path.join(pasta_projeto, "src", "server.py")
    if os.path.isfile(server_py):
        try:
            with open(server_py, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                if "sqlite" in content:
                    return True
        except Exception:
            pass

    planner_json = os.path.join(pasta_projeto, "PLANNER.json")
    if os.path.isfile(planner_json):
        try:
            with open(planner_json, "r", encoding="utf-8") as f:
                pj = json.load(f)
                infra = pj.get("infraestrutura_alvo", {})
                if "sqlite" in str(infra.get("banco_dados") or "").lower():
                    return True
        except Exception:
            pass

    return False


def tem_banco_relacional(perfil: Dict[str, Any]) -> bool:
    return "postgres" in str(perfil.get("banco") or "").lower()


def tem_frontend(pasta_projeto: str) -> bool:
    return os.path.isfile(os.path.join(pasta_projeto, "frontend", "Dockerfile"))


def porta_api(perfil: Dict[str, Any]) -> int:
    portas = perfil.get("portas") or []
    return int(portas[0]) if portas else PORTA_MOLDE


def nome_banco(projeto: Dict[str, Any]) -> str:
    return _slug_python(projeto.get("slug"))


def servicos_do_perfil(perfil: Dict[str, Any], pasta_projeto: str) -> List[str]:
    """Serviços do compose, na ordem: app, nginx, [web], [db], [fila]."""
    servicos = ["app", "nginx"]
    if tem_frontend(pasta_projeto):
        servicos.append("web")
    if tem_banco_relacional(perfil) and not projeto_usa_sqlite_wal(pasta_projeto, perfil):
        servicos.append("db")
    if perfil.get("filas"):
        servicos.append("fila")
    return servicos


# ---------------------------------------------------------------------------
# Render das peças ajustadas ao perfil
# ---------------------------------------------------------------------------

def _ler(caminho: str) -> str:
    with open(caminho, "r", encoding="utf-8", newline="") as f:
        return f.read()


def _gravar(caminho: str, texto: str) -> None:
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        f.write(texto)


def renderizar_dockerfile(molde: str, porta: int) -> str:
    return molde if porta == PORTA_MOLDE else molde.replace(str(PORTA_MOLDE), str(porta))


def renderizar_compose(
    molde: str,
    perfil: Dict[str, Any],
    servicos: List[str],
    banco: str,
) -> Dict[str, Any]:
    base = yaml.safe_load(molde)
    moldes = base["services"]
    porta = porta_api(perfil)

    app = copy.deepcopy(moldes["app"])
    ambiente = [e for e in app.get("environment") or [] if not e.startswith("PORT=")]
    ambiente.insert(0, f"PORT={porta}")
    ambiente.append(f"AIDD_MODULOS={','.join(perfil.get('modulos') or [])}")
    if perfil.get("integracoes_externas"):
        ambiente.append(f"AIDD_INTEGRACOES_EXTERNAS={','.join(perfil['integracoes_externas'])}")
    depende: Dict[str, Any] = {}
    if "db" in servicos:
        ambiente.append(
            f"DATABASE_URL=postgresql://{USUARIO_BANCO}:{SENHA_BANCO}@db:{PORTA_BANCO}/{banco}"
        )
        depende["db"] = {"condition": "service_healthy"}
    if "fila" in servicos:
        ambiente.append(f"REDIS_URL=redis://fila:{PORTA_FILA}/0")
        ambiente.append(f"AIDD_FILAS={','.join(perfil['filas'])}")
        depende["fila"] = {"condition": "service_healthy"}
    app["environment"] = ambiente
    teste = app.get("healthcheck", {}).get("test")
    if teste:
        app["healthcheck"]["test"] = [
            str(p).replace(f":{PORTA_MOLDE}/", f":{porta}/") for p in teste
        ]
    if depende:
        app["depends_on"] = depende

    nginx = copy.deepcopy(moldes["nginx"])
    nginx["depends_on"] = {
        nome: cond for nome, cond in (nginx.get("depends_on") or {}).items() if nome in servicos
    }

    saida: Dict[str, Any] = {"app": app, "nginx": nginx}
    if "web" in servicos:
        saida["web"] = copy.deepcopy(moldes["web"])
    rede = next(iter(base.get("networks") or {"aidd_network": None}))
    volumes = copy.deepcopy(base.get("volumes") or {})
    if "db" in servicos:
        saida["db"] = {
            "image": IMAGEM_BANCO,
            "restart": "always",
            "environment": [
                f"POSTGRES_DB={banco}",
                f"POSTGRES_USER={USUARIO_BANCO}",
                f"POSTGRES_PASSWORD={SENHA_BANCO}",
            ],
            "volumes": ["db_data:/var/lib/postgresql/data"],
            "networks": [rede],
            "healthcheck": {
                "test": ["CMD-SHELL", f"pg_isready -U {USUARIO_BANCO} -d {banco}"],
                "interval": "10s", "timeout": "5s", "retries": 5,
            },
        }
        volumes["db_data"] = {"driver": "local"}
    else:
        volumes["app_data"] = {"driver": "local"}
    if "fila" in servicos:
        saida["fila"] = {
            "image": IMAGEM_FILA,
            "restart": "always",
            "volumes": ["fila_data:/data"],
            "networks": [rede],
            "healthcheck": {
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "10s", "timeout": "5s", "retries": 5,
            },
        }
        volumes["fila_data"] = {"driver": "local"}

    return {"services": saida, "volumes": volumes, "networks": base.get("networks")}


_RE_LOCATION = re.compile(r"^\s*location\s+(=\s+)?(\S+)", re.MULTILINE)


def renderizar_nginx(molde: str, perfil: Dict[str, Any], servicos: List[str]) -> str:
    porta = porta_api(perfil)
    texto = molde.replace(f"server app:{PORTA_MOLDE}", f"server app:{porta}")
    if "web" not in servicos:
        # Sem front-end o upstream do front cai no próprio app: nginx nunca
        # resolve um host `web` que não existe no compose.
        texto = re.sub(r"server web:\d+", f"server app:{porta}", texto)

    prefixos = [m.group(2) for m in _RE_LOCATION.finditer(texto) if not m.group(1)]
    exatas = {m.group(2) for m in _RE_LOCATION.finditer(texto) if m.group(1)}
    faltando = [
        rota for rota in perfil.get("rotas_quarteto") or []
        if rota not in exatas
        and not any(p != "/" and rota.startswith(p) for p in prefixos)
    ]
    ancora = re.search(r"^([ \t]*)location /static/", texto, re.MULTILINE)
    if faltando and ancora:
        linhas = "".join(
            f"{ancora.group(1)}location {rota} {{ limit_req zone=api_limit burst=50 nodelay; "
            f"proxy_pass http://aidd_backend; }}\n"
            for rota in faltando
        )
        texto = texto[:ancora.start()] + linhas + texto[ancora.start():]
    return texto


# ---------------------------------------------------------------------------
# Geração no projeto
# ---------------------------------------------------------------------------

def gerar_infra(entrada: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Busca as peças `moldes/infra/*` no almoxarifado e as ajusta ao perfil.

    Returns:
        Lista (nome da peça, caminho gravado no projeto).

    Raises:
        ValueError / FileNotFoundError do almoxarifado (peça ausente, sha256
        violado ou destino dentro de tools/) — o chamador converte em exit 1.
    """
    pasta_projeto = entrada["pasta_projeto"]
    perfil = entrada["perfil_app"]
    servicos = servicos_do_perfil(perfil, pasta_projeto)
    gravados: List[Tuple[str, str]] = []
    for nome, sub in PECAS_INFRA:
        destino = os.path.normpath(os.path.join(pasta_projeto, sub))
        os.makedirs(destino, exist_ok=True)
        gravados.append((nome, str(obter_peca(nome, destino, raiz=RAIZ_ECOSSISTEMA))))
    arquivo = dict(gravados)

    _gravar(arquivo[PECA_DOCKERFILE], renderizar_dockerfile(
        _ler(arquivo[PECA_DOCKERFILE]), porta_api(perfil)))

    compose = renderizar_compose(
        _ler(arquivo[PECA_COMPOSE]), perfil, servicos, nome_banco(entrada["projeto"]))
    cabecalho = (
        f"# Gerado pelo aidd-ops a partir da peça {PECA_COMPOSE} (almoxarifado)\n"
        f"# e do perfil_app da planta ({ENTRADA_C2}). Serviços: {', '.join(servicos)}.\n"
    )
    _gravar(arquivo[PECA_COMPOSE], cabecalho + yaml.safe_dump(
        compose, sort_keys=False, allow_unicode=True, default_flow_style=False))

    _gravar(arquivo[PECA_NGINX], renderizar_nginx(_ler(arquivo[PECA_NGINX]), perfil, servicos))
    return gravados
