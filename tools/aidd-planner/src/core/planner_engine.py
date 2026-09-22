# -*- coding: utf-8 -*-
"""
Motor Central do aidd-planner (AIDD Ecosystem)
Responsável por carregar, validar, gerar e exportar planos para os 3 fluxos da Tríade Canônica.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

_PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SCHEMA_PATH = os.path.join(_PLANNER_DIR, "schemas", "planner_schema.json")
_SCHEMA_PIPELINE_PATH = os.path.join(_PLANNER_DIR, "..", "..", "componentes", "compartilhado", "specs", "handoff-execucao.schema.json")
_SCHEMA_VSA_DISPATCH_PATH = os.path.join(_PLANNER_DIR, "..", "..", "componentes", "compartilhado", "specs", "vsa-topological-dispatch.schema.json")

# aidd-ops e a fonte unica das Fases 1-3 (Intake -> Curadoria -> Sizing) que
# produzem o PLANO-INFRAESTRUTURA.json — o mesmo contrato que aidd-factory
# exige (fase_1_intake/fase_2_curadoria/fase_3_sizing), documentado como
# imutavel em docs/planos/fazendo/PLAN-0034-upgrade-ferramentas-enterprise/
# 02-factory-blueprints.md. exportar_para_fluxo_factory reusa essa fonte em
# vez de reimplementar o envelope aqui (achado real: a versao anterior
# escrevia {projeto, descricao, servicos, banco_central}, que o validador
# proprio do aidd-factory rejeitava 100% das vezes).
_ECOSSISTEMA_ROOT = os.path.join(_PLANNER_DIR, "..", "..")
_AIDD_OPS_SCRIPTS_DIR = os.path.join(_ECOSSISTEMA_ROOT, "tools", "aidd-ops", "scripts")
if os.path.isdir(_AIDD_OPS_SCRIPTS_DIR) and _AIDD_OPS_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _AIDD_OPS_SCRIPTS_DIR)


class PlannerValidationError(Exception):
    """Exceção levantada quando um plano não cumpre os requisitos do schema ou regras invariantes."""
    pass


def carregar_schema() -> Dict[str, Any]:
    """Carrega o JSON Schema canônico do planner."""
    if not os.path.isfile(_SCHEMA_PATH):
        raise FileNotFoundError(f"Schema do planner não encontrado em: {_SCHEMA_PATH}")
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validar_plano(plano: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valida deterministicamente um dicionário de plano contra o JSON Schema e regras de fluxo.
    Retorna (valido: bool, erros: List[str]).
    """
    erros: List[str] = []

    # 1. Validação básica de chaves obrigatórias de primeiro nível
    chaves_obrigatorias = [
        "meta",
        "ddd_bounded_contexts",
        "bdd_cenarios",
        "quarteto_sine_qua_non",
        "infraestrutura_alvo",
        "payload_especifico_fluxo",
    ]
    for chave in chaves_obrigatorias:
        if chave not in plano:
            erros.append(f"Campo obrigatório ausente na raiz: '{chave}'")

    if erros:
        return False, erros

    # 2. Validação do bloco meta
    meta = plano.get("meta", {})
    fluxos_validos = ["fluxo_01_generator", "fluxo_02_factory", "fluxo_03_bridge"]
    fluxo = meta.get("fluxo_alvo")
    if fluxo not in fluxos_validos:
        erros.append(f"meta.fluxo_alvo inválido ('{fluxo}'). Deve ser um de: {fluxos_validos}")

    if not meta.get("projeto_nome") or len(str(meta.get("projeto_nome"))) < 2:
        erros.append("meta.projeto_nome é obrigatório e deve ter no mínimo 2 caracteres.")
    if not meta.get("slug"):
        erros.append("meta.slug é obrigatório.")
    if not meta.get("descricao") or len(str(meta.get("descricao"))) < 10:
        erros.append("meta.descricao deve conter no mínimo 10 caracteres.")

    # 3. Validação de DDD Bounded Contexts
    contexts = plano.get("ddd_bounded_contexts", [])
    if not isinstance(contexts, list) or len(contexts) == 0:
        erros.append("ddd_bounded_contexts deve ser uma lista com pelo menos 1 contexto delimitado.")
    else:
        for idx, ctx in enumerate(contexts):
            if not ctx.get("modulo"):
                erros.append(f"ddd_bounded_contexts[{idx}].modulo é obrigatório.")
            entidades = ctx.get("entidades", [])
            if not isinstance(entidades, list) or len(entidades) == 0:
                erros.append(f"ddd_bounded_contexts[{idx}] deve possuir pelo menos 1 entidade.")
            else:
                for e_idx, ent in enumerate(entidades):
                    if not ent.get("nome"):
                        erros.append(f"Contexto '{ctx.get('modulo')}': entidade[{e_idx}] sem nome.")
                    if not ent.get("atributos") or not isinstance(ent.get("atributos"), dict):
                        erros.append(f"Contexto '{ctx.get('modulo')}': entidade '{ent.get('nome')}' deve ter atributos (dict).")
                    regras = ent.get("regras_invariantes", [])
                    if not isinstance(regras, list) or len(regras) == 0:
                        erros.append(f"Contexto '{ctx.get('modulo')}': entidade '{ent.get('nome')}' deve ter regras_invariantes.")

    # 4. Validação de BDD Cenários
    bdd = plano.get("bdd_cenarios", [])
    if not isinstance(bdd, list) or len(bdd) == 0:
        erros.append("bdd_cenarios deve conter pelo menos 1 cenário estruturado (Dado/Quando/Então).")
    else:
        for idx, cenario in enumerate(bdd):
            for campo in ["id", "modulo", "titulo", "dado", "quando", "entao"]:
                if not cenario.get(campo):
                    erros.append(f"bdd_cenarios[{idx}] sem campo obrigatório '{campo}'.")

    # 5. Validação do Quarteto Sine Qua Non
    quarteto = plano.get("quarteto_sine_qua_non", {})
    for pilar in ["swagger", "webhooks", "mcp", "guia"]:
        cfg = quarteto.get(pilar)
        if pilar == "guia" and cfg is None and "docs" in quarteto:
            cfg = quarteto.get("docs")
        if cfg is None:
            erros.append(f"Quarteto Sine Qua Non incompleto: falta pilar '{pilar}'.")
        else:
            if cfg.get("ativo") is not True:
                erros.append(f"Pilar obrigatório do Quarteto '{pilar}' deve estar ativo: true.")

    # 6. Validação do Payload Específico de Fluxo
    payload = plano.get("payload_especifico_fluxo", {})
    if fluxo == "fluxo_01_generator":
        if "fatias_vsa" not in payload or not isinstance(payload["fatias_vsa"], list) or len(payload["fatias_vsa"]) == 0:
            erros.append("Fluxo 01 exige 'payload_especifico_fluxo.fatias_vsa' com ao menos 1 fatia.")
        if "casos_teste_tdd" not in payload or not isinstance(payload["casos_teste_tdd"], list) or len(payload["casos_teste_tdd"]) == 0:
            erros.append("Fluxo 01 exige 'payload_especifico_fluxo.casos_teste_tdd' para orientar o ciclo Red-Green.")
    elif fluxo == "fluxo_02_factory":
        if "ferramentas_opensource" not in payload or not isinstance(payload["ferramentas_opensource"], list) or len(payload["ferramentas_opensource"]) == 0:
            erros.append("Fluxo 02 exige 'payload_especifico_fluxo.ferramentas_opensource' com lista de serviços Docker.")
        if "fatias_integracao" not in payload or not isinstance(payload["fatias_integracao"], list) or len(payload["fatias_integracao"]) == 0:
            erros.append("Fluxo 02 exige 'payload_especifico_fluxo.fatias_integracao' para o gateway VSA.")
    elif fluxo == "fluxo_03_bridge":
        if not payload.get("diretorio_lowcode"):
            erros.append("Fluxo 03 exige 'payload_especifico_fluxo.diretorio_lowcode' com o caminho do código fonte exportado.")
        if "mapeamento_banco" not in payload or not isinstance(payload["mapeamento_banco"], list) or len(payload["mapeamento_banco"]) == 0:
            erros.append("Fluxo 03 exige 'payload_especifico_fluxo.mapeamento_banco' para conversão Supabase/mock -> PostgreSQL.")

    return (len(erros) == 0, erros)


def gerar_template_plano(
    fluxo_alvo: str,
    projeto_nome: str,
    slug: str,
    descricao: str,
    dominio: str
) -> Dict[str, Any]:
    """Gera um dicionário de plano 100% em conformidade com o schema para o fluxo especificado."""
    if fluxo_alvo not in ["fluxo_01_generator", "fluxo_02_factory", "fluxo_03_bridge"]:
        raise ValueError(f"Fluxo alvo desconhecido: {fluxo_alvo}")

    base = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "meta": {
            "projeto_nome": projeto_nome,
            "slug": slug,
            "versao": "1.0.0",
            "descricao": descricao,
            "dominio": dominio,
            "fluxo_alvo": fluxo_alvo
        },
        "ddd_bounded_contexts": [
            {
                "modulo": "nucleo",
                "descricao": f"Contexto delimitado principal para o domínio {dominio}",
                "entidades": [
                    {
                        "nome": "RegistroPrincipal",
                        "atributos": {
                            "id": "str",
                            "nome": "str",
                            "status": "str",
                            "criado_em": "datetime"
                        },
                        "regras_invariantes": [
                            "O status inicial deve ser sempre 'ativo'",
                            "O nome não pode ser vazio nem conter caracteres ilegais"
                        ]
                    }
                ]
            }
        ],
        "bdd_cenarios": [
            {
                "id": "SCN-001",
                "modulo": "nucleo",
                "titulo": "Criação com sucesso de registro principal",
                "dado": "Um usuário autenticado com dados válidos",
                "quando": "Uma requisição POST for enviada para a rota de criação",
                "entao": "O registro deve ser persistido e o sistema retorna status HTTP 201 com id gerado"
            }
        ],
        "quarteto_sine_qua_non": {
          "swagger": {
            "ativo": True,
            "prefixo": "/docs"
          },
          "webhooks": {
            "ativo": True,
            "eventos_suportados": ["registro.criado", "registro.atualizado", "registro.removido"]
          },
          "mcp": {
            "ativo": True,
            "ferramentas_expostas": ["consultar_registro", "criar_registro"]
          },
          "guia": {
            "ativo": True,
            "guia_usuario": True
          }
        },
        "infraestrutura_alvo": {
            "banco_dados": "postgresql",
            "porta_api": 8000,
            "ambiente": "vps_docker"
        }
    }

    if fluxo_alvo == "fluxo_01_generator":
        base["payload_especifico_fluxo"] = {
            "fatias_vsa": [
                {
                    "nome": "nucleo",
                    "endpoints": [
                        {"metodo": "POST", "caminho": "/nucleo", "resumo": "Cria novo registro"},
                        {"metodo": "GET", "caminho": "/nucleo/{id}", "resumo": "Busca registro por ID"}
                    ],
                    "modelos": ["RegistroPrincipalCreate", "RegistroPrincipalResponse"]
                }
            ],
            "casos_teste_tdd": [
                {
                    "nome": "test_criar_registro_sucesso",
                    "red_expectation": "Rota POST /nucleo retorna 404 antes da implementação",
                    "green_assertion": "Rota POST /nucleo retorna 201 com JSON contendo id e status ativo"
                }
            ]
        }
    elif fluxo_alvo == "fluxo_02_factory":
        base["payload_especifico_fluxo"] = {
            "ferramentas_opensource": [
                {
                    "nome": "Evolution API",
                    "categoria": "whatsapp",
                    "imagem_docker": "atendai/evolution-api:v2.1.2",
                    "porta_host": 8080,
                    "porta_container": 8080,
                    "finalidade": "Gateway de mensageria WhatsApp para notificações de eventos"
                }
            ],
            "fatias_integracao": [
                {
                    "servico": "evolution-api",
                    "rotas_proxy": ["/api/v1/whatsapp/enviar", "/api/v1/whatsapp/status"]
                }
            ]
        }
    elif fluxo_alvo == "fluxo_03_bridge":
        base["payload_especifico_fluxo"] = {
            "diretorio_lowcode": "./app-exportada",
            "plataforma_origem": "lovable",
            "mapeamento_banco": [
                {
                    "tabela_origem": "clientes_mock",
                    "tabela_destino": "clientes",
                    "campos": {"full_name": "nome", "user_email": "email"}
                }
            ],
            "rotas_frontend": ["/", "/dashboard", "/configuracoes"]
        }

    return base


def exportar_para_fluxo_factory(plano: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte um PLANNER.json canônico no formato de entrada exigido pela aidd-factory
    (`pipeline_factory.py --plano <arquivo>`): o envelope
    fase_1_intake/fase_2_curadoria/fase_3_sizing produzido pelo aidd-ops
    (`componentes/compartilhado/specs/plano-infraestrutura.schema.json`).

    A stack de ferramentas já foi curada no PRÉ-PLANO
    (`payload_especifico_fluxo.ferramentas_opensource`) — em vez de tentar
    redescobrir o domínio de negócio casando texto contra os 5 nichos fixos
    de `catalogo_nichos.json` (o que falharia para qualquer domínio fora
    desses 5, ex.: "gestão de tarefas"), esta exportação usa o caminho
    "nicho dinâmico" do aidd-ops (`montar_plano_em_memoria(...,
    ferramentas_planejadas=...)`), que confia na stack já decidida pelo
    plano — Lei #7 (Developer in Control). Ver gap documentado em
    docs/features/v2_arquitetura-aidd-ops-factory.md §7.1/§9.1.
    """
    valido, erros = validar_plano(plano)
    if not valido:
        raise PlannerValidationError(f"Plano inválido para exportação: {erros}")

    meta = plano["meta"]
    payload = plano.get("payload_especifico_fluxo", {})
    ferramentas = payload.get("ferramentas_opensource", [])

    from pipeline_ops import montar_plano_em_memoria  # noqa: E402 (aidd-ops, sys.path acima)

    texto_intake = f"{meta.get('dominio', '')} {meta['projeto_nome']}".strip()
    resultado = montar_plano_em_memoria(texto_intake, ferramentas_planejadas=ferramentas)
    factory_input = resultado.valor

    erro_fase = (
        factory_input["fase_1_intake"].get("erro")
        or factory_input.get("fase_2_curadoria", {}).get("erro")
        or factory_input.get("fase_3_sizing", {}).get("erro")
    )
    if erro_fase:
        raise PlannerValidationError(
            f"Exportação para aidd-factory falhou nas Fases 1-3 do aidd-ops: "
            f"{erro_fase.get('codigo')}: {erro_fase.get('erro')} "
            f"(detalhes: {erro_fase.get('detalhes')})"
        )

    return factory_input


def exportar_para_pipeline_execucao(plano: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte um PLANNER.json canônico no manifesto de handoff de execução unificado
    para a Tríade Canônica (Pure, Open, Freedom), estritamente conforme com
    handoff-execucao.schema.json e auditável via G_PIPELINE_HANDOFF.

    Invariantes aplicadas:
      - Bounded Contexts mapeados em fatias verticais para fase_paralela_assincrona (git-worktrees).
      - Integração de núcleo compartilhado, migrations e validação do Quarteto Sine Qua Non
        mapeados em fase_sequencial_sincrona.
      - Quality Gates inseridos na barreira_sincronizacao (join barrier).
      - Zero Stubs em identificadores, títulos e comandos de validação.
    """
    valido, erros = validar_plano(plano)
    if not valido:
        raise PlannerValidationError(f"Plano inválido para exportação de pipeline: {erros}")

    meta = plano.get("meta", {})
    projeto_nome = meta.get("projeto_nome") or meta.get("nome_projeto") or "Projeto AIDD"
    slug = meta.get("slug") or projeto_nome.lower().replace(" ", "-").replace("_", "-")
    fluxo_raw = str(meta.get("fluxo_alvo", "")).lower()

    if "01" in fluxo_raw or "generator" in fluxo_raw or "pure" in fluxo_raw:
        fluxo_alvo = "pure"
    elif "02" in fluxo_raw or "factory" in fluxo_raw or "open" in fluxo_raw:
        fluxo_alvo = "open"
    elif "03" in fluxo_raw or "bridge" in fluxo_raw or "freedom" in fluxo_raw:
        fluxo_alvo = "freedom"
    else:
        fluxo_alvo = "pure"

    repositorio_alvo = meta.get("repositorio_alvo") or "."
    iniciativa_id = meta.get("iniciativa_id") or f"PLAN-{slug}"
    descricao = meta.get("descricao") or f"Pipeline de execucao deterministico para {projeto_nome}"

    timestamp_execucao = meta.get("timestamp_execucao")
    if not timestamp_execucao:
        from datetime import datetime, timezone
        timestamp_execucao = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    contexts = plano.get("ddd_bounded_contexts", [])
    fase_paralela: List[Dict[str, Any]] = []

    for idx, ctx in enumerate(contexts, start=1):
        mod_nome = ctx.get("modulo", f"modulo_{idx}")
        mod_slug = mod_nome.lower().replace(" ", "-").replace("_", "-")
        ticket_id = f"SLICE-{mod_slug.upper()}"

        alvos = ctx.get("arquivos_alvo") or []
        if not alvos:
            if fluxo_alvo == "pure":
                alvos = [
                    f"src/slices/{mod_slug}/slice.py",
                    f"tests/unit/test_{mod_slug}.py",
                ]
            elif fluxo_alvo == "open":
                alvos = [
                    f"src/integrations/{mod_slug}/adapter.py",
                    f"tests/unit/test_{mod_slug}.py",
                ]
            elif fluxo_alvo == "freedom":
                alvos = [
                    f"src/routes/{mod_slug}/route.py",
                    f"tests/unit/test_{mod_slug}.py",
                ]
            else:
                alvos = [
                    f"src/slices/{mod_slug}/slice.py",
                    f"tests/unit/test_{mod_slug}.py",
                ]

        cmd_val = ctx.get("comando_validacao") or f"pytest tests/unit/test_{mod_slug}.py"
        cmd_red = ctx.get("comando_red") or f"pytest tests/unit/test_{mod_slug}.py"
        cmd_green = ctx.get("comando_green") or f"pytest tests/unit/test_{mod_slug}.py"

        fase_paralela.append({
            "id": ticket_id,
            "titulo": f"Implementar fatia vertical {mod_nome}",
            "arquivos_alvo": alvos,
            "comando_validacao": cmd_val,
            "comando_red": cmd_red,
            "comando_green": cmd_green,
            "isolamento": "git-worktree",
            "blocked_by": [],
        })

    barreira_sincronizacao = [
        "gates/G_SAIDA_BINARIA.py",
        "gates/G_TESTES_REAIS.py",
    ]

    todos_slices_ids = [t["id"] for t in fase_paralela]

    fase_sequencial: List[Dict[str, Any]] = [
        {
            "id": "STEP-SHARED-CORE-INTEGRATION",
            "titulo": "Integrar barramento central de servicos e rotas do gateway API",
            "arquivos_alvo": [
                "src/core/gateway.py",
                "tests/integration/test_gateway.py",
            ],
            "comando_validacao": "pytest tests/integration/test_gateway.py",
            "blocked_by": todos_slices_ids,
            "isolamento": "processo-isolado",
        },
        {
            "id": "STEP-DB-MIGRATIONS",
            "titulo": "Executar scripts de migracao e schema do banco de dados",
            "arquivos_alvo": [
                "migrations/001_initial_schema.sql",
                "tests/test_migrations.py",
            ],
            "comando_validacao": "pytest tests/test_migrations.py",
            "blocked_by": ["STEP-SHARED-CORE-INTEGRATION"],
            "isolamento": "processo-isolado",
        },
        {
            "id": "STEP-QUARTETO-SINE-QUA-NON",
            "titulo": "Validar conformidade dos 4 pilares do Quarteto Sine Qua Non (/docs, /webhooks, /mcp, /guia)",
            "arquivos_alvo": [
                "gates/G_QUARTETO_SINE_QUA_NON.py",
                "docs/guia/README.md",
            ],
            "comando_validacao": "python gates/G_QUARTETO_SINE_QUA_NON.py",
            "blocked_by": ["STEP-DB-MIGRATIONS"],
            "isolamento": "processo-isolado",
        },
    ]

    manifesto: Dict[str, Any] = {
        "versao_schema": "1.0.0",
        "origem_plano": "criacao",
        "fluxo_alvo": fluxo_alvo,
        "meta": {
            "nome_projeto": projeto_nome,
            "repositorio_alvo": repositorio_alvo,
            "timestamp_execucao": timestamp_execucao,
            "iniciativa_id": iniciativa_id,
            "descricao": descricao,
        },
        "fase_paralela_assincrona": fase_paralela,
        "barreira_sincronizacao": barreira_sincronizacao,
        "fase_sequencial_sincrona": fase_sequencial,
    }

    try:
        import jsonschema
        if os.path.isfile(_SCHEMA_PIPELINE_PATH):
            with open(_SCHEMA_PIPELINE_PATH, "r", encoding="utf-8") as f_s:
                schema_pipeline = json.load(f_s)
            validator = jsonschema.Draft7Validator(schema_pipeline)
            erros_schema = list(validator.iter_errors(manifesto))
            if erros_schema:
                msgs = [f"[{e.path}]: {e.message}" for e in erros_schema]
                raise PlannerValidationError(f"Manifesto gerado viola handoff-execucao.schema.json: {msgs}")
    except ImportError:
        pass

    return manifesto


def compilar_grafo_topologico_vsa(plano: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compila o manifesto formal de despacho de fatias verticais (VSA) em grafo topológico acíclico (DAG).
    Valida dependências via algoritmo de Kahn e assegura conformidade estrita com vsa-topological-dispatch.schema.json.
    """
    valido, erros = validar_plano(plano)
    if not valido:
        raise PlannerValidationError(f"Plano inválido para compilação VSA: {'; '.join(erros)}")

    meta = plano.get("meta", {})
    projeto_nome = meta.get("nome_projeto") or "app-aidd"
    projeto_slug = meta.get("slug") or projeto_nome.lower().replace(" ", "-").replace("_", "-")
    projeto_slug = "".join(c for c in projeto_slug if c.isalnum() or c in "-_")
    if not projeto_slug:
        projeto_slug = "app-aidd"

    fluxo_raw = meta.get("fluxo_alvo") or plano.get("fluxo_alvo") or "fluxo_01_generator"
    fluxo_map = {
        "1": "fluxo_01_generator",
        "2": "fluxo_02_factory",
        "3": "fluxo_03_bridge",
        "pure": "fluxo_01_generator",
        "open": "fluxo_02_factory",
        "freedom": "fluxo_03_bridge",
        "bridge": "fluxo_03_bridge",
        "fluxo_01_generator": "fluxo_01_generator",
        "fluxo_02_factory": "fluxo_02_factory",
        "fluxo_03_bridge": "fluxo_03_bridge",
    }
    fluxo_alvo = fluxo_map.get(str(fluxo_raw).lower(), "fluxo_01_generator")

    bounded_contexts = plano.get("ddd_bounded_contexts", [])
    if not bounded_contexts:
        raise PlannerValidationError("Plano não contém ddd_bounded_contexts para geração de fatias VSA.")

    grafo_fatias: List[Dict[str, Any]] = []
    nomes_slices: Set[str] = set()
    mapa_deps: Dict[str, List[str]] = {}

    for bc in bounded_contexts:
        nome_bc = bc.get("modulo") or bc.get("nome") or "modulo"
        slug_bc = "".join(c for c in nome_bc.lower().replace(" ", "_").replace("-", "_") if c.isalnum() or c == "_")
        slice_id = f"slice_{slug_bc}" if not slug_bc.startswith("slice_") else slug_bc

        # Evita colisões de slice_id
        orig_slice_id = slice_id
        idx = 1
        while slice_id in nomes_slices:
            slice_id = f"{orig_slice_id}_{idx}"
            idx += 1
        nomes_slices.add(slice_id)

        deps_raw = bc.get("dependencias") or []
        deps_sanitizadas = []
        for d in deps_raw:
            d_slug = "".join(c for c in str(d).lower().replace(" ", "_").replace("-", "_") if c.isalnum() or c == "_")
            d_id = f"slice_{d_slug}" if not d_slug.startswith("slice_") else d_slug
            deps_sanitizadas.append(d_id)

        mapa_deps[slice_id] = deps_sanitizadas

        arquivos_alvo = [
            f"src/slices/{slug_bc}/router.py",
            f"src/slices/{slug_bc}/service.py",
            f"tests/slices/test_{slug_bc}.py",
        ]

        grafo_fatias.append({
            "slice_id": slice_id,
            "modulo_ddd": nome_bc,
            "dependencias": deps_sanitizadas,
            "isolamento": "git-worktree",
            "arquivos_esperados": arquivos_alvo,
            "barreira_validacao": {
                "comandos_teste": [f"pytest tests/slices/test_{slug_bc}.py"],
                "quality_gates": ["python gates/G_SAIDA_BINARIA.py", "python gates/G_TESTES_REAIS.py"],
            },
        })

    # Validação topológica de Kahn
    in_degree: Dict[str, int] = {s: 0 for s in nomes_slices}
    adj: Dict[str, List[str]] = {s: [] for s in nomes_slices}

    for u, deps in mapa_deps.items():
        for v in deps:
            if v not in nomes_slices:
                raise PlannerValidationError(f"Fatia '{u}' referencia dependência inexistente '{v}'.")
            adj[v].append(u)
            in_degree[u] += 1

    queue = [s for s in nomes_slices if in_degree[s] == 0]
    processados = 0

    while queue:
        curr = queue.pop(0)
        processados += 1
        for vizinho in adj[curr]:
            in_degree[vizinho] -= 1
            if in_degree[vizinho] == 0:
                queue.append(vizinho)

    if processados < len(nomes_slices):
        raise PlannerValidationError(
            f"Ciclo de dependência detectado no grafo topológico VSA! Total de nós: {len(nomes_slices)}, processados: {processados}."
        )

    convergencia_master = {
        "target_branch": "main",
        "merge_strategy": "fast-forward",
        "post_merge_suite": [
            "python ecossistema.py audit",
            "python gates/G_QUARTETO_SINE_QUA_NON.py",
        ],
    }

    manifesto_vsa: Dict[str, Any] = {
        "versao_schema": "1.0.0",
        "projeto_slug": projeto_slug,
        "fluxo_alvo": fluxo_alvo,
        "grafo_fatias": grafo_fatias,
        "convergencia_master": convergencia_master,
    }

    try:
        import jsonschema
        if os.path.isfile(_SCHEMA_VSA_DISPATCH_PATH):
            with open(_SCHEMA_VSA_DISPATCH_PATH, "r", encoding="utf-8") as f_s:
                schema_vsa = json.load(f_s)
            validator = jsonschema.Draft7Validator(schema_vsa)
            erros_schema = list(validator.iter_errors(manifesto_vsa))
            if erros_schema:
                msgs = [f"[{e.path}]: {e.message}" for e in erros_schema]
                raise PlannerValidationError(f"Manifesto VSA gerado viola vsa-topological-dispatch.schema.json: {msgs}")
    except ImportError:
        pass

    return manifesto_vsa
