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


# =============================================================================
# SLA/SLO Metrics — Histogram with latency buckets + HTML Dashboard
# =============================================================================

SLA_LATENCY_BUCKETS = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0]


class SLAHistogram:
    """Histogram with SLA-oriented buckets for p99/p95 tracking.

    Buckets: [0.05, 0.1, 0.2, 0.5, 1.0, 2.0] seconds.
    Provides percentile estimation from cumulative bucket counts.
    """

    def __init__(self, name: str, help_text: str, buckets: Optional[List[float]] = None):
        self.name = name
        self.help_text = help_text
        self.buckets = tuple(sorted(buckets or SLA_LATENCY_BUCKETS))
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

    def _percentile(self, p: float) -> float:
        """Estimate the p-th percentile (0 < p < 1) from cumulative buckets."""
        if self._count == 0:
            return 0.0
        target = p * self._count
        prev_count = 0
        prev_bucket = 0.0
        for b in self.buckets:
            count_at_b = self._bucket_counts[b]
            if count_at_b >= target:
                # Linear interpolation within bucket
                if count_at_b == prev_count:
                    return b
                fraction = (target - prev_count) / (count_at_b - prev_count)
                return prev_bucket + fraction * (b - prev_bucket)
            prev_count = count_at_b
            prev_bucket = b
        return float("inf")

    def p99(self) -> float:
        return self._percentile(0.99)

    def p95(self) -> float:
        return self._percentile(0.95)

    def p50(self) -> float:
        return self._percentile(0.50)

    def mean(self) -> float:
        with self._lock:
            return self._sum / self._count if self._count > 0 else 0.0

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help_text}", f"# TYPE {self.name} histogram"]
        with self._lock:
            for b in self.buckets:
                lines.append(f'{self.name}_bucket{{le="{b}"}} {self._bucket_counts[b]}')
            lines.append(f'{self.name}_bucket{{le="+Inf"}} {self._count}')
            lines.append(f"{self.name}_sum {self._sum}")
            lines.append(f"{self.name}_count {self._count}")
        return "\n".join(lines)


def generate_prometheus_dashboard_html(registry: MetricsRegistry) -> str:
    """Generate a self-contained HTML dashboard for Prometheus metrics.

    Scans the registry for SLAHistogram instances and renders:
    - Live metric values (p50, p95, p99, mean, count)
    - Visual alert badge (red) when p99 > 200ms
    - Raw Prometheus exposition text
    """
    # Collect SLA histograms from registry
    sla_histograms = [m for m in registry._metrics if isinstance(m, SLAHistogram)]

    # Build metric cards
    cards_html = ""
    for h in sla_histograms:
        p99_val = h.p99()
        p95_val = h.p95()
        p50_val = h.p50()
        mean_val = h.mean()
        count_val = h._count

        # Alert badge: red when p99 > 200ms
        p99_ms = p99_val * 1000
        alert_badge = ""
        if p99_ms > 200:
            alert_badge = (
                '<span style="background:#e74c3c;color:#fff;padding:2px 8px;'
                'border-radius:4px;font-weight:bold;margin-left:8px;">'
                f'⚠ SLO BREACH — p99 = {p99_ms:.0f}ms &gt; 200ms</span>'
            )

        cards_html += f"""
        <div style="background:#1e1e2e;border:1px solid #333;border-radius:8px;padding:20px;margin:12px 0;">
            <h3 style="color:#89b4fa;margin:0 0 12px 0;">{h.name} {alert_badge}</h3>
            <p style="color:#6c7086;margin:0 0 16px 0;">{h.help_text}</p>
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
                <div style="text-align:center;">
                    <div style="color:#a6e3a1;font-size:24px;font-weight:bold;">{p50_val*1000:.1f}ms</div>
                    <div style="color:#6c7086;font-size:12px;">p50</div>
                </div>
                <div style="text-align:center;">
                    <div style="color:#f9e2af;font-size:24px;font-weight:bold;">{p95_val*1000:.1f}ms</div>
                    <div style="color:#6c7086;font-size:12px;">p95</div>
                </div>
                <div style="text-align:center;">
                    <div style="color:{'#e74c3c' if p99_ms > 200 else '#a6e3a1'};font-size:24px;font-weight:bold;">{p99_ms:.1f}ms</div>
                    <div style="color:#6c7086;font-size:12px;">p99</div>
                </div>
                <div style="text-align:center;">
                    <div style="color:#89b4fa;font-size:24px;font-weight:bold;">{mean_val*1000:.1f}ms</div>
                    <div style="color:#6c7086;font-size:12px;">mean</div>
                </div>
                <div style="text-align:center;">
                    <div style="color:#cba6f7;font-size:24px;font-weight:bold;">{count_val}</div>
                    <div style="color:#6c7086;font-size:12px;">count</div>
                </div>
            </div>
        </div>
        """

    # Raw Prometheus text
    raw_metrics = registry.render().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIDD Prometheus Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #11111b; color: #cdd6f4; font-family: 'Segoe UI', system-ui, sans-serif; padding: 32px; }}
        h1 {{ color: #89b4fa; margin-bottom: 8px; }}
        .subtitle {{ color: #6c7086; margin-bottom: 24px; }}
        pre {{ background: #181825; border: 1px solid #333; border-radius: 8px; padding: 16px; overflow-x: auto; font-size: 13px; color: #a6adc8; margin-top: 24px; }}
    </style>
</head>
<body>
    <h1>AIDD Prometheus SLA Dashboard</h1>
    <p class="subtitle">Auto-generated metrics overview &middot; SLO target: p99 &le; 200ms</p>
    {cards_html if cards_html else '<p style="color:#6c7086;">No SLA histograms registered yet.</p>'}
    <h2 style="color:#89b4fa;margin-top:32px;">Raw Prometheus Exposition</h2>
    <pre>{raw_metrics}</pre>
</body>
</html>"""
