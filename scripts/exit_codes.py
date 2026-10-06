#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo canônico de Exit Codes semânticos e Saída Estruturada AIDD.

Conforme definido em docs/protocolos/CONVENCAO-EXIT-CODES-DETERMINISTICOS.md.
"""

from enum import IntEnum
import json
import sys
from typing import Any, Dict, Optional


class ExitCode(IntEnum):
    """Taxonomia universal de códigos de saída para scripts determinísticos."""
    SUCCESS = 0
    RULE_VIOLATION = 1
    INVALID_USAGE = 2
    ENVIRONMENT_ERROR = 3
    IO_OR_TIMEOUT = 4
    INTERNAL_BUG = 5


def emit_json(
    status: str,
    exit_code: ExitCode,
    reason_code: str,
    summary: str,
    data: Optional[Dict[str, Any]] = None,
    stream: Optional[Any] = None,
) -> None:
    """Emite o payload canônico formatado em JSON para a stream especificada."""
    payload = {
        "status": status,
        "exit_code": int(exit_code),
        "reason_code": reason_code,
        "summary": summary,
        "data": data or {},
    }
    target_stream = stream or sys.stdout
    target_stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    target_stream.flush()


def exit_success(summary: str, data: Optional[Dict[str, Any]] = None, as_json: bool = False) -> None:
    """Encerra a execução com sucesso (código 0)."""
    if as_json:
        emit_json(
            status="success",
            exit_code=ExitCode.SUCCESS,
            reason_code="SUCCESS",
            summary=summary,
            data=data,
        )
    else:
        print(f"[OK] {summary}")
    sys.exit(ExitCode.SUCCESS)


def exit_rule_violation(
    reason_code: str,
    summary: str,
    data: Optional[Dict[str, Any]] = None,
    as_json: bool = False,
) -> None:
    """Encerra com violação de regra ou quality gate (código 1)."""
    if as_json:
        emit_json(
            status="failure",
            exit_code=ExitCode.RULE_VIOLATION,
            reason_code=reason_code,
            summary=summary,
            data=data,
        )
    else:
        sys.stderr.write(f"[FALHA] [{reason_code}] {summary}\n")
    sys.exit(ExitCode.RULE_VIOLATION)


def exit_invalid_usage(
    summary: str,
    data: Optional[Dict[str, Any]] = None,
    as_json: bool = False,
) -> None:
    """Encerra com erro de uso ou argumentos da CLI (código 2)."""
    if as_json:
        emit_json(
            status="error",
            exit_code=ExitCode.INVALID_USAGE,
            reason_code="INVALID_USAGE",
            summary=summary,
            data=data,
        )
    else:
        sys.stderr.write(f"[USO INVÁLIDO] {summary}\n")
    sys.exit(ExitCode.INVALID_USAGE)


def exit_env_error(
    reason_code: str,
    summary: str,
    data: Optional[Dict[str, Any]] = None,
    as_json: bool = False,
) -> None:
    """Encerra com erro de ambiente ou dependência ausente (código 3)."""
    if as_json:
        emit_json(
            status="error",
            exit_code=ExitCode.ENVIRONMENT_ERROR,
            reason_code=reason_code,
            summary=summary,
            data=data,
        )
    else:
        sys.stderr.write(f"[ERRO DE AMBIENTE] [{reason_code}] {summary}\n")
    sys.exit(ExitCode.ENVIRONMENT_ERROR)


def exit_io_or_timeout(
    reason_code: str,
    summary: str,
    data: Optional[Dict[str, Any]] = None,
    as_json: bool = False,
) -> None:
    """Encerra com erro de E/S ou timeout (código 4)."""
    if as_json:
        emit_json(
            status="error",
            exit_code=ExitCode.IO_OR_TIMEOUT,
            reason_code=reason_code,
            summary=summary,
            data=data,
        )
    else:
        sys.stderr.write(f"[ERRO I/O OU TIMEOUT] [{reason_code}] {summary}\n")
    sys.exit(ExitCode.IO_OR_TIMEOUT)


def exit_internal_bug(
    reason_code: str,
    summary: str,
    data: Optional[Dict[str, Any]] = None,
    as_json: bool = False,
) -> None:
    """Encerra com falha interna inesperada (código 5)."""
    if as_json:
        emit_json(
            status="error",
            exit_code=ExitCode.INTERNAL_BUG,
            reason_code=reason_code,
            summary=summary,
            data=data,
        )
    else:
        sys.stderr.write(f"[BUG INTERNO] [{reason_code}] {summary}\n")
    sys.exit(ExitCode.INTERNAL_BUG)

