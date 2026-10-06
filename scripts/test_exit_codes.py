#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes determinísticos para scripts/exit_codes.py (prova que morde)."""

import io
import json
import pytest
from scripts.exit_codes import (
    ExitCode,
    emit_json,
    exit_success,
    exit_rule_violation,
    exit_invalid_usage,
    exit_env_error,
    exit_io_or_timeout,
    exit_internal_bug,
)


def test_exit_codes_valores_canonicos():
    """Valida que os códigos de saída preservam os números exatos."""
    assert ExitCode.SUCCESS == 0
    assert ExitCode.RULE_VIOLATION == 1
    assert ExitCode.INVALID_USAGE == 2
    assert ExitCode.ENVIRONMENT_ERROR == 3
    assert ExitCode.IO_OR_TIMEOUT == 4
    assert ExitCode.INTERNAL_BUG == 5


def test_emit_json_estrutura_valida():
    """Valida que emit_json gera o envelope canônico sem caracteres espúrios."""
    buffer = io.StringIO()
    emit_json(
        status="failure",
        exit_code=ExitCode.RULE_VIOLATION,
        reason_code="PORTAO_BLOQUEADO",
        summary="Regra X violada no arquivo Y",
        data={"arquivo": "teste.py"},
        stream=buffer,
    )
    conteudo = buffer.getvalue()
    parsed = json.loads(conteudo)
    assert parsed["status"] == "failure"
    assert parsed["exit_code"] == 1
    assert parsed["reason_code"] == "PORTAO_BLOQUEADO"
    assert parsed["summary"] == "Regra X violada no arquivo Y"
    assert parsed["data"]["arquivo"] == "teste.py"


def test_exit_success_termina_com_codigo_0():
    """Valida encerramento determinístico com código 0."""
    with pytest.raises(SystemExit) as exc:
        exit_success("Tudo certo")
    assert exc.value.code == ExitCode.SUCCESS


def test_exit_rule_violation_morde_com_codigo_1():
    """Valida encerramento determinístico com código 1 (bloqueio)."""
    with pytest.raises(SystemExit) as exc:
        exit_rule_violation("REGRA_VIOLADA", "Falha de validação")
    assert exc.value.code == ExitCode.RULE_VIOLATION


def test_exit_invalid_usage_morde_com_codigo_2():
    """Valida encerramento determinístico com código 2."""
    with pytest.raises(SystemExit) as exc:
        exit_invalid_usage("Falta o argumento --tipo")
    assert exc.value.code == ExitCode.INVALID_USAGE


def test_exit_env_error_morde_com_codigo_3():
    """Valida encerramento determinístico com código 3."""
    with pytest.raises(SystemExit) as exc:
        exit_env_error("DEPENDENCY_MISSING", "Falta instalar ferramenta X")
    assert exc.value.code == ExitCode.ENVIRONMENT_ERROR


def test_exit_io_or_timeout_morde_com_codigo_4():
    """Valida encerramento determinístico com código 4."""
    with pytest.raises(SystemExit) as exc:
        exit_io_or_timeout("NETWORK_TIMEOUT", "Conexão expirou")
    assert exc.value.code == ExitCode.IO_OR_TIMEOUT


def test_exit_internal_bug_morde_com_codigo_5():
    """Valida encerramento determinístico com código 5."""
    with pytest.raises(SystemExit) as exc:
        exit_internal_bug("UNHANDLED_CRASH", "Exceção inesperada")
    assert exc.value.code == ExitCode.INTERNAL_BUG

