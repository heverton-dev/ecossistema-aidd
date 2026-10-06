# -*- coding: utf-8 -*-
"""
Casos de uso (Use Cases) da fatia vertical modulo1.

Orquestram regras de aplicação    sem SQL e sem HTTP: montam o agregado a
partir do DTO, chamam o repositório (porta), coletam os Domain Events do
agregado e os publicam no barramento após o commit. Todo retorno é um
``Result[T, E]`` do Shared Kernel — nunca exceção crua para cima.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from core.result import Result

from ..domain.entities import Modulo1Item
from ..domain.events import DomainEvent
from ..domain.repositories import Modulo1Repositorio, PublicadorEventos
from .dtos import (
    AtualizarModulo1DTO,
    CriarModulo1DTO,
    ListarModulo1DTO,
    MetricasModulo1DTO,
    Modulo1DTO,
)


class CriarModulo1UseCase:
    """Cria um novo item do módulo 1."""

    def __init__(self, repositorio: Modulo1Repositorio, publicador: Optional[PublicadorEventos] = None):
        self._repositorio = repositorio
        self._publicador = publicador

    def executar(self, dto: CriarModulo1DTO) -> Result[Modulo1DTO]:
        try:
            item = Modulo1Item.novo(
                titulo=dto.titulo,
                descricao=dto.descricao,
                dados=dto.dados,
                status=dto.status,
            )
        except ValueError as exc:
            return Result.fail(str(exc), codigo="TITULO_OBRIGATORIO")
        item = self._repositorio.adicionar(item)
        self._publicar_eventos(item.domain_events)
        item.clear_domain_events()
        return Result.ok(Modulo1DTO.from_entity(item))

    def _publicar_eventos(self, eventos: Iterable[DomainEvent]) -> None:
        if self._publicador is None:
            return
        for evento in eventos:
            self._publicador.publicar(evento.event_name, evento.to_payload())


class ObterModulo1UseCase:
    """Obtém um item existente pelo ID."""

    def __init__(self, repositorio: Modulo1Repositorio):
        self._repositorio = repositorio

    def executar(self, item_id: int) -> Result[Modulo1DTO]:
        item = self._repositorio.buscar_por_id(item_id)
        if item is None:
            return Result.fail("Item não encontrado", codigo="NAO_ENCONTRADO")
        return Result.ok(Modulo1DTO.from_entity(item))


class ListarModulo1UseCase:
    """Lista itens com filtros e paginação."""

    def __init__(self, repositorio: Modulo1Repositorio):
        self._repositorio = repositorio

    def executar(self, dto: ListarModulo1DTO) -> Result[List[Modulo1DTO]]:
        itens = self._repositorio.listar(
            apenas_ativos=dto.apenas_ativos,
            status=dto.status,
            busca=dto.busca,
            pagina=dto.pagina,
            limite=dto.limite,
        )
        return Result.ok([Modulo1DTO.from_entity(item) for item in itens])


class AtualizarModulo1UseCase:
    """Atualiza (merge) um item existente."""

    def __init__(self, repositorio: Modulo1Repositorio, publicador: Optional[PublicadorEventos] = None):
        self._repositorio = repositorio
        self._publicador = publicador

    def executar(self, dto: AtualizarModulo1DTO) -> Result[Modulo1DTO]:
        item = self._repositorio.buscar_por_id(dto.item_id)
        if item is None:
            return Result.fail("Item não encontrado", codigo="NAO_ENCONTRADO")
        try:
            item.aplicar_atualizacao(
                titulo=dto.titulo,
                descricao=dto.descricao,
                dados=dto.dados,
                status=dto.status,
            )
        except ValueError as exc:
            return Result.fail(str(exc), codigo="INVARIANTE_VIOLADO")
        persistido = self._repositorio.atualizar(item)
        if persistido is None:
            return Result.fail("Item não encontrado", codigo="NAO_ENCONTRADO")
        self._publicar_eventos(item.domain_events)
        item.clear_domain_events()
        return Result.ok(Modulo1DTO.from_entity(item))

    def _publicar_eventos(self, eventos: Iterable[DomainEvent]) -> None:
        if self._publicador is None:
            return
        for evento in eventos:
            self._publicador.publicar(evento.event_name, evento.to_payload())


class DeletarModulo1UseCase:
    """Remove logicamente um item existente."""

    def __init__(self, repositorio: Modulo1Repositorio, publicador: Optional[PublicadorEventos] = None):
        self._repositorio = repositorio
        self._publicador = publicador

    def executar(self, item_id: int) -> Result[int]:
        item = self._repositorio.buscar_por_id(item_id)
        if item is None:
            return Result.fail("Item não encontrado", codigo="NAO_ENCONTRADO")
        item.deletar()
        persistido = self._repositorio.deletar(item)
        if persistido is None:
            return Result.fail("Item não encontrado", codigo="NAO_ENCONTRADO")
        for evento in item.domain_events:
            if self._publicador is not None:
                self._publicador.publicar(evento.event_name, evento.to_payload())
        item.clear_domain_events()
        return Result.ok(item_id)


class ObterMetricasModulo1UseCase:
    """Obtém os KPIs agregados do módulo."""

    def __init__(self, repositorio: Modulo1Repositorio):
        self._repositorio = repositorio

    def executar(self) -> Result[MetricasModulo1DTO]:
        metricas = self._repositorio.obter_metricas()
        dto = MetricasModulo1DTO(
            total=int(metricas.get("total", 0)),
            ativos=int(metricas.get("ativos", 0)),
            concluidos=int(metricas.get("concluidos", 0)),
        )
        return Result.ok(dto)