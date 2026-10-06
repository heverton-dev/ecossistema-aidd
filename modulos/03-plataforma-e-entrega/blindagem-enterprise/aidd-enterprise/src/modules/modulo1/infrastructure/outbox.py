# -*- coding: utf-8 -*-
"""
Adapters de infraestrutura de EVENTOS e CQRS da fatia vertical modulo1.

- ``OutboxSqliteAdapter``: persiste Domain Events na tabela ``_outbox_events``
  (Transactional Outbox) + trilha WORM ``_audit_log``, sempre na MESMA
  transação da mutação — garante at-least-once mesmo se o processo cair.
- ``EventBusPublisher``: publica os mesmos Domain Events no EventBus do
  Shared Kernel após o commit (reação assíncrona em memória/distribuída).
- ``ReadModelInvalidator``: adapter CQRS — invalida o read-model cache a cada
  evento de mutação do agregado, disparado por Domain Event.
"""

from __future__ import annotations

from typing import Any

from core.cqrs import read_model
from core.database import append_audit_log

from ..domain.events import DomainEvent
from ..domain.repositories import PublicadorEventos, RegistradorOutbox


class OutboxSqliteAdapter(RegistradorOutbox):
    """Grava Domain Events no outbox transacional + audit log WORM."""

    def __init__(self, db: Any):
        self._db = db

    def registrar(self, conn: Any, evento: DomainEvent) -> str:
        payload = evento.to_payload()
        evento_id = self._db.enqueue_outbox_event(conn, evento.event_name, payload)
        append_audit_log(conn.cursor(), evento.event_name, payload)
        return evento_id


class EventBusPublisher(PublicadorEventos):
    """Publica Domain Events no EventBus do Shared Kernel após o commit."""

    def __init__(self, events: Any):
        self._events = events

    def publicar(self, event_name: str, payload: dict) -> None:
        if self._events is not None:
            self._events.emit(event_name, payload)


class ReadModelInvalidator:
    """Adapter CQRS: invalida o cache de leitura quando o agregado muda.

    Assina os event_name do domínio no EventBus e, para qualquer mutação,
    invalida o prefixo ``modulo1_`` e a chave da listagem ``modulo1_list``.
    """

    EVENTOS_MUTACAO = ("modulo1_criado", "modulo1_atualizado", "modulo1_deletado")

    def __init__(self, events: Any):
        self._events = events

    def registrar(self) -> "ReadModelInvalidator":
        if self._events is None:
            return self
        for nome in self.EVENTOS_MUTACAO:
            try:
                self._events.on(nome, self._invalidar)
            except (AttributeError, TypeError):
                # Barramentos mínimos podem não expor assinatura; segue sem cache.
                return self
        return self

    @staticmethod
    def _invalidar(payload: dict) -> None:
        read_model.invalidate_prefix("modulo1_")
        read_model.invalidate("modulo1_list")