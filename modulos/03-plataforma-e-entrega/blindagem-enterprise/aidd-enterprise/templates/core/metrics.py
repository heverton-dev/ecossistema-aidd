# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v6.0-Enterprise — Métricas Prometheus (Sem Dependências Externas)
=============================================================================
Implementação própria e mínima do exposition format do Prometheus
(# HELP / # TYPE / série + labels), preservando o princípio de Zero Fricção
do pack: nenhuma dependência nova (prometheus_client) é necessária para
expor GET /metrics de forma compatível com qualquer scraper Prometheus.
"""

import threading
from typing import Dict, List, Optional


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
    """Histograma com buckets cumulativos fixos (semântica `le`, igual ao Prometheus)."""

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
    """Instrumenta requisições HTTP: contagem por método/rota/status e histograma de latência."""

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
