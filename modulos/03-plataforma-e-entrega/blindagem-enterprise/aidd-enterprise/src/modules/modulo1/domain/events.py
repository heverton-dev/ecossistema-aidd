# -*- coding: utf-8 -*-
"""
Domain Events da fatia vertical modulo1.

Eventos de domínio são FATOS que ocorreram dentro do agregado. A
infraestrutura persiste estes eventos via Transactional Outbox na MESMA
transação da mutação (at-least-once) e, após o commit, o mesmo evento é
publicado no EventBus do Shared Kernel para reação assíncrona.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DomainEvent:
    """Base imutável de um evento de domínio do agregado modulo1."""

    event_name: str = "domain_event"
    item_id: Optional[int] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        corpo = dict(self.payload)
        corpo.setdefault("id", self.item_id)
        return corpo


@dataclass(frozen=True)
class Modulo1Criado(DomainEvent):
    """Fato: um novo item do módulo 1 foi criado."""

    event_name: str = "modulo1_criado"


@dataclass(frozen=True)
class Modulo1Atualizado(DomainEvent):
    """Fato: um item existente do módulo 1 teve campos alterados."""

    event_name: str = "modulo1_atualizado"


@dataclass(frozen=True)
class Modulo1Deletado(DomainEvent):
    """Fato: um item existente do módulo 1 foi removido (soft delete)."""

    event_name: str = "modulo1_deletado"