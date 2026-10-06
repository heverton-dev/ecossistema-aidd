# -*- coding: utf-8 -*-
"""
Value Objects do domínio modulo1 — imutáveis e auto-validados.

Regra do DDD tático: objetos de valor não têm identidade própria, são
imutáveis e carregam seus INVARIANTES de negócio no próprio construtor.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


class Titulo:
    """Título de um item do módulo 1.

    Invariantes:
    - Deve ser uma string não vazia após remoção de espaços nas bordas.
    - Limite de ``TAMANHO_MAXIMO`` caracteres.
    """

    TAMANHO_MAXIMO = 200

    __slots__ = ("_valor",)

    def __init__(self, valor: str):
        limpo = (valor or "").strip()
        if not limpo:
            raise ValueError("O título do item é obrigatório")
        if len(limpo) > self.TAMANHO_MAXIMO:
            raise ValueError(
                f"O título deve ter no máximo {self.TAMANHO_MAXIMO} caracteres"
            )
        self._valor = limpo

    @property
    def valor(self) -> str:
        return self._valor

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, Titulo) and self._valor == outro._valor

    def __hash__(self) -> int:
        return hash(self._valor)

    def __repr__(self) -> str:
        return f"Titulo({self._valor!r})"


class StatusModulo1:
    """Status de um item do módulo 1 — enum fechado de estados válidos."""

    ATIVO = "ativo"
    CONCLUIDO = "concluido"
    PAUSADO = "pausado"
    ARQUIVADO = "arquivado"

    VALORES = frozenset({ATIVO, CONCLUIDO, PAUSADO, ARQUIVADO})

    __slots__ = ("_valor",)

    def __init__(self, valor: str = ATIVO):
        normalizado = (valor or "").strip().lower()
        if normalizado not in self.VALORES:
            raise ValueError(
                f"Status '{valor}' não é um status válido para o módulo modulo1"
            )
        self._valor = normalizado

    @property
    def valor(self) -> str:
        return self._valor

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, StatusModulo1) and self._valor == outro._valor

    def __hash__(self) -> int:
        return hash(self._valor)

    def __repr__(self) -> str:
        return f"StatusModulo1({self._valor!r})"


class DadosItem:
    """Blob estruturado de dados complementares do item (imutável por valor).

    Mantém os INVARIANTES de que os dados podem ser ``None`` ou um dicionário,
    e expõe apenas cópias defensivas — nenhum caminho permite mutação externa.
    """

    __slots__ = ("_valor",)

    def __init__(self, dados: Optional[Dict[str, Any]]):
        self._valor: Dict[str, Any] = dict(dados) if dados else {}

    @property
    def valor(self) -> Dict[str, Any]:
        return dict(self._valor)

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, DadosItem) and self._valor == outro._valor

    def __hash__(self) -> int:
        return hash(json.dumps(self._valor, sort_keys=True, ensure_ascii=False))

    def __repr__(self) -> str:
        return f"DadosItem({self._valor!r})"