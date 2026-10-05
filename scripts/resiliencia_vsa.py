# -*- coding: utf-8 -*-
"""
Tratamento de Exceções e Resiliência Operacional (VSA).
Dimensão D11: Tratamento de Exceções e Fallback.
"""

import time
import logging
from typing import Callable, Any, Tuple, Type

logger = logging.getLogger("vsa_resiliencia")


def executar_com_retry(
    operacao: Callable[[], Any],
    max_tentativas: int = 3,
    backoff_inicial: float = 0.05,
    fator_multiplicador: float = 2.0,
    excecoes_permitidas: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    atraso = backoff_inicial
    ultima_excecao = None

    for tentativa in range(1, max_tentativas + 1):
        try:
            return operacao()
        except excecoes_permitidas as e:
            ultima_excecao = e
            logger.warning(
                f"[VSA Resiliência] Tentativa {tentativa}/{max_tentativas} falhou: {e}. "
                f"Aguardando {atraso:.3f}s..."
            )
            if tentativa < max_tentativas:
                time.sleep(atraso)
                atraso *= fator_multiplicador

    logger.error("[VSA Resiliência] Todas as tentativas falharam. Propagando exceção.")
    raise ultima_excecao
