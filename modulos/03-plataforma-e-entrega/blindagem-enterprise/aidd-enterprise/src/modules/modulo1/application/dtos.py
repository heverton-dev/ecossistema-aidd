# -*- coding: utf-8 -*-
"""DTOs tipados da fatia vertical modulo1 (contratos de entrada e saída)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..domain.entities import Modulo1Item
from ..domain.value_objects import StatusModulo1


@dataclass(frozen=True)
class CriarModulo1DTO:
    """Entrada do caso de uso de criação."""

    titulo: str
    descricao: str = ""
    dados: Optional[Dict[str, Any]] = None
    status: str = StatusModulo1.ATIVO


@dataclass(frozen=True)
class AtualizarModulo1DTO:
    """Entrada do caso de uso de atualização (merge: None = manter)."""

    item_id: int
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    dados: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


@dataclass(frozen=True)
class ListarModulo1DTO:
    """Filtros de listagem."""

    apenas_ativos: bool = True
    status: Optional[str] = None
    busca: Optional[str] = None
    pagina: int = 1
    limite: int = 50


@dataclass(frozen=True)
class Modulo1DTO:
    """Saída tipada de um item — conversor para os contratos HTTP legados."""

    id: Optional[int]
    titulo: str
    descricao: str
    dados: Dict[str, Any] = field(default_factory=dict)
    status: str = StatusModulo1.ATIVO
    ativo: bool = True
    criado_em: Optional[str] = None
    atualizado_em: Optional[str] = None
    deletado_em: Optional[str] = None

    @classmethod
    def from_entity(cls, item: Modulo1Item) -> "Modulo1DTO":
        return cls(
            id=item.id,
            titulo=item.titulo.valor,
            descricao=item.descricao,
            dados=item.dados.valor,
            status=item.status.valor,
            ativo=item.ativo,
            criado_em=item.criado_em,
            atualizado_em=item.atualizado_em,
            deletado_em=item.deletado_em,
        )

    def to_raw_dict(self) -> Dict[str, Any]:
        """Formato legado equivalente a ``dict(row)`` de um ``SELECT *``."""
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "dados_json": json.dumps(self.dados, ensure_ascii=False),
            "status": self.status,
            "ativo": 1 if self.ativo else 0,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
            "deletado_em": self.deletado_em,
        }

    def to_payload(self) -> Dict[str, Any]:
        """Payload de criação (com ``dados``), igual ao contrato legado."""
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "status": self.status,
            "dados": self.dados,
        }

    def to_payload_atualizado(self) -> Dict[str, Any]:
        """Payload de atualização (sem ``dados``), igual ao contrato legado."""
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "status": self.status,
        }


@dataclass(frozen=True)
class MetricasModulo1DTO:
    """Saída tipada dos KPIs do módulo."""

    total: int
    ativos: int
    concluidos: int

    @property
    def taxa_conclusao(self) -> float:
        return round((self.concluidos / self.total * 100) if self.total > 0 else 0.0, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "ativos": self.ativos,
            "concluidos": self.concluidos,
            "taxa_conclusao": self.taxa_conclusao,
        }