# -*- coding: utf-8 -*-
"""
Resiliencia operacional de aidd-forge (D11 / DoD 4).

Retry com backoff exponencial para falhas transientes (IO de permissao,
travamento de git lock) e tratamento estruturado de falhas persistido em
JSONL para auditoria.
"""

from __future__ import annotations

import errno
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

T = TypeVar("T")

_ERRNOS_TRANSIENTES = frozenset(
    {
        errno.EACCES,
        errno.EPERM,
        errno.EBUSY,
        errno.ETIMEDOUT,
        errno.EAGAIN,
    }
)
_EBUSY_WINDOWS = 32  # errno-win32 EBUSY (nao existe no modulo errno do POSIX)
_ARQUIVO_FALHAS = "FORGE-FALHAS.jsonl"

PathLike = Union[str, Path]


class ResilienciaEsgotadaError(RuntimeError):
    """Todas as tentativas transientes foram esgotadas sem sucesso."""


def eh_transiente(erro: BaseException) -> bool:
    """Classifica falhas transientes: permissao de IO e travamento de git lock."""
    if isinstance(erro, PermissionError):
        return True
    if isinstance(erro, OSError):
        if getattr(erro, "errno", None) in _ERRNOS_TRANSIENTES or getattr(erro, "errno", None) == _EBUSY_WINDOWS:
            return True
        mensagem = str(erro).lower()
        if "index.lock" in mensagem or "resource temporarily unavailable" in mensagem:
            return True
    return False


def backoff_exponencial(tentativa: int, base: float, fator: float) -> float:
    """Espera deterministica: base * fator ** (tentativa - 1)."""
    if tentativa < 1:
        raise ValueError("tentativa deve ser >= 1")
    return base * (fator ** (tentativa - 1))


def com_retry(
    operacao: Callable[[], T],
    *,
    tentativas: int = 3,
    backoff_base: float = 0.1,
    fator: float = 2.0,
    esperar: Callable[[float], None] = time.sleep,
    contexto: Optional[Dict[str, Any]] = None,
) -> T:
    """
    Executa `operacao` com backoff exponencial. Erros transientes sao
    retentados; nao transientes propagam imediatamente; esgotado o limite,
    lanca ResilienciaEsgotadaError com o registro estruturado da falha.
    """
    if tentativas < 1:
        raise ValueError("tentativas deve ser >= 1")

    ultimo_erro: Optional[BaseException] = None
    for tentativa in range(1, tentativas + 1):
        try:
            return operacao()
        except BaseException as exc:
            if not eh_transiente(exc):
                raise
            ultimo_erro = exc
            if tentativa == tentativas:
                registro = registrar_falha(exc, tentativas=tentativa, contexto=contexto or {})
                raise ResilienciaEsgotadaError(
                    f"esgotadas {tentativas} tentativas transientes: {registro}"
                ) from exc
            esperar(backoff_exponencial(tentativa, backoff_base, fator))

    raise ResilienciaEsgotadaError(f"esgotadas {tentativas} tentativas: {ultimo_erro!r}")


def registrar_falha(
    erro: BaseException,
    *,
    tentativas: int,
    contexto: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Gera o registro estruturado (deterministico) de uma falha tratada."""
    return {
        "tipo": type(erro).__name__,
        "mensagem": str(erro),
        "transiente": eh_transiente(erro),
        "tentativas": int(tentativas),
        "contexto": dict(contexto or {}),
    }


def persistir_falha(pasta: PathLike, registro: Dict[str, Any]) -> Path:
    """Persiste o registro estruturado em JSONL (Lei #3: persistencia em arquivo)."""
    caminho = Path(pasta) / _ARQUIVO_FALHAS
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(registro, sort_keys=True, ensure_ascii=False) + "\n")
    return caminho
