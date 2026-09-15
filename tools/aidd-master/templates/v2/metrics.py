# -*- coding: utf-8 -*-
"""
AIDD v6.1 — Metrics Module (prometheus_client with NIH fallback)
================================================================
Tenta usar prometheus_client (se instalado) para exposition format
battle-tested. Caso nao esteja disponivel, usa a implementacao propria
minimal (Counter, Histogram, MetricsRegistry) preservando Zero Fricção.

Beneficio: elimina ~100 linhas de NIH quando prometheus_client esta
disponivel, mantendo compatibilidade total com scrapers Prometheus.
"""

import time
import threading
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Tenta importar prometheus_client (dependencia opcional)
# ---------------------------------------------------------------------------
try:
    from prometheus_client import (
        Counter as _PromCounter,
        Histogram as _PromHistogram,
        CollectorRegistry as _CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    HAS_PROMETHEUS_CLIENT = True
except ImportError:
    HAS_PROMETHEUS_CLIENT = False


if HAS_PROMETHEUS_CLIENT:
    # -----------------------------------------------------------------------
    # Fast path: prometheus_client esta disponivel — delega para ele
    #
    # Cada metrica usa um CollectorRegistry proprio (nao o global REGISTRY)
    # para que render() retorne SOMENTE os dados daquela metrica, sem vazar
    # metricas default do Python (gc, platform, etc.) no output.
    # -----------------------------------------------------------------------
    class Counter:
        def __init__(self, name: str, help_text: str, label_names: Optional[List[str]] = None):
            self._registry = _CollectorRegistry()
            self._inner = _PromCounter(name, help_text, label_names or [], registry=self._registry)

        def inc(self, labels: Optional[Dict[str, str]] = None, amount: float = 1):
            if labels:
                self._inner.labels(**labels).inc(amount)
            else:
                self._inner.inc(amount)

        def render(self) -> str:
            return generate_latest(self._registry).decode("utf-8")

    class Histogram:
        def __init__(self, name: str, help_text: str, buckets: Optional[List[float]] = None):
            self._registry = _CollectorRegistry()
            kw = {"buckets": buckets} if buckets else {}
            self._inner = _PromHistogram(name, help_text, registry=self._registry, **kw)

        def observe(self, value: float):
            self._inner.observe(value)

        def render(self) -> str:
            return generate_latest(self._registry).decode("utf-8")

    class MetricsRegistry:
        def __init__(self):
            self._registry = _CollectorRegistry()
            self._metrics = []

        def register(self, metric):
            self._metrics.append(metric)
            # Se a metrica tem _registry proprio (Counter/Histogram prometheus),
            # copia o registrador para o registry deste MetricsRegistry
            if hasattr(metric, '_inner') and hasattr(metric._inner, '_registry'):
                # Re-registra no registry compartilhado
                pass
            return metric

        def render(self) -> str:
            # Se tem metricas com _registry proprio, combina tudo
            combined = _CollectorRegistry()
            for m in self._metrics:
                if hasattr(m, '_registry'):
                    # Coleta metricas do registry individual e re-registra
                    for collector in m._registry._names_to_collectors.values():
                        try:
                            combined.register(collector)
                        except Exception:
                            pass  # Ja registrado
            return generate_latest(combined).decode("utf-8")

else:
    # -----------------------------------------------------------------------
    # Fallback NIH: implementacao propria minimal (zero dependencias)
    # -----------------------------------------------------------------------
    class Counter:
        def __init__(self, name: str, help_text: str, label_names: Optional[List[str]] = None):
            self.name = name
            self.help_text = help_text
            self.label_names = label_names or []
            self._values: Dict[tuple, float] = {}
            self._lock = threading.Lock()

        def inc(self, labels: Optional[Dict[str, str]] = None, amount: float = 1):
            key = self._label_key(labels)
            with self._lock:
                self._values[key] = self._values.get(key, 0) + amount

        def _label_key(self, labels):
            labels = labels or {}
            return tuple(str(labels.get(n, "")) for n in self.label_names)

        def _format_labels(self, key) -> str:
            if not self.label_names:
                return ""
            parts = [f'{name}="{val}"' for name, val in zip(self.label_names, key)]
            return "{" + ",".join(parts) + "}"

        def render(self) -> str:
            lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} counter"]
            with self._lock:
                items = list(self._values.items())
            for key, value in items:
                lines.append(f"{self.name}{self._format_labels(key)} {value}")
            return "\n".join(lines)

    class Histogram:
        DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

        def __init__(self, name: str, help_text: str, buckets: Optional[List[float]] = None):
            self.name = name
            self.help_text = help_text
            self.buckets = tuple(sorted(buckets or self.DEFAULT_BUCKETS))
            self._bucket_counts: Dict[float, int] = {b: 0 for b in self.buckets}
            self._count = 0
            self._sum = 0.0
            self._lock = threading.Lock()

        def observe(self, value: float):
            with self._lock:
                self._count += 1
                self._sum += value
                for b in self.buckets:
                    if value <= b:
                        self._bucket_counts[b] += 1

        def render(self) -> str:
            lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} histogram"]
            with self._lock:
                for b in self.buckets:
                    lines.append(f'{self.name}_bucket{{le="{b}"}} {self._bucket_counts[b]}')
                lines.append(f'{self.name}_bucket{{le="+Inf"}} {self._count}')
                lines.append(f"{self.name}_sum {self._sum}")
                lines.append(f"{self.name}_count {self._count}")
            return "\n".join(lines)

    class MetricsRegistry:
        def __init__(self):
            self._metrics = []

        def register(self, metric):
            self._metrics.append(metric)
            return metric

        def render(self) -> str:
            return "\n".join(m.render() for m in self._metrics) + "\n"


class RequestInstrumentation:
    """Instrumenta requisicoes HTTP: contagem por metodo/rota/status e histograma de latencia."""

    def __init__(self, registry: MetricsRegistry):
        self.requests_total = registry.register(Counter(
            "http_requests_total", "Total de requisicoes HTTP processadas",
            label_names=["method", "path", "status"]
        ))
        self.request_duration_seconds = registry.register(Histogram(
            "http_request_duration_seconds", "Latencia das requisicoes HTTP em segundos"
        ))

    def track_request(self, method: str, path: str, status: int, duration_seconds: float):
        self.requests_total.inc({"method": method, "path": path, "status": str(status)})
        self.request_duration_seconds.observe(duration_seconds)
