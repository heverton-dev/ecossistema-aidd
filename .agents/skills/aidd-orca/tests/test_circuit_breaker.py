"""Unit tests for circuit_breaker.py — health evaluation and process kill."""

from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest

from scripts.circuit_breaker import (
    CircuitBreakerConfig,
    HealthStatus,
    avaliar_saude,
    interromper_processo,
)


# ---------------------------------------------------------------------------
# avaliar_saude
# ---------------------------------------------------------------------------

class TestAvaliarSaude:
    def test_ok_within_limits(self):
        result = avaliar_saude(
            start_time=0.0,
            last_activity_time=100.0,
            current_time=200.0,
            config=CircuitBreakerConfig(max_execution_time_seconds=1800, idle_heartbeat_seconds=300),
        )
        assert result == HealthStatus.OK

    def test_total_timeout(self):
        result = avaliar_saude(
            start_time=0.0,
            last_activity_time=1790.0,
            current_time=1801.0,
            config=CircuitBreakerConfig(max_execution_time_seconds=1800, idle_heartbeat_seconds=300),
        )
        assert result == HealthStatus.TIMEOUT_TOTAL

    def test_idle_timeout(self):
        result = avaliar_saude(
            start_time=0.0,
            last_activity_time=500.0,
            current_time=801.0,
            config=CircuitBreakerConfig(max_execution_time_seconds=1800, idle_heartbeat_seconds=300),
        )
        assert result == HealthStatus.TIMEOUT_IDLE

    def test_total_timeout_priority_over_idle(self):
        """Total timeout should win even if idle would also trigger."""
        result = avaliar_saude(
            start_time=0.0,
            last_activity_time=0.0,
            current_time=2000.0,
            config=CircuitBreakerConfig(max_execution_time_seconds=1800, idle_heartbeat_seconds=300),
        )
        assert result == HealthStatus.TIMEOUT_TOTAL

    def test_default_config(self):
        result = avaliar_saude(start_time=0.0, last_activity_time=0.0, current_time=1.0)
        assert result == HealthStatus.OK

    def test_custom_config(self):
        cfg = CircuitBreakerConfig(max_execution_time_seconds=10, idle_heartbeat_seconds=5)
        assert avaliar_saude(0, 0, 6, cfg) == HealthStatus.TIMEOUT_IDLE
        assert avaliar_saude(0, 0, 11, cfg) == HealthStatus.TIMEOUT_TOTAL
        assert avaliar_saude(0, 8, 11, cfg) == HealthStatus.TIMEOUT_TOTAL


# ---------------------------------------------------------------------------
# interromper_processo
# ---------------------------------------------------------------------------

class TestInterromperProcesso:
    def test_kill_nonexistent_pid_returns_true(self):
        # PID 0 is invalid on most OSes; ProcessLookupError → True
        result = interromper_processo(0)
        assert result is True

    def test_kill_real_subprocess(self):
        # Spawn a short-lived process and kill it
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pid = proc.pid
        result = interromper_processo(pid)
        assert result is True
        # Confirm it's dead via subprocess.wait (cross-platform reliable)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
        assert proc.poll() is not None
