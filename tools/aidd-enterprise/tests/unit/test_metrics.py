# -*- coding: utf-8 -*-
"""
Testes das métricas Prometheus (Onda 4 / v6.0-Enterprise): valida o formato
de exposição (# HELP / # TYPE / séries + labels), a semântica cumulativa dos
buckets de histograma, e o overhead de instrumentação medido via timeit
(critério de aceite: < 0.1ms de overhead por requisição).
"""

import os
import sys
import timeit

TEMPLATES_V2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates", "v2"))
if TEMPLATES_V2 not in sys.path:
    sys.path.insert(0, TEMPLATES_V2)

from metrics import Counter, Histogram, MetricsRegistry, RequestInstrumentation  # noqa: E402


def test_counter_render_produces_valid_help_and_type_lines():
    c = Counter("aidd_test_total", "Contador de teste")
    c.inc()
    c.inc()
    rendered = c.render()

    lines = rendered.splitlines()
    assert lines[0] == "# HELP aidd_test_total Contador de teste"
    assert lines[1] == "# TYPE aidd_test_total counter"
    assert "aidd_test_total 2" in rendered


def test_counter_render_includes_labels_in_prometheus_format():
    c = Counter("aidd_requests_total", "Requisicoes", label_names=["method", "status"])
    c.inc({"method": "GET", "status": "200"})
    c.inc({"method": "GET", "status": "200"})
    c.inc({"method": "POST", "status": "500"})

    rendered = c.render()
    assert 'aidd_requests_total{method="GET",status="200"} 2' in rendered
    assert 'aidd_requests_total{method="POST",status="500"} 1' in rendered


def test_histogram_buckets_are_cumulative_like_prometheus():
    h = Histogram("aidd_latency_seconds", "Latencia de teste", buckets=[0.1, 0.5, 1.0])
    h.observe(0.05)  # cai em todos os buckets (<=0.1, <=0.5, <=1.0)
    h.observe(0.3)   # cai em <=0.5 e <=1.0
    h.observe(2.0)   # cai apenas em +Inf

    rendered = h.render()
    assert 'aidd_latency_seconds_bucket{le="0.1"} 1' in rendered
    assert 'aidd_latency_seconds_bucket{le="0.5"} 2' in rendered
    assert 'aidd_latency_seconds_bucket{le="1.0"} 2' in rendered
    assert 'aidd_latency_seconds_bucket{le="+Inf"} 3' in rendered
    assert "aidd_latency_seconds_count 3" in rendered
    assert "aidd_latency_seconds_sum 2.35" in rendered


def test_metrics_registry_renders_all_registered_metrics_together():
    registry = MetricsRegistry()
    c = registry.register(Counter("a_total", "A"))
    h = registry.register(Histogram("b_seconds", "B"))
    c.inc()
    h.observe(0.01)

    rendered = registry.render()
    assert "# TYPE a_total counter" in rendered
    assert "# TYPE b_seconds histogram" in rendered
    assert rendered.endswith("\n")


def test_request_instrumentation_tracks_method_path_and_status():
    registry = MetricsRegistry()
    instrumentation = RequestInstrumentation(registry)

    instrumentation.track_request("GET", "/api/pedidos", 200, 0.012)
    instrumentation.track_request("POST", "/api/pedidos/criar", 500, 0.045)

    rendered = registry.render()
    assert 'http_requests_total{method="GET",path="/api/pedidos",status="200"} 1' in rendered
    assert 'http_requests_total{method="POST",path="/api/pedidos/criar",status="500"} 1' in rendered
    assert "http_request_duration_seconds_count 2" in rendered


def test_instrumentation_overhead_is_below_one_tenth_millisecond():
    """Critério de aceite: overhead de instrumentação < 0.1ms por requisição."""
    registry = MetricsRegistry()
    instrumentation = RequestInstrumentation(registry)

    def instrumented_call():
        instrumentation.track_request("GET", "/health", 200, 0.001)

    n = 1000
    total_seconds = timeit.timeit(instrumented_call, number=n)
    overhead_ms_per_call = (total_seconds / n) * 1000

    assert overhead_ms_per_call < 0.1, f"Overhead medido: {overhead_ms_per_call:.4f}ms (limite: 0.1ms)"
