# -*- coding: utf-8 -*-
"""
Fallback e resiliencia operacional de aidd-enterprise (D11).

- Classificacao de falhas transientes (IO de permissao, travamento de lock)
  com retry e backoff exponencial deterministico.
- Captura graceful de falhas fatais em relatorio diagnostico estruturado,
  gravado atomicamente (tmp + replace) sem corromper o workspace.
- Nenhum erro de injecao derruba o processo com traceback: sempre exit 0/1.
"""

from __future__ import annotations

import errno
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union

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
_RELATORIO_DIAGNOSTICO = "ENTERPRISE-DIAGNOSTICO.json"

PathLike = Union[str, Path]


class ResilienciaEsgotadaError(RuntimeError):
    """Todas as tentativas transientes foram esgotadas sem sucesso."""

    def __init__(self, mensagem: str, registro: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(mensagem)
        self.registro: Dict[str, Any] = dict(registro or {})
        self.tentativas: int = int(self.registro.get("tentativas", 0))


def eh_transiente(erro: BaseException) -> bool:
    """Classifica falhas transientes: permissao de IO e travamento de lock."""
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
                    f"esgotadas {tentativas} tentativas transientes: {registro}", registro
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


def _causa_raiz(erro: BaseException) -> BaseException:
    """Sobe a cadeia de causas ate a falha raiz (ex.: ResilienciaEsgotadaError)."""
    atual = erro
    while atual.__cause__ is not None and atual.__cause__ is not atual:
        atual = atual.__cause__
    return atual


def gerar_relatorio_diagnostico(
    erro: BaseException,
    *,
    tentativas: int,
    contexto: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Formata a falha fatal em relatorio diagnostico estruturado e legivel."""
    raiz = _causa_raiz(erro)
    return {
        "tipo": type(erro).__name__,
        "mensagem": str(raiz) or type(raiz).__name__,
        "transiente": eh_transiente(raiz) or eh_transiente(erro),
        "tentativas": int(tentativas),
        "contexto": dict(contexto or {}),
        "captura": type(raiz).__name__,
    }


def persistir_diagnostico(pasta: PathLike, registro: Dict[str, Any]) -> Path:
    """Grava o relatorio atomicamente (tmp + replace); nunca deixa JSON parcial."""
    caminho = Path(pasta) / _RELATORIO_DIAGNOSTICO
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(caminho.suffix + ".tmp")
    tmp.write_text(json.dumps(registro, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, caminho)
    return caminho


def executar_com_fallback(
    operacao: Callable[[], T],
    pasta: PathLike,
    *,
    tentativas: int = 3,
    backoff_base: float = 0.1,
    fator: float = 2.0,
    esperar: Callable[[float], None] = time.sleep,
    contexto: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Envolve uma operacao de injecao com retry e captura graceful de falha fatal.
    Retorna 0 em sucesso; 1 com relatorio diagnostico gravado em qualquer falha
    (sem traceback, sem corromper o workspace).
    """
    try:
        com_retry(
            operacao,
            tentativas=tentativas,
            backoff_base=backoff_base,
            fator=fator,
            esperar=esperar,
            contexto=contexto,
        )
        return 0
    except ResilienciaEsgotadaError as exc:
        registro = gerar_relatorio_diagnostico(exc, tentativas=exc.tentativas or tentativas, contexto=contexto)
    except BaseException as exc:  # captura graceful: nunca propaga abruptamente
        registro = gerar_relatorio_diagnostico(exc, tentativas=1, contexto=contexto)

    try:
        caminho = persistir_diagnostico(pasta, registro)
    except OSError as exc:
        print(f"[aidd-enterprise][fallback] falha ao gravar diagnostico: {exc}", file=sys.stderr)
        return 1
    print(
        f"[aidd-enterprise][fallback] falha capturada ({registro['tipo']}): "
        f"{registro['mensagem']} -> {caminho}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    print("Uso: fallback.executar_com_fallback(operacao, pasta, ...)", file=sys.stderr)
    sys.exit(1)
