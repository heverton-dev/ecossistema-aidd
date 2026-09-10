# -*- coding: utf-8 -*-
"""
Rotas finas (thin routes adapter) da fatia vertical modulo1.

Padrão Clean Architecture para a camada de Interfaces: aqui SÓ existe o
mapeamento HTTP -> Use Case/Application Service -> DTO. Nenhum SQL, nenhuma
regra de negócio, nenhuma manipulação direta de persistência.
"""

from __future__ import annotations

from typing import Any, Optional

from core.cqrs import read_model
from core.openapi import RouteRegistry

registry = RouteRegistry()


def _extrair(query_params: dict, nome: str):
    """Normaliza parâmetro vindo de query string (lista ou escalar)."""
    valor = query_params.get(nome)
    if isinstance(valor, list):
        return valor[0] if valor else None
    return valor


def registrar_rotas(service: Any = None):
    tag_name = "Modulo1"

    @registry.get(
        "/api/modulo1",
        summary="Listar todos os itens do módulo modulo1",
        tags=[tag_name],
        description="Retorna a lista de registros cadastrados no módulo modulo1.",
        query_params=[
            {"name": "status", "type": "string", "req": False, "desc": "Filtrar por status"},
            {"name": "apenas_ativos", "type": "boolean", "req": False, "desc": "Filtrar apenas itens ativos (default True)"},
            {"name": "busca", "type": "string", "req": False, "desc": "Busca textual por título/descrição"},
            {"name": "pagina", "type": "integer", "req": False, "desc": "Número da página (default 1)"},
            {"name": "limite", "type": "integer", "req": False, "desc": "Tamanho da página (default 50)"}
        ],
        responses={
            "200": {"description": "Lista recuperada com sucesso", "content": {"application/json": {"example": [{"id": 1, "titulo": "Exemplo", "status": "ativo"}]}}}
        }
    )
    def listar(params):
        if not service:
            return []
        return read_model.get_or_revalidate(
            "modulo1_list",
            lambda: service.listar(
                apenas_ativos=_extrair(params, "apenas_ativos") != "false",
                status=_extrair(params, "status"),
                busca=_extrair(params, "busca"),
                pagina=_extrair(params, "pagina") or 1,
                limite=_extrair(params, "limite") or 50,
            ),
            ttl=30,
        )

    @registry.get(
        "/api/modulo1/metricas",
        summary="Obter métricas e KPIs do módulo modulo1",
        tags=[tag_name],
        description="Retorna indicadores quantitativos agregados para dashboards executivos.",
        responses={
            "200": {"description": "Métricas consolidadas", "content": {"application/json": {"example": {"total": 10, "ativos": 8, "concluidos": 2, "taxa_conclusao": 20.0}}}}
        }
    )
    def metricas(params):
        return service.obter_metricas() if service else {"total": 0, "ativos": 0, "concluidos": 0, "taxa_conclusao": 0.0}

    @registry.get(
        "/api/modulo1/obter",
        summary="Obter item de modulo1 por ID",
        tags=[tag_name],
        description="Retorna os detalhes completos de um registro do módulo modulo1.",
        query_params=[
            {"name": "id", "type": "integer", "req": True, "desc": "ID do registro"}
        ],
        responses={
            "200": {"description": "Registro encontrado", "content": {"application/json": {"example": {"id": 1, "titulo": "Exemplo"}}}},
            "404": {"description": "Registro não encontrado"}
        }
    )
    def obter(params):
        item_id = int(_extrair(params, "id") or 0)
        res = service.obter_por_id(item_id) if service else None
        return res if res else {"sucesso": False, "erro": "Item não encontrado"}

    @registry.post(
        "/api/modulo1/criar",
        summary="Criar novo item no módulo modulo1",
        tags=[tag_name],
        description="Cadastra um novo registro com emissão de evento no EventBus.",
        body_schema=[
            {"name": "titulo", "type": "string", "req": True, "desc": "Título identificador"},
            {"name": "descricao", "type": "string", "req": False, "desc": "Descrição complementar"},
            {"name": "status", "type": "string", "req": False, "desc": "Status inicial (default 'ativo')"},
            {"name": "dados", "type": "object", "req": False, "desc": "Objeto JSON customizado"}
        ],
        body_example={"titulo": "Novo Registro Modulo1", "descricao": "Descrição detalhada", "status": "ativo", "dados": {"prioridade": "alta"}},
        responses={
            "200": {"description": "Item criado com sucesso", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
        }
    )
    def criar(data):
        if not service:
            return {"sucesso": False, "erro": "Serviço indisponível"}
        try:
            return service.criar(
                titulo=(data or {}).get("titulo", ""),
                dados=(data or {}).get("dados", {}),
                descricao=(data or {}).get("descricao", ""),
                status=(data or {}).get("status", "ativo"),
            )
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    @registry.post(
        "/api/modulo1/atualizar",
        summary="Atualizar item do módulo modulo1",
        tags=[tag_name],
        description="Atualiza campos de um registro existente e emite evento de alteração.",
        body_schema=[
            {"name": "id", "type": "integer", "req": True, "desc": "ID do registro a atualizar"},
            {"name": "titulo", "type": "string", "req": False, "desc": "Novo título"},
            {"name": "descricao", "type": "string", "req": False, "desc": "Nova descrição"},
            {"name": "status", "type": "string", "req": False, "desc": "Novo status"},
            {"name": "dados", "type": "object", "req": False, "desc": "Novos dados"}
        ],
        body_example={"id": 1, "titulo": "Modulo1 Atualizado", "status": "concluido"},
        responses={
            "200": {"description": "Item atualizado com sucesso", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
        }
    )
    def atualizar(data):
        if not service:
            return {"sucesso": False, "erro": "Serviço indisponível"}
        item_id = int((data or {}).get("id", 0))
        return service.atualizar(
            item_id=item_id,
            titulo=(data or {}).get("titulo"),
            dados=(data or {}).get("dados"),
            descricao=(data or {}).get("descricao"),
            status=(data or {}).get("status"),
        )

    @registry.post(
        "/api/modulo1/deletar",
        summary="Remover item do módulo modulo1",
        tags=[tag_name],
        description="Remove logicamente um registro e publica evento de exclusão.",
        body_schema=[
            {"name": "id", "type": "integer", "req": True, "desc": "ID do registro a remover"}
        ],
        body_example={"id": 1},
        responses={
            "200": {"description": "Item removido com sucesso", "content": {"application/json": {"example": {"sucesso": True, "id": 1}}}}
        }
    )
    def deletar(data):
        if not service:
            return {"sucesso": False, "erro": "Serviço indisponível"}
        item_id = int((data or {}).get("id", 0))
        return service.deletar(item_id)