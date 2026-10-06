# -*- coding: utf-8 -*-
"""
Application Service / composition root da fatia vertical modulo1.

Este módulo é a FRONTEIRA entre a aplicação (use cases DDD) e o mundo
externo (server.py / testes): monta o repositório SQLite, os adapters de
Outbox/EventBus/CQRS e os casos de uso. Contém ZERO SQL e ZERO regra de
negócio — apenas orquestração e tradução Result -> contratos legados.

O nome ``Modulo1Service`` e as assinaturas ``criar/atualizar/deletar/...``
são preservados para compatibilidade total com server.py e testes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .application.dtos import (
    AtualizarModulo1DTO,
    CriarModulo1DTO,
    ListarModulo1DTO,
)
from .application.use_cases import (
    AtualizarModulo1UseCase,
    CriarModulo1UseCase,
    DeletarModulo1UseCase,
    ListarModulo1UseCase,
    ObterModulo1UseCase,
    ObterMetricasModulo1UseCase,
)
from .infrastructure.outbox import (
    EventBusPublisher,
    OutboxSqliteAdapter,
    ReadModelInvalidator,
)
from .infrastructure.sqlite_repository import SqliteModulo1Repository


class Modulo1Service:
    """Composition root do módulo modulo1 (Clean Architecture)."""

    def __init__(self, db: Any, events=None):
        self._db = db
        outbox = OutboxSqliteAdapter(db)
        repositorio = SqliteModulo1Repository(db, outbox)
        publicador = EventBusPublisher(events)

        self._criar = CriarModulo1UseCase(repositorio, publicador)
        self._obter = ObterModulo1UseCase(repositorio)
        self._listar = ListarModulo1UseCase(repositorio)
        self._atualizar = AtualizarModulo1UseCase(repositorio, publicador)
        self._deletar = DeletarModulo1UseCase(repositorio, publicador)
        self._metricas = ObterMetricasModulo1UseCase(repositorio)

        # CQRS: invalidaçao do read-model cache dirigida por Domain Events.
        ReadModelInvalidator(events).registrar()

    # ------------------------------------------------------------------ #
    # Contratos legados (mesma superfície do antigo services.py)
    # ------------------------------------------------------------------ #

    def listar(
        self,
        apenas_ativos: bool = True,
        status: Optional[str] = None,
        busca: Optional[str] = None,
        pagina: int = 1,
        limite: int = 50,
    ) -> List[Dict[str, Any]]:
        dto = ListarModulo1DTO(
            apenas_ativos=apenas_ativos,
            status=status,
            busca=busca,
            pagina=pagina,
            limite=limite,
        )
        resultado = self._listar.executar(dto)
        if not resultado.sucesso:
            return []
        assert resultado.valor is not None
        return [item.to_raw_dict() for item in resultado.valor]

    def obter_metricas(self) -> Dict[str, Any]:
        resultado = self._metricas.executar()
        if not resultado.sucesso:
            return {"total": 0, "ativos": 0, "concluidos": 0, "taxa_conclusao": 0.0}
        assert resultado.valor is not None
        return resultado.valor.to_dict()

    def obter_por_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        resultado = self._obter.executar(item_id)
        if not resultado.sucesso:
            return None
        assert resultado.valor is not None
        return resultado.valor.to_raw_dict()

    def criar(
        self,
        titulo: str,
        dados: Optional[Dict[str, Any]] = None,
        descricao: str = "",
        status: str = "ativo",
    ) -> Dict[str, Any]:
        dto = CriarModulo1DTO(
            titulo=titulo,
            descricao=descricao,
            dados=dados,
            status=status,
        )
        resultado = self._criar.executar(dto)
        if not resultado.sucesso:
            raise ValueError(resultado.erro or "Não foi possível criar o item")
        assert resultado.valor is not None
        return {
            "sucesso": True,
            "id": resultado.valor.id,
            "item": resultado.valor.to_payload(),
        }

    def atualizar(
        self,
        item_id: int,
        titulo: Optional[str] = None,
        dados: Optional[Dict[str, Any]] = None,
        descricao: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        dto = AtualizarModulo1DTO(
            item_id=item_id,
            titulo=titulo,
            descricao=descricao,
            dados=dados,
            status=status,
        )
        resultado = self._atualizar.executar(dto)
        if not resultado.sucesso:
            return {"sucesso": False, "erro": resultado.erro or "Erro ao atualizar"}
        assert resultado.valor is not None
        return {
            "sucesso": True,
            "id": item_id,
            "item": resultado.valor.to_payload_atualizado(),
        }

    def deletar(self, item_id: int) -> Dict[str, Any]:
        resultado = self._deletar.executar(item_id)
        if not resultado.sucesso:
            return {"sucesso": False, "erro": resultado.erro or "Erro ao deletar"}
        return {"sucesso": True, "id": item_id}