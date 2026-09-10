# -*- coding: utf-8 -*-
"""
Ports (interfaces) do domínio modulo1.

Protocolos PYTHON PURAMENTE ABSTRATOS: definem o CONTRATO que a camada de
aplicação consome e que a infraestrutura implementa (Dependency Inversion).
NENHUMA dependência de infraestrutura, SQLite, HTTP ou Core é permitida aqui.
"""

from __future__ import annotations

from typing import Any, List, Optional, Protocol, runtime_checkable

from .entities import Modulo1Item
from .events import DomainEvent


@runtime_checkable
class Modulo1Repositorio(Protocol):
    """Contrato de persistência do agregado modulo1 (porta de saída)."""

    def adicionar(self, item: Modulo1Item) -> Modulo1Item:
        """Persiste um item novo e devolve o agregado com identidade atribuída."""
        ...

    def buscar_por_id(self, item_id: int) -> Optional[Modulo1Item]:
        """Recupera um item não deletado pelo ID, ou ``None``."""
        ...

    def listar(
        self,
        apenas_ativos: bool = True,
        status: Optional[str] = None,
        busca: Optional[str] = None,
        pagina: int = 1,
        limite: int = 50,
    ) -> List[Modulo1Item]:
        """Lista itens não deletados com filtros, ordenação e paginação."""
        ...

    def atualizar(self, item: Modulo1Item) -> Optional[Modulo1Item]:
        """Persiste mudanças de um item existente (None se não encontrado)."""
        ...

    def deletar(self, item: Modulo1Item) -> Optional[Modulo1Item]:
        """Aplica o soft delete persistido de um item (None se não encontrado)."""
        ...

    def obter_metricas(self) -> dict:
        """Agrega KPIs quantitativos do módulo."""
        ...


@runtime_checkable
class RegistradorOutbox(Protocol):
    """Porta do padrão Transactional Outbox — escrita DENTRO da transação."""

    def registrar(self, conn: Any, evento: DomainEvent) -> str:
        """Grava o evento de domínio na fila de saída da MESMA transação."""
        ...


@runtime_checkable
class PublicadorEventos(Protocol):
    """Porta de publicação de eventos no barramento (após o commit)."""

    def publicar(self, event_name: str, payload: dict) -> None:
        """Publica o evento no EventBus do Shared Kernel."""
        ...