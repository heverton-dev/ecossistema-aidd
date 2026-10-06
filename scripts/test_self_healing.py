# -*- coding: utf-8 -*-
"""
Testes unitários determinísticos do mecanismo de self-healing.
"""

from scripts.exit_codes import ExitCode
from scripts.self_healing import SelfHealingPolicy, run_with_self_healing


def test_self_healing_sucesso_imediato():
    policy = SelfHealingPolicy(max_attempts=3, initial_delay_sec=0.0)
    success, result, error, attempts = policy.execute_with_retry(lambda: 42)
    assert success is True
    assert result == 42
    assert error is None
    assert attempts == 1


def test_self_healing_recupera_apos_falha_transitoria():
    contagem = {"chamadas": 0}

    def operacao_transitoria():
        contagem["chamadas"] += 1
        if contagem["chamadas"] < 3:
            raise ConnectionResetError("Falha de rede transitória")
        return "conectado"

    policy = SelfHealingPolicy(max_attempts=4, initial_delay_sec=0.0)
    success, result, error, attempts = policy.execute_with_retry(operacao_transitoria)
    assert success is True
    assert result == "conectado"
    assert error is None
    assert attempts == 3


def test_self_healing_executa_fallback_quando_esgota_tentativas():
    def operacao_quebrada():
        raise TimeoutError("Timeout definitivo")

    policy = SelfHealingPolicy(max_attempts=2, initial_delay_sec=0.0)
    success, result, error, attempts = policy.execute_with_retry(
        operacao_quebrada,
        fallback=lambda err: f"recuperado_via_fallback:{type(err).__name__}",
    )
    assert success is True
    assert result == "recuperado_via_fallback:TimeoutError"
    assert isinstance(error, TimeoutError)
    assert attempts == 2


def test_self_healing_falha_sem_fallback_retorna_erro():
    def operacao_fatal():
        raise RuntimeError("Bug interno irrecuperavel")

    policy = SelfHealingPolicy(max_attempts=2, initial_delay_sec=0.0)
    success, result, error, attempts = policy.execute_with_retry(operacao_fatal)
    assert success is False
    assert result is None
    assert isinstance(error, RuntimeError)
    assert attempts == 2


def test_run_with_self_healing_envelope_json_e_exit_code():
    res_ok = run_with_self_healing(lambda: "ok", max_attempts=2)
    assert res_ok["success"] is True
    assert res_ok["exit_code"] == ExitCode.SUCCESS.value
    assert res_ok["healed"] is False

    def falha_io():
        raise OSError("Disco inacessivel")

    res_io = run_with_self_healing(falha_io, max_attempts=2)
    assert res_io["success"] is False
    assert res_io["exit_code"] == ExitCode.IO_OR_TIMEOUT.value
    assert res_io["healed"] is False
