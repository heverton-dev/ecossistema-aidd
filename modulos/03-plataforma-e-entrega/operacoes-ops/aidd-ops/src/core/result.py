# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops MVP — PADRÃO RESULTADO MONÁDICO (Result Pattern via returns)
=============================================================================
Mesmo padrão de tools/aidd-master/src/core/result.py baseado na biblioteca
'returns' (dry-python). Elimina exceções soltas e fornece retornos previsíveis
com métodos monádicos completos (map, bind, alt, unwrap, value_or).
=============================================================================
"""

from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union
from returns.result import Result as ReturnsResult, Success, Failure, safe

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T]):
    """Monad Result baseado na biblioteca dry-python 'returns'.

    Combina a interface amigável do Ecossistema AIDD (sucesso, valor, erro, codigo,
    to_dict) com os operadores monádicos formais da lib returns (map, bind, alt,
    unwrap, value_or).
    """

    def __init__(
        self,
        sucesso: bool,
        valor: Optional[T] = None,
        erro: Optional[str] = None,
        codigo: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None,
        _inner: Optional[ReturnsResult[T, Any]] = None,
    ):
        self.sucesso = bool(sucesso)
        self.valor = valor
        self.erro = erro
        self.codigo = codigo or ("SUCESSO" if sucesso else "ERRO_NEGOCIO")
        self.detalhes = detalhes or {}

        if _inner is not None:
            self._inner = _inner
        elif self.sucesso:
            self._inner = Success(valor)
        else:
            self._inner = Failure(erro)

    @classmethod
    def ok(cls, valor: Optional[T] = None, detalhes: Optional[Dict[str, Any]] = None) -> "Result[T]":
        """Gera um resultado de sucesso imutável com motor returns.result.Success."""
        return cls(sucesso=True, valor=valor, codigo="SUCESSO", detalhes=detalhes, _inner=Success(valor))

    @classmethod
    def fail(cls, erro: str, codigo: str = "ERRO_NEGOCIO", detalhes: Optional[Dict[str, Any]] = None) -> "Result[T]":
        """Gera um resultado de falha com motivo e código padronizados via returns.result.Failure."""
        msg = str(erro)
        return cls(sucesso=False, erro=msg, codigo=codigo, detalhes=detalhes, _inner=Failure(msg))

    @classmethod
    def from_returns(
        cls,
        res: ReturnsResult[T, Any],
        codigo: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None,
    ) -> "Result[T]":
        """Converte uma instância nativa de returns.result.Result para Result do ecossistema."""
        if isinstance(res, Success):
            return cls(
                sucesso=True,
                valor=res.unwrap(),
                codigo="SUCESSO",
                detalhes=detalhes,
                _inner=res,
            )
        err_val = res.failure()
        return cls(
            sucesso=False,
            erro=str(err_val),
            codigo=codigo or "ERRO_NEGOCIO",
            detalhes=detalhes,
            _inner=res,
        )

    def to_returns(self) -> ReturnsResult[T, Any]:
        """Retorna o objeto monádico nativo returns.result.Result (Success ou Failure)."""
        return self._inner

    def map(self, function: Callable[[T], Any]) -> "Result[Any]":
        """Monadic map (via returns): aplica function se for sucesso; propaga falha."""
        if not self.sucesso:
            return self
        try:
            mapped_inner = self._inner.map(function)
            return Result(
                sucesso=True,
                valor=mapped_inner.unwrap(),
                codigo=self.codigo,
                detalhes=self.detalhes,
                _inner=mapped_inner,
            )
        except Exception as exc:
            return Result.fail(str(exc), codigo="ERRO_MAP", detalhes=self.detalhes)

    def bind(self, function: Callable[[T], Union["Result[Any]", ReturnsResult[Any, Any]]]) -> "Result[Any]":
        """Monadic bind / flat_map (via returns): encadeia operação se for sucesso."""
        if not self.sucesso:
            return self
        try:
            res = function(self.valor)
            if isinstance(res, Result):
                return res
            if isinstance(res, (Success, Failure)):
                return Result.from_returns(res, detalhes=self.detalhes)
            return Result.ok(res, detalhes=self.detalhes)
        except Exception as exc:
            return Result.fail(str(exc), codigo="ERRO_BIND", detalhes=self.detalhes)

    def alt(self, function: Callable[[Any], Any]) -> "Result[T]":
        """Monadic alt (via returns): aplica function ao erro se for falha."""
        if self.sucesso:
            return self
        try:
            alted_inner = self._inner.alt(function)
            return Result(
                sucesso=False,
                erro=str(alted_inner.failure()),
                codigo=self.codigo,
                detalhes=self.detalhes,
                _inner=alted_inner,
            )
        except Exception as exc:
            return Result.fail(str(exc), codigo="ERRO_ALT", detalhes=self.detalhes)

    def unwrap(self) -> T:
        """Extrai o valor se sucesso, ou levanta UnwrapFailedError se falha."""
        return self._inner.unwrap()

    def value_or(self, default: T) -> T:
        """Retorna o valor se for sucesso, ou o default se for falha."""
        return self._inner.value_or(default)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa o resultado para formato JSON amigável a APIs e MCP."""
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


__all__ = ["Result", "Success", "Failure", "safe", "ReturnsResult"]
