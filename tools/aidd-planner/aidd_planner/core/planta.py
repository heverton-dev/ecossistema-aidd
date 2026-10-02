# -*- coding: utf-8 -*-
"""Planta baixa com tickets roteados para as 6 ferramentas (Ticket 11, D2, contrato C2).

O aidd-planner deixa de entregar "1 modulo generico so para o construtor". Aqui a
planta e' desenhada de verdade:

1. le o contrato C1 que o aidd-forge gravou (`.aidd/HANDOFF_FORGE_PLANNER.json`)
   e valida contra a fonte unica `componentes/compartilhado/specs/`;
2. deriva `modulos_funcionais` do desenho (DDD bounded contexts + BDD), cada um
   com suas filas e integracoes externas declaradas;
3. deriva `camadas` (horizontais + verticais, ancoradas no terreno provado pelo
   C1) e `fases` (uma por grupo de tickets roteados);
4. roteia um ticket por modulo para o construtor do fluxo e um ticket para cada
   acabamento: aidd-master, aidd-enterprise e aidd-ops — cada ticket com
   `ferramenta_destino`, `entrada`, `saida_esperada`, `pecas_do_almoxarifado` e
   `criterio_de_aceite`;
5. calcula o `perfil_app` **a partir da propria planta** (modulos, entidades,
   persistencia, filas, integracoes, rotas do Quarteto e portas) — nada vem de
   lista fixa de nichos, que era o que reprovava o ops com
   `NICHO_NAO_RECONHECIDO`;
6. monta a `entrada_construtor` especifica do fluxo (plano de motores da factory,
   `origem_export` da bridge, ideia + capacidade de IA do generator).

Determinismo (Lei #1): tudo aqui e' funcao pura do plano e do C1 — mesma entrada,
mesma planta. Nenhuma chamada de LLM, nenhuma lista fixa de nicho.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

try:  # pragma: no cover - a CLI cai no espelho src/ quando o pacote nao existe
    from .planner_engine import PlannerValidationError
except ImportError:  # pragma: no cover
    from src.core.planner_engine import PlannerValidationError

PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAIZ_ECOSSISTEMA = os.path.dirname(os.path.dirname(PLANNER_DIR))
DIRETORIO_SPECS = os.path.join(RAIZ_ECOSSISTEMA, "componentes", "compartilhado", "specs")

HANDOFF_C1_RELATIVO = (".aidd", "HANDOFF_FORGE_PLANNER.json")
SCHEMA_C1_NOME = "handoff-forge-to-planner.schema.json"
SCHEMA_C2_NOME = "handoff-planner-to-engine.schema.json"
MAPA_DONOS_NOME = "MAPA-DONOS-FERRAMENTAS.json"

HANDOFF_C2_NOME = "HANDOFF_PLANNER_ENGINE.json"
HANDOFF_ENGINE_MASTER_NOME = "HANDOFF_ENGINE_MASTER.json"

# As 6 ferramentas que a planta pode enderecar (fonte: MAPA-DONOS-FERRAMENTAS.json).
FERRAMENTAS_DA_PLANTA = (
    "aidd-pure",
    "aidd-open",
    "aidd-freedom",
    "aidd-master",
    "aidd-enterprise",
    "aidd-ops",
)

MAPPED_CONSTRUTOR_POR_FLUXO = {
    1: "aidd-pure",
    2: "aidd-open",
    3: "aidd-freedom",
}

FLUXO_POR_ROTAS_QUARTETO = {
    # O molde `quarteto/variantes/aidd-open` monta o webhook em /webhooks
    # (achado real do E2E: /webhook respondia 404, o canonico e' /webhooks).
    1: "/webhook",
    2: "/webhooks",
    3: "/webhook",
}

CAMADAS_HORIZONTAIS = ("dominio", "aplicacao", "infraestrutura", "interfaces")

FASE_POR_FERRAMENTA = {
    "aidd-pure": "F02-construtor-pure",
    "aidd-open": "F02-construtor-open",
    "aidd-freedom": "F02-construtor-bridge",
    "aidd-master": "F03-harmonizacao-master",
    "aidd-enterprise": "F04-blindagem-enterprise",
    "aidd-ops": "F05-infraestrutura-ops",
}

# Pecas do almoxarifado que cada acabamento consome sob demanda (Lei: quem guarda
# a peca e' o forge; o conteudo da receita e' do dono da receita). Cada lista e'
# filtrada pela evidencia do C1 antes de entrar no ticket — peca nao provada
# nao vira promessa.
PECAS_POR_FERRAMENTA = {
    "aidd-pure": (),
    "aidd-freedom": (),
    "aidd-open": (
        "moldes/quarteto/variantes/aidd-open/openapi.py",
        "moldes/quarteto/variantes/aidd-open/webhooks.py",
        "moldes/quarteto/variantes/aidd-open/mcp_server.py",
    ),
    "aidd-master": (
        "moldes/quarteto/openapi.json.j2",
        "moldes/quarteto/swagger.html",
        "moldes/quarteto/webhook_studio.html",
        "moldes/quarteto/mcp_server.py",
        "moldes/quarteto/docs.html",
    ),
    "aidd-enterprise": (
        "injetor/G_INJECT.py",
        "injetor/inject.py",
        "gates/G_ARQUITETURA.py",
    ),
    "aidd-ops": (
        "moldes/infra/Dockerfile",
        "moldes/infra/docker-compose.yml",
        "moldes/infra/deploy.sh",
        "moldes/infra/nginx/nginx.conf",
    ),
}

TIPOS_CANONICOS = {
    "": "string",
    "str": "string",
    "string": "string",
    "text": "string",
    "texto": "string",
    "<class 'str'>": "string",
    "int": "integer",
    "integer": "integer",
    "<class 'int'>": "integer",
    "bool": "boolean",
    "boolean": "boolean",
    "<class 'bool'>": "boolean",
    "float": "float",
    "<class 'float'>": "float",
    "datetime": "datetime",
    "date": "datetime",
    "timestamp": "datetime",
    "<class 'datetime.datetime'>": "datetime",
    "json": "json",
    "dict": "json",
    "<class 'dict'>": "json",
}

PERSISTENCIA_POR_BANCO = (
    ("postgres", "postgresql"),
    ("mongo", "postgresql"),
    ("sqlite", "sqlite_wal"),
)


class PlantaValidationError(PlannerValidationError):
    """A planta nao pode ser desenhada/roteada com o contrato C1 que chegou."""


# ---------------------------------------------------------------------------
# Utilidades deterministicas
# ---------------------------------------------------------------------------

def tipo_canonico(valor: object) -> str:
    """Normaliza um token de tipo (Python ou textual) para o enum do contrato C2."""
    chave = valor.lower() if isinstance(valor, str) else str(valor)
    return TIPOS_CANONICOS.get(chave, "string")


def slugar(valor: object, padrao: str = "modulo") -> str:
    """Slug deterministico compativel com o padrao `^[a-z0-9-]+$` do contrato C2."""
    bruto = re.sub(r"[^a-z0-9]+", "-", str(valor or "").lower()).strip("-")
    return bruto or padrao


def _sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _sha256_arvore(caminho: str) -> str:
    """SHA-256 estavel de uma pasta: lista relativa + tamanho de cada arquivo."""
    partes: List[str] = []
    for raiz, _pastas, arquivos in os.walk(caminho):
        for arquivo in sorted(arquivos):
            completo = os.path.join(raiz, arquivo)
            relativo = os.path.relpath(completo, caminho).replace(os.sep, "/")
            try:
                tamanho = os.path.getsize(completo)
            except OSError:
                tamanho = -1
            partes.append(f"{relativo}:{tamanho}")
    return _sha256_texto("\n".join(sorted(partes)))


def _carregar_schema(nome: str) -> Dict[str, Any]:
    caminho = os.path.join(DIRETORIO_SPECS, nome)
    if not os.path.isfile(caminho):
        raise PlantaValidationError(f"schema ausente na fonte unica: {caminho}")
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _validar_contra_schema(instancia: Dict[str, Any], nome_schema: str, rotulo: str) -> None:
    try:
        import jsonschema
    except ImportError as erro:  # pragma: no cover - dependencia do ecosistema
        raise PlantaValidationError(
            f"jsonschema indisponivel para validar o {rotulo}: {erro}"
        ) from erro

    schema = _carregar_schema(nome_schema)
    try:
        jsonschema.validate(instance=instancia, schema=schema)
    except jsonschema.ValidationError as erro:
        raise PlantaValidationError(
            f"{rotulo} viola {nome_schema}: {erro.message}"
        ) from erro


# ---------------------------------------------------------------------------
# C1 — leitura do terreno pronto gravado pelo aidd-forge
# ---------------------------------------------------------------------------

def caminho_handoff_c1(pasta_projeto: str) -> str:
    return os.path.join(pasta_projeto, *HANDOFF_C1_RELATIVO)


def validar_handoff_c1(handoff: Dict[str, Any]) -> Dict[str, Any]:
    """Valida o C1 contra a fonte unica; levanta `PlantaValidationError` se violar."""
    if not isinstance(handoff, dict):
        raise PlantaValidationError("C1 invalido: o handoff do forge nao e' um objeto JSON")
    _validar_contra_schema(handoff, SCHEMA_C1_NOME, "contrato C1 (forge -> planner)")
    return handoff


def carregar_handoff_c1(pasta_projeto: str, caminho: Optional[str] = None) -> Dict[str, Any]:
    """Le `.aidd/HANDOFF_FORGE_PLANNER.json` e valida.

    Estrito de proposito: quem chama decide se degrada (a CLI degrada e registra
    aviso, para o E2E nao virar Mentira; o gerador da planta nao inventa terreno).
    """
    alvo = caminho or caminho_handoff_c1(pasta_projeto)
    if not os.path.isfile(alvo):
        raise PlantaValidationError(
            f"C1 ausente: {alvo} nao existe (rode 'forge init' para preparar o terreno)"
        )
    try:
        with open(alvo, "r", encoding="utf-8") as f:
            handoff = json.load(f)
    except (OSError, json.JSONDecodeError) as erro:
        raise PlantaValidationError(f"C1 ilegivel em {alvo}: {erro}") from erro
    return validar_handoff_c1(handoff)


def pecas_disponiveis(handoff_c1: Optional[Dict[str, Any]]) -> Set[str]:
    """Evidencia do almoxarifado provada pelo C1 (vazio quando nao ha C1)."""
    if not handoff_c1:
        return set()
    almoxarifado = handoff_c1.get("almoxarifado") or {}
    return set(almoxarifado.get("pecas_disponiveis") or [])


def _filtrar_pecas(candidatas: Iterable[str], disponiveis: Set[str]) -> List[str]:
    """So entra no ticket a peca que o C1 provou existir (evidencia, nao promessa)."""
    return [peca for peca in dict.fromkeys(candidatas) if peca in disponiveis]


# ---------------------------------------------------------------------------
# Modulos funcionais: o desenho (DDD + BDD) normalizado para o contrato C2
# ---------------------------------------------------------------------------

def derivar_modulos_funcionais(plano: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Converte os bounded contexts do plano no formato `modulos_funcionais` do C2."""
    modulos: List[Dict[str, Any]] = []
    for indice, contexto in enumerate(plano.get("ddd_bounded_contexts") or [], start=1):
        nome = str(contexto.get("modulo") or contexto.get("nome") or f"modulo_{indice}")
        slug = slugar(contexto.get("slug") or nome, padrao=f"modulo-{indice}")

        entidades: List[Dict[str, Any]] = []
        for entidade in contexto.get("entidades") or []:
            atributos = entidade.get("atributos") or {}
            campos = [
                {"nome": chave, "tipo": tipo_canonico(valor), "obrigatorio": True}
                for chave, valor in atributos.items()
            ] or [{"nome": "id", "tipo": "integer", "obrigatorio": True}]
            nome_entidade = str(entidade.get("nome") or f"Registro{indice}")
            entidades.append({"nome": nome_entidade, "campos": campos})

        if not entidades:
            entidades = [{
                "nome": slug.replace("-", " ").title().replace(" ", ""),
                "campos": [{"nome": "id", "tipo": "integer", "obrigatorio": True}],
            }]

        regras = [
            {
                "id": f"RN-{slug}-{num:02d}",
                "descricao": str(regra),
                "criterio_aceitacao": (
                    f"O comportamento de '{regra}' responde 2xx e persiste de forma atomica"
                ),
            }
            for num, regra in enumerate(
                contexto.get("regras_invariantes")
                or [f"O modulo {nome} aplica suas regras a cada entrada"], start=1)
        ]

        modulo: Dict[str, Any] = {
            "nome": nome,
            "slug": slug,
            "entidades": entidades,
            "regras_negocio": regras,
        }
        filas = [str(f) for f in (contexto.get("filas") or []) if str(f).strip()]
        integracoes = [
            str(i) for i in (contexto.get("integracoes_externas") or []) if str(i).strip()
        ]
        if filas:
            modulo["filas"] = list(dict.fromkeys(filas))
        if integracoes:
            modulo["integracoes_externas"] = list(dict.fromkeys(integracoes))
        modulos.append(modulo)
    return modulos


# ---------------------------------------------------------------------------
# Camadas e fases: a forma da planta
# ---------------------------------------------------------------------------

def derivar_camadas(
    handoff_c1: Optional[Dict[str, Any]],
    slugs_modulos: Sequence[str],
) -> List[str]:
    """Camadas da planta: horizontais + verticais, ancoradas no terreno do C1.

    Uma camada so entra se o C1 prova que a pasta que a sustenta existe
    (`governance` -> `governanca`, `pipeline_phases` -> `orquestracao_fases`);
    as camadas do app e o Quarteto (Lei #10) sao invariantes do desenho.
    """
    pastas = set()
    if handoff_c1:
        estrutura = handoff_c1.get("estrutura_projeto") or {}
        pastas = set(estrutura.get("pastas_criadas") or [])

    camadas: List[str] = []
    if "governance" in pastas:
        camadas.append("governanca")
    camadas.extend(CAMADAS_HORIZONTAIS)
    if "pipeline_phases" in pastas:
        camadas.append("orquestracao_fases")
    camadas.append("quarteto")
    camadas.extend(f"fatia:{slug}" for slug in slugs_modulos)
    return camadas


def derivar_fases(tickets: Sequence[Dict[str, Any]]) -> List[str]:
    """Uma fase por grupo de tickets, na ordem em que a planta roteia."""
    fases: List[str] = []
    for ferramenta in dict.fromkeys(t.get("ferramenta_destino") for t in tickets):
        if not ferramenta:
            continue
        fase = FASE_POR_FERRAMENTA.get(ferramenta)
        if fase and fase not in fases:
            fases.append(fase)
    return fases


# ---------------------------------------------------------------------------
# Tickets roteados: um para o construtor do fluxo, um para cada acabamento
# ---------------------------------------------------------------------------

def _ticket(
    identificador: str,
    ferramenta: str,
    entrada: Dict[str, Any],
    saida_esperada: str,
    pecas: Sequence[str],
    criterio: str,
) -> Dict[str, Any]:
    return {
        "id": identificador,
        "ferramenta_destino": ferramenta,
        "entrada": entrada,
        "saida_esperada": saida_esperada,
        "pecas_do_almoxarifado": list(pecas),
        "criterio_de_aceite": criterio,
    }


def rotear_tickets(
    plano: Dict[str, Any],
    modulos_funcionais: Sequence[Dict[str, Any]],
    handoff_c1: Optional[Dict[str, Any]] = None,
    fluxo_num: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Roteia a planta para as ferramentas donas de cada etapa.

    Construtor do fluxo (um ticket por fatia vertical), aidd-master,
    aidd-enterprise e aidd-ops. Cada ticket carrega a entrada de trabalho, a
    saida esperada, as pecas do almoxarifado que a etapa vai consumir e o
    criterio de aceite binario.
    """
    numero = _resolver_fluxo(plano, fluxo_num)
    construtor = MAPPED_CONSTRUTOR_POR_FLUXO[numero]
    disponiveis = pecas_disponiveis(handoff_c1)
    pecas_construtor = _filtrar_pecas(PECAS_POR_FERRAMENTA[construtor], disponiveis)

    tickets: List[Dict[str, Any]] = []
    for indice, modulo in enumerate(modulos_funcionais, start=1):
        slug = modulo["slug"]
        tickets.append(_ticket(
            f"TCK-C{indice:02d}",
            construtor,
            {
                "modulo": modulo["nome"],
                "slug": slug,
                "entidades": [entidade["nome"] for entidade in modulo["entidades"]],
                "regras_negocio": [
                    regra["id"] for regra in modulo["regras_negocio"]
                ],
                "bdd_cenarios": [
                    cenario.get("id")
                    for cenario in (plano.get("bdd_cenarios") or [])
                    if cenario.get("modulo") == modulo["nome"]
                ],
                "fatia_esperada": f"src/modules/{slug}/",
                "hoteis_do_c1": {
                    "leis_e_guardas": [
                        lei.get("gate") for lei in (handoff_c1 or {}).get("leis_e_guardas") or []
                    ],
                },
            },
            f"Fatia vertical `{slug}` gerada em `src/modules/{slug}/` com testes "
            f"Red-Green passando e nenhum arquivo fora da zona do construtor",
            pecas_construtor,
            f"`src/modules/{slug}/` existe com testes reais do modulo e "
            f"`{HANDOFF_ENGINE_MASTER_NOME}` grava os slices com hash da arvore",
        ))

    slugs = [modulo["slug"] for modulo in modulos_funcionais]
    rotas = rotas_quarteto(plano, numero)

    tickets.append(_ticket(
        "TCK-MASTER",
        "aidd-master",
        {
            "fatias": [f"src/modules/{slug}/" for slug in slugs],
            "rotas_quarteto": list(rotas),
            "casca_compartilhada": ["src/core/", "src/shared/", "frontend/"],
            "dependencias": [ticket["id"] for ticket in tickets],
        },
        "Monolito modular VSA com as 4 rotas do Quarteto subindo "
        f"({', '.join(rotas)}) e `HANDOFF_MASTER_ENTERPRISE.json` gravado",
        _filtrar_pecas(PECAS_POR_FERRAMENTA["aidd-master"], disponiveis),
        "As 4 rotas do Quarteto respondem 2xx/3xx medido e nenhum slice ficou "
        "fora de src/core, src/shared ou frontend",
    ))

    tickets.append(_ticket(
        "TCK-ENTERPRISE",
        "aidd-enterprise",
        {
            "componentes_candidatos": [
                f"src/core/{slug}/" for slug in slugs
            ] or ["src/core/"],
            "catalogo_de_blindagem": "injetor/G_INJECT.py",
            "dependencias": ["TCK-MASTER"],
        },
        "Componentes de missao critica blindados com SHA-256 e "
        "`HANDOFF_ENTERPRISE_OPS.json` gravado com selo e drift medido",
        _filtrar_pecas(PECAS_POR_FERRAMENTA["aidd-enterprise"], disponiveis),
        "`COMPONENT-REGISTRY.json` confere com o sha256 de cada componente e o "
        "verificar-drift devolve exit 0",
    ))

    tickets.append(_ticket(
        "TCK-OPS",
        "aidd-ops",
        {
            "perfil_app": calcular_perfil_app(plano, modulos_funcionais),
            "servicos_declarados": list(modulos_funcionais),
            "dependencias": ["TCK-ENTERPRISE"],
        },
        "Infra gerada a partir do perfil do app (Dockerfile, docker-compose.yml, "
        "deploy.sh e nginx) com os servicos que a planta pediu — nada de nicho adivinhado",
        _filtrar_pecas(PECAS_POR_FERRAMENTA["aidd-ops"], disponiveis),
        "`docker-compose.yml` lista exatamente os servicos de `perfil_app` "
        "(modulos, banco, filas, integracoes e portas) e o build sobe sem nicho fixo",
    ))

    return tickets


# ---------------------------------------------------------------------------
# perfil_app: derivado da propria planta
# ---------------------------------------------------------------------------

def _persistencia(plano: Dict[str, Any]) -> str:
    banco = str((plano.get("infraestrutura_alvo") or {}).get("banco_dados") or "sqlite").lower()
    for marca, valor in PERSISTENCIA_POR_BANCO:
        if marca in banco:
            return valor
    return "sqlite_wal"


def rotas_quarteto(plano: Dict[str, Any], fluxo_num: Optional[int] = None) -> List[str]:
    """Rotas do Quarteto desenhadas no plano (Lei #10), na ordem canônica."""
    numero = _resolver_fluxo(plano, fluxo_num)
    quarteto = plano.get("quarteto_sine_qua_non") or {}
    swagger = quarteto.get("swagger") or {}
    guia = quarteto.get("guia") or quarteto.get("docs") or {}
    rotas = [
        "/api",
        str(swagger.get("prefixo") or "/docs"),
        FLUXO_POR_ROTAS_QUARTETO.get(numero, "/webhook"),
        "/mcp",
        str(guia.get("prefixo") or "/docs/guia"),
    ]
    return list(dict.fromkeys(rotas))


def _integracoes_da_planta(plano: Dict[str, Any]) -> List[str]:
    payload = plano.get("payload_especifico_fluxo") or {}
    integracoes: List[str] = []
    for ferramenta in payload.get("ferramentas_opensource") or []:
        nome = str(ferramenta.get("nome") or "").strip()
        if nome:
            integracoes.append(slugar(nome, padrao="integracao"))
    origem = str(payload.get("plataforma_origem") or "").strip()
    if origem:
        integracoes.append(slugar(origem, padrao="integracao"))
    integracoes.extend(
        str(item.get("nome") or "") for item in (payload.get("fatias_integracao") or [])
    )
    return [item for item in integracoes if item]


def _portas_da_planta(plano: Dict[str, Any]) -> List[int]:
    infra = plano.get("infraestrutura_alvo") or {}
    portas: List[int] = []
    for chave in ("porta_api", "porta_webhook", "porta_mcp"):
        valor = infra.get(chave)
        if isinstance(valor, int):
            portas.append(valor)
    payload = plano.get("payload_especifico_fluxo") or {}
    for ferramenta in payload.get("ferramentas_opensource") or []:
        valor = ferramenta.get("porta_host")
        if isinstance(valor, int):
            portas.append(valor)
    return sorted(set(portas))


def calcular_perfil_app(
    plano: Dict[str, Any],
    modulos_funcionais: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Perfil do app calculado da propria planta (nada de lista fixa de nichos).

    Modulo desenhado vira item de perfil; entidade ganha o modulo como prefixo;
    filas e integracoes vem do que cada modulo declarou e das ferramentas do
    fluxo; rotas vem do Quarteto; portas vem da infraestrutura desenhada.
    """
    numero = _resolver_fluxo(plano, None)
    modulos = [str(modulo["slug"]) for modulo in modulos_funcionais]

    entidades: List[str] = []
    filas: List[str] = []
    integracoes: List[str] = []
    for modulo in modulos_funcionais:
        for entidade in modulo.get("entidades") or []:
            entidades.append(f"{modulo['slug']}.{entidade['nome']}")
        filas.extend(str(f) for f in modulo.get("filas") or [])
        integracoes.extend(str(i) for i in modulo.get("integracoes_externas") or [])
    integracoes.extend(_integracoes_da_planta(plano))

    perfil: Dict[str, Any] = {
        "modulos": modulos,
        "entidades": entidades,
        "banco": _persistencia(plano),
        "filas": sorted(set(filas)),
        "integracoes_externas": sorted(set(integracoes)),
        "rotas_quarteto": rotas_quarteto(plano, numero),
        "portas": _portas_da_planta(plano),
    }
    return perfil


# ---------------------------------------------------------------------------
# entrada_construtor: o que cada construtor precisa para comecar
# ---------------------------------------------------------------------------

def _caminho_relativo_ao_projeto(caminho: str, pasta_projeto: Optional[str]) -> str:
    if not pasta_projeto:
        return caminho
    try:
        relativo = os.path.relpath(os.path.abspath(caminho), os.path.abspath(pasta_projeto))
    except ValueError:  # pragma: no cover - unidades diferentes no Windows
        return caminho
    if relativo.startswith(".."):
        return os.path.abspath(caminho)
    return relativo.replace(os.sep, "/")


def _hash_do_nucleo_do_plano(plano: Dict[str, Any]) -> str:
    """Hash do desenho sem a planta (o handoff nao se auto-referencia)."""
    nucleo = {chave: valor for chave, valor in plano.items() if chave != "planta"}
    return _sha256_texto(json.dumps(nucleo, sort_keys=True, ensure_ascii=False))


def _plano_de_motores(plano: Dict[str, Any]) -> Dict[str, Any]:
    """Entrada da factory: o envelope fase_1/2/3 do aidd-ops (fonte unica)."""
    import importlib
    import sys

    from .planner_engine import _AIDD_OPS_SCRIPTS_DIR

    if os.path.isdir(_AIDD_OPS_SCRIPTS_DIR) and _AIDD_OPS_SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, _AIDD_OPS_SCRIPTS_DIR)

    # aidd-ops: Intake -> Curadoria -> Sizing (nossa fonte unica do plano de motores)
    montar_plano_em_memoria = importlib.import_module("pipeline_ops").montar_plano_em_memoria

    meta = plano.get("meta") or {}
    payload = plano.get("payload_especifico_fluxo") or {}
    texto = f"{meta.get('dominio', '')} {meta.get('projeto_nome', '')}".strip()
    entrada = montar_plano_em_memoria(
        texto,
        ferramentas_planejadas=payload.get("ferramentas_opensource") or [],
    ).valor

    erro = (
        (entrada.get("fase_1_intake") or {}).get("erro")
        or (entrada.get("fase_2_curadoria") or {}).get("erro")
        or (entrada.get("fase_3_sizing") or {}).get("erro")
    )
    if erro:
        raise PlantaValidationError(
            "a factory nao aceitou a entrada do plano: "
            f"{erro.get('codigo')}: {erro.get('erro')} (detalhes: {erro.get('detalhes')})"
        )
    return entrada


def montar_entrada_construtor(
    plano: Dict[str, Any],
    fluxo_num: Optional[int] = None,
    handoff_c1: Optional[Dict[str, Any]] = None,
    pasta_projeto: Optional[str] = None,
) -> Dict[str, Any]:
    """Entrada especifica de cada construtor (Lei: o construtor ve' a planta dela)."""
    numero = _resolver_fluxo(plano, fluxo_num)
    meta = plano.get("meta") or {}
    payload = plano.get("payload_especifico_fluxo") or {}

    entrada: Dict[str, Any] = {
        "origem_export": {
            "caminho": _caminho_planner_json(pasta_projeto),
            "hash": _hash_do_nucleo_do_plano(plano),
        }
    }

    if numero == 1:
        entrada["ideia"] = str(meta.get("descricao") or meta.get("projeto_nome") or "")
        entrada["capacidade_llm"] = str(
            (handoff_c1 or {}).get("capacidade_llm") or "nenhuma"
        )
    elif numero == 2:
        entrada["plano_motores"] = _plano_de_motores(plano)
    else:
        origem = str(payload.get("diretorio_lowcode") or "")
        if origem:
            absoluto = origem if os.path.isabs(origem) else os.path.join(
                pasta_projeto or ".", origem
            )
            entrada["origem_export"] = {
                "caminho": _caminho_relativo_ao_projeto(absoluto, pasta_projeto),
                "hash": _sha256_arvore(absoluto) if os.path.isdir(absoluto)
                else _sha256_texto(origem),
            }
        entrada["plataforma_origem"] = str(payload.get("plataforma_origem") or "")
    return entrada


def _caminho_planner_json(pasta_projeto: Optional[str]) -> str:
    """Caminho do PLANNER.json sempre em notacao POSIX, relativo a raiz do projeto."""
    if not pasta_projeto:
        return "PLANNER.json"
    return _caminho_relativo_ao_projeto(
        os.path.join(pasta_projeto, "PLANNER.json"), pasta_projeto
    )


# ---------------------------------------------------------------------------
# C2 — montagem do handoff completo
# ---------------------------------------------------------------------------

def _resolver_fluxo(plano: Dict[str, Any], fluxo_num: Optional[int]) -> int:
    if isinstance(fluxo_num, int) and fluxo_num in (1, 2, 3):
        return fluxo_num
    meta = plano.get("meta") or {}
    bruto = str(meta.get("fluxo_alvo") or "").lower()
    if "01" in bruto or "generator" in bruto or "pure" in bruto:
        return 1
    if "02" in bruto or "factory" in bruto or "open" in bruto:
        return 2
    if "03" in bruto or "bridge" in bruto or "freedom" in bruto:
        return 3
    return 1


def _arquitetura_alvo(plano: Dict[str, Any], numero: int) -> Dict[str, str]:
    return {
        "padrao_frontend": "tanstack_router_typescript_tailwind",
        "padrao_backend": "fastapi_modular_vsa",
        "persistencia": "postgresql" if numero == 3 else _persistencia(plano),
    }


def _quarteto_contrato(plano: Dict[str, Any]) -> Dict[str, bool]:
    quarteto = plano.get("quarteto_sine_qua_non") or {}
    guia = quarteto.get("guia") or quarteto.get("docs") or {}
    return {
        "swagger": (quarteto.get("swagger") or {}).get("ativo") is True,
        "webhooks": (quarteto.get("webhooks") or {}).get("ativo") is True,
        "mcp": (quarteto.get("mcp") or {}).get("ativo") is True,
        "documentacao": bool(guia.get("ativo") is True or guia.get("guia_usuario") is True),
    }


def montar_handoff_engine(
    plano: Dict[str, Any],
    handoff_c1: Optional[Dict[str, Any]] = None,
    fluxo_num: Optional[int] = None,
    pasta_projeto: Optional[str] = None,
    validar: bool = True,
) -> Dict[str, Any]:
    """Monta o contrato C2 completo (camadas, fases, tickets, entrada e perfil)."""
    numero = _resolver_fluxo(plano, fluxo_num)
    meta = plano.get("meta") or {}
    nome = str(meta.get("projeto_nome") or "Projeto AIDD")
    slug = slugar(meta.get("slug") or nome, padrao="projeto-aidd")
    modulos_funcionais = derivar_modulos_funcionais(plano)

    if not modulos_funcionais:
        raise PlantaValidationError(
            "a planta nao tem modulo desenhado: o PLANNER.json precisa de "
            "ddd_bounded_contexts com modulo e entidades"
        )

    tickets = rotear_tickets(plano, modulos_funcionais, handoff_c1, numero)

    payload: Dict[str, Any] = {
        "versao_schema": "1.0.0",
        "fluxo_alvo": numero,
        "metadados_projeto": {
            "nome": nome,
            "slug": slug,
            "dominio": str(meta.get("dominio") or "generico"),
            "descricao": str(meta.get("descricao") or f"Sistema {nome} no dominio {meta.get('dominio') or 'generico'}"),
        },
        "quarteto_sine_qua_non": _quarteto_contrato(plano),
        "arquitetura_alvo": _arquitetura_alvo(plano, numero),
        "modulos_funcionais": modulos_funcionais,
        "camadas": derivar_camadas(handoff_c1, [modulo["slug"] for modulo in modulos_funcionais]),
        "fases": [],
        "tickets": tickets,
        "entrada_construtor": montar_entrada_construtor(
            plano, numero, handoff_c1, pasta_projeto
        ),
        "perfil_app": calcular_perfil_app(plano, modulos_funcionais),
    }
    payload["fases"] = derivar_fases(tickets)

    avisos: List[str] = []
    if not handoff_c1:
        avisos.append(
            "C1 ausente (.aidd/HANDOFF_FORGE_PLANNER.json): a planta foi desenhada sem "
            "evidencia de almoxarifado e sem ancoragem de governanca — nenhum ticket cita peca"
        )
    if avisos:
        payload["avisos"] = avisos

    if validar:
        _validar_contra_schema(payload, SCHEMA_C2_NOME, "contrato C2 (planner -> engine)")
    return payload


# Alias de leitura: a planta e' o contrato C2.
montar_planta = montar_handoff_engine


def validar_handoff_engine(handoff: Dict[str, Any]) -> Dict[str, Any]:
    """Valida um C2 qualquer contra a fonte unica e devolve o proprio handoff."""
    _validar_contra_schema(handoff, SCHEMA_C2_NOME, "contrato C2 (planner -> engine)")
    return handoff


def gravar_planta(
    pasta_projeto: str,
    plano: Dict[str, Any],
    handoff_c1: Optional[Dict[str, Any]] = None,
    fluxo_num: Optional[int] = None,
) -> Dict[str, Any]:
    """Grava `PLANNER.json` (com a planta) e `HANDOFF_PLANNER_ENGINE.json` (C2).

    Quem produz escreve: os dois arquivos sao gravados pelo proprio planner, com
    o C2 validado contra a fonte unica ANTES de encostar no disco.
    """
    payload = montar_handoff_engine(
        plano, handoff_c1, fluxo_num=fluxo_num, pasta_projeto=pasta_projeto
    )

    plano_com_planta = dict(plano)
    plano_com_planta["planta"] = {
        "camadas": payload["camadas"],
        "fases": payload["fases"],
        "tickets": payload["tickets"],
        "perfil_app": payload["perfil_app"],
        "entrada_construtor": payload["entrada_construtor"],
    }

    caminho_planner = os.path.join(pasta_projeto, "PLANNER.json")
    with open(caminho_planner, "w", encoding="utf-8", newline="\n") as f:
        json.dump(plano_com_planta, f, indent=2, ensure_ascii=False)
        f.write("\n")

    caminho_handoff = os.path.join(pasta_projeto, HANDOFF_C2_NOME)
    with open(caminho_handoff, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return {
        "planta": plano_com_planta,
        "handoff": payload,
        "caminho_planner": caminho_planner,
        "caminho_handoff": caminho_handoff,
    }
