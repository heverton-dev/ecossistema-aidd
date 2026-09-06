# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops MVP — PADRÃO RESULTADO MONÁDICO (Result Pattern)
=============================================================================
Mesmo padrão de tools/aidd-master/src/core/result.py.
Elimina exceções soltas e fornece retornos previsíveis para as 3 fases do MVP.
"""

from typing import Any, Optional, Dict, Generic, TypeVar

T = TypeVar("T")


class Result(Generic[T]):
    def __init__(
        self,
        sucesso: bool,
        valor: Optional[T] = None,
        erro: Optional[str] = None,
        codigo: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None
    ):
        self.sucesso = bool(sucesso)
        self.valor = valor
        self.erro = erro
        self.codigo = codigo or ("SUCESSO" if sucesso else "ERRO_NEGOCIO")
        self.detalhes = detalhes or {}

    @classmethod
    def ok(cls, valor: Optional[T] = None, detalhes: Optional[Dict[str, Any]] = None) -> "Result[T]":
        """Gera um resultado de sucesso imutável."""
        return cls(sucesso=True, valor=valor, codigo="SUCESSO", detalhes=detalhes)

    @classmethod
    def fail(cls, erro: str, codigo: str = "ERRO_NEGOCIO", detalhes: Optional[Dict[str, Any]] = None) -> "Result[T]":
        """Gera um resultado de falha com motivo e código padronizados."""
        return cls(sucesso=False, erro=str(erro), codigo=codigo, detalhes=detalhes)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa o resultado para formato JSON amigável."""
        res = {
            "sucesso": self.sucesso,
            "codigo": self.codigo
        }
        if self.sucesso:
            res["dados"] = self.valor
        else:
            res["erro"] = self.erro
        if self.detalhes:
            res["detalhes"] = self.detalhes
        return res

    def __repr__(self) -> str:
        if self.sucesso:
            return f"<Result.ok valor={self.valor!r}>"
        return f"<Result.fail erro={self.erro!r} codigo={self.codigo!r}>"
