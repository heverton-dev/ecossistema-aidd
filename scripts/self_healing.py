# -*- coding: utf-8 -*-
"""
Mecanismo Canônico de Self-Healing Determinístico do Ecossistema AIDD.

Implementa estratégias de resiliência sem loops infinitos:
- Retry determinístico com backoff configurável e teto estrito
- Fallback seguro para degradação graciosa
- Integração estrita com a taxonomia de ExitCode (scripts/exit_codes.py)
"""

import time
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

from scripts.exit_codes import ExitCode


class MaxRetriesExceededError(Exception):
    """Exceção levantada quando todas as tentativas determinísticas falham."""
    pass


class SelfHealingPolicy:
    """Política determinística de recuperação e self-healing."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_sec: float = 0.05,
        backoff_factor: float = 2.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts deve ser ao menos 1")
        self.max_attempts = max_attempts
        self.initial_delay_sec = max(0.0, initial_delay_sec)
        self.backoff_factor = max(1.0, backoff_factor)
        self.retryable_exceptions = retryable_exceptions

    def execute_with_retry(
        self,
        operation: Callable[..., Any],
        *args: Any,
        fallback: Optional[Callable[[Exception], Any]] = None,
        **kwargs: Any,
    ) -> Tuple[bool, Any, Optional[Exception], int]:
        """
        Executa operação com retry determinístico e fallback opcional.

        Retorna:
            (success: bool, result: Any, last_error: Optional[Exception], attempts: int)
        """
        last_error: Optional[Exception] = None
        delay = self.initial_delay_sec

        for attempt in range(1, self.max_attempts + 1):
            try:
                result = operation(*args, **kwargs)
                return True, result, None, attempt
            except self.retryable_exceptions as e:
                last_error = e
                if attempt < self.max_attempts:
                    if delay > 0:
                        time.sleep(delay)
                    delay *= self.backoff_factor

        if fallback is not None:
            try:
                fallback_result = fallback(last_error)
                return True, fallback_result, last_error, self.max_attempts
            except Exception as fb_err:
                return False, None, fb_err, self.max_attempts

        return False, None, last_error, self.max_attempts


def run_with_self_healing(
    operation: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    fallback: Optional[Callable[[Exception], Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Função utilitária de alto nível para self-healing determinístico.
    Mapeia o resultado diretamente para a taxonomia de ExitCode do ecossistema.
    """
    policy = SelfHealingPolicy(max_attempts=max_attempts)
    success, result, error, attempts = policy.execute_with_retry(
        operation, *args, fallback=fallback, **kwargs
    )

    if success:
        return {
            "success": True,
            "exit_code": ExitCode.SUCCESS.value,
            "result": result,
            "attempts": attempts,
            "healed": attempts > 1 or (error is not None and fallback is not None),
        }

    return {
        "success": False,
        "exit_code": ExitCode.IO_OR_TIMEOUT.value if isinstance(error, (TimeoutError, OSError)) else ExitCode.INTERNAL_BUG.value,
        "error": str(error) if error else "Operação falhou",
        "attempts": attempts,
        "healed": False,
    }
