"""Circuit breaker and process-interruption primitives for ORCA ADE.

Two-level safety net: absolute execution timeout + idle-heartbeat
timeout. Process kill is cross-platform (Windows taskkill / Unix SIGKILL).

Spec:
  - docs/features/orquestracao-orca-ade/12-circuit-breaker-e-timeouts-de-seguranca.md

Zero LLM cost — pure OS-level mechanics.
"""

from __future__ import annotations

import os
import platform
import signal
import subprocess
from dataclasses import dataclass
from enum import Enum


class HealthStatus(str, Enum):
    """Result of a circuit-breaker health evaluation."""

    OK = "OK"
    TIMEOUT_TOTAL = "TIMEOUT_TOTAL"
    TIMEOUT_IDLE = "TIMEOUT_IDLE"


@dataclass
class CircuitBreakerConfig:
    """Declarative limits for the circuit breaker.

    Defaults match the canonical values from the spec.
    """

    max_execution_time_seconds: float = 1800.0  # 30 min
    idle_heartbeat_seconds: float = 300.0  # 5 min


def avaliar_saude(
    start_time: float,
    last_activity_time: float,
    current_time: float,
    config: CircuitBreakerConfig | None = None,
) -> HealthStatus:
    """Evaluate whether a running process is healthy.

    Priority: total timeout is checked *first* — if exceeded, the
    process is killed regardless of recent activity.
    """
    if config is None:
        config = CircuitBreakerConfig()

    elapsed_total = current_time - start_time
    if elapsed_total > config.max_execution_time_seconds:
        return HealthStatus.TIMEOUT_TOTAL

    elapsed_idle = current_time - last_activity_time
    if elapsed_idle > config.idle_heartbeat_seconds:
        return HealthStatus.TIMEOUT_IDLE

    return HealthStatus.OK


def interromper_processo(pid: int) -> bool:
    """Terminate a process by PID at the OS level.

    Returns True on clean termination (or if the process was already gone).
    Returns False only if the kill call itself failed unexpectedly.

    Windows: ``taskkill /F /T /PID <pid>``
    Unix:    ``os.kill(pid, SIGKILL)``
    """
    try:
        if platform.system() == "Windows":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                check=False,
            )
        else:
            os.kill(pid, signal.SIGKILL)
        return True
    except (ProcessLookupError, OSError):
        # Process already dead or inaccessible — treat as clean.
        return True
    except Exception:
        return False
