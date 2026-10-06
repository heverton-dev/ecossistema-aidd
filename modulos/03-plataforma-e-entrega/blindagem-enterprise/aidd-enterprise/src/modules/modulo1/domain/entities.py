# -*- coding: utf-8 -*-
"""
Entidade rica (Agregado) da fatia vertical modulo1.

A regra de RICH DOMAIN MODEL exige que toda mutação passe por métodos de
domínio que:
  1. Validam os INVARIANTES de negócio.
  2. Registram DomainEvents no agregado (fonte única de verdade da mudança).
  3. São a única porta de escrita do estado interno.

A camada de persistência (infrastructure/) apenas persiste/recarrega este
agregado a partir das linhas do banco — não decide regra de negócio nenhuma.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from .events import (
    DomainEvent,
    Modulo1Atualizado,
    Modulo1Criado,
    Modulo1Deletado,
)
from .value_objects import DadosItem, StatusModulo1, Titulo


def _agora_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Modulo1Item:
    """Agregado raiz que representa um item cadastrável do módulo 1."""

    def __init__(
        self,
        *,
        titulo: str,
        descricao: str = "",
        dados: Optional[Dict[str, Any]] = None,
        status: str = StatusModulo1.ATIVO,
        item_id: Optional[int] = None,
        ativo: bool = True,
        criado_em: Optional[str] = None,
        atualizado_em: Optional[str] = None,
        deletado_em: Optional[str] = None,
    ) -> None:
        # Value objects aplicam os invariantes; exceção de domínio (ValueError)
        # propaga para quem chamou a operação.
        self._titulo = titulo if isinstance(titulo, Titulo) else Titulo(titulo)
        self._status = status if isinstance(status, StatusModulo1) else StatusModulo1(status)
        self._descricao = (descricao or "").strip()
        self._dados = dados if isinstance(dados, DadosItem) else DadosItem(dados)
        self._id = item_id
        self._ativo = bool(ativo)
        self._criado_em = criado_em
        self._atualizado_em = atualizado_em
        self._deletado_em = deletado_em
        self._domain_events: List[DomainEvent] = []

    # ------------------------------------------------------------------ #
    # Factories do agregado
    # ------------------------------------------------------------------ #

    @classmethod
    def novo(
        cls,
        titulo: str,
        descricao: str = "",
        dados: Optional[Dict[str, Any]] = None,
        status: str = StatusModulo1.ATIVO,
    ) -> "Modulo1Item":
        """Cria um item novo (ainda sem identidade persistida)."""
        return cls(titulo=titulo, descricao=descricao, dados=dados, status=status)

    @classmethod
    def from_linha(cls, linha: Dict[str, Any]) -> "Modulo1Item":
        """Reconstitui o agregado a partir de uma linha já materializada do banco.

        ``linha["dados"]`` deve chegar como ``dict`` (desserialização do JSON é
        responsabilidade da camada de infraestrutura).
        """
        return cls(
            titulo=linha.get("titulo", ""),
            descricao=linha.get("descricao", "") or "",
            dados=linha.get("dados") or {},
            status=linha.get("status", StatusModulo1.ATIVO),
            item_id=linha.get("id"),
            ativo=bool(linha.get("ativo", 1)),
            criado_em=linha.get("criado_em"),
            atualizado_em=linha.get("atualizado_em"),
            deletado_em=linha.get("deletado_em"),
        )

    # ------------------------------------------------------------------ #
    # Regras de negócio (únicas portas de mutação do agregado)
    # ------------------------------------------------------------------ #

    def confirmar_criacao(self, item_id: int) -> None:
        """Recebe a identidade gerada pela persistência e registra o evento
        de criação — o evento de domínio carrega o ID real do agregado."""
        agora = _agora_iso()
        self._id = item_id
        self._criado_em = agora
        self._atualizado_em = agora
        self._domain_events.append(
            Modulo1Criado(
                item_id=int(item_id),
                payload={
                    "id": item_id,
                    "titulo": self._titulo.valor,
                    "descricao": self._descricao,
                    "status": self._status.valor,
                    "dados": self._dados.valor,
                },
            )
        )

    def aplicar_atualizacao(
        self,
        titulo: Optional[str] = None,
        descricao: Optional[str] = None,
        dados: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> bool:
        """Aplica mudanças nos campos e registra um DomainEvent se algo mudou.

        Valor atual é mantido para os campos não informados (semântica merge,
        igual ao comportamento anterior do serviço).
        """
        alterou = False
        if titulo is not None:
            novo_titulo = titulo if isinstance(titulo, Titulo) else Titulo(titulo)
            if novo_titulo != self._titulo:
                self._titulo = novo_titulo
                alterou = True
        if descricao is not None:
            nova_descricao = (descricao or "").strip()
            if nova_descricao != self._descricao:
                self._descricao = nova_descricao
                alterou = True
        if dados is not None:
            novos_dados = dados if isinstance(dados, DadosItem) else DadosItem(dados)
            if novos_dados != self._dados:
                self._dados = novos_dados
                alterou = True
        if status is not None:
            novo_status = status if isinstance(status, StatusModulo1) else StatusModulo1(status)
            if novo_status != self._status:
                self._status = novo_status
                alterou = True

        if alterou:
            item_id = self._id
            if item_id is None:
                raise ValueError("Item não persistido não pode ser atualizado")
            self._atualizado_em = _agora_iso()
            self._domain_events.append(
                Modulo1Atualizado(
                    item_id=item_id,
                    payload={
                        "id": item_id,
                        "titulo": self._titulo.valor,
                        "descricao": self._descricao,
                        "status": self._status.valor,
                    },
                )
            )
        return alterou

    def deletar(self) -> None:
        """Remove logicamente o item e registra o evento de exclusão."""
        if self._deletado_em is not None:
            return
        item_id = self._id
        if item_id is None:
            raise ValueError("Item não persistido não pode ser deletado")
        agora = _agora_iso()
        self._deletado_em = agora
        self._ativo = False
        self._atualizado_em = agora
        self._domain_events.append(
            Modulo1Deletado(item_id=item_id, payload={"id": item_id})
        )

    # ------------------------------------------------------------------ #
    # Acesso somente-leitura ao estado do agregado
    # ------------------------------------------------------------------ #

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def titulo(self) -> Titulo:
        return self._titulo

    @property
    def descricao(self) -> str:
        return self._descricao

    @property
    def dados(self) -> DadosItem:
        return self._dados

    @property
    def status(self) -> StatusModulo1:
        return self._status

    @property
    def ativo(self) -> bool:
        return self._ativo

    @property
    def criado_em(self) -> Optional[str]:
        return self._criado_em

    @property
    def atualizado_em(self) -> Optional[str]:
        return self._atualizado_em

    @property
    def deletado_em(self) -> Optional[str]:
        return self._deletado_em

    @property
    def domain_events(self) -> List[DomainEvent]:
        return self._domain_events

    def clear_domain_events(self) -> None:
        """Limpa a fila de eventos de domínio após entrega (Outbox + EventBus)."""
        self._domain_events = []

    def __repr__(self) -> str:
        return (
            f"Modulo1Item(id={self._id!r}, titulo={self._titulo.valor!r}, "
            f"status={self._status.valor!r}, ativo={self._ativo!r})"
        )