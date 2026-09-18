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
    for pilar in ["swagger", "webhooks", "mcp", "docs"]:
        if pilar not in quarteto:
            erros.append(f"Quarteto Sine Qua Non incompleto: falta pilar '{pilar}'.")
        else:
            if quarteto[pilar].get("ativo") is not True:
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
            "prefixo": "/swagger"
          },
          "webhooks": {
            "ativo": True,
            "eventos_suportados": ["registro.criado", "registro.atualizado", "registro.removido"]
          },
          "mcp": {
            "ativo": True,
            "ferramentas_expostas": ["consultar_registro", "criar_registro"]
          },
          "docs": {
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
