# -*- coding: utf-8 -*-
"""
Módulo de Fallback e Resiliência Operacional para aidd-tdd (D11 / DoD 4).
Implementa detecção prévia de runners no ambiente e Circuit Breaker para evitar loops infinitos.
"""

from __future__ import annotations

import shutil
import sys
from typing import Optional


class CircuitBreakerError(RuntimeError):
    """Lançada quando o limite de tentativas consecutivas sem transição é excedido."""
    pass


def verificar_runner_instalado(runner: str) -> bool:
    """Verifica se o executável do runner existe no PATH do sistema operacional."""
    return shutil.which(runner) is not None


class CircuitBreakerTdd:
    """Monitor de tentativas consecutivas para proteger contra gasto infinito de tokens."""

    def __init__(self, max_tentativas: int = 5):
        self.max_tentativas = max_tentativas
        self.tentativas = 0

    def registrar_tentativa(self) -> int:
        if self.atingiu_limite():
            raise CircuitBreakerError(
                f"[CIRCUIT BREAKER TDD] Limite de {self.max_tentativas} tentativas consecutivas excedido. Abortando execução para evitar loop infinito."
            )
        self.tentativas += 1
        return self.tentativas

    def atingiu_limite(self) -> bool:
        return self.tentativas >= self.max_tentativas

    def resetar(self) -> None:
        self.tentativas = 0
