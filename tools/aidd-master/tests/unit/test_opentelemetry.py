# -*- coding: utf-8 -*-
"""
Testes unitários de OpenTelemetry e Trilha de Auditoria (extract_or_generate_trace_id / @trace_span).
"""

import uuid
from src.core.opentelemetry import (
    extract_or_generate_trace_id,
    get_current_trace_id,
    trace_span,
)
from src.core.logs import correlation_id_var


def test_extract_trace_id_from_dict_case_variants():
    # 1. Header padrão X-Trace-Id
    cid1 = extract_or_generate_trace_id({"X-Trace-Id": "req-111"})
    assert cid1 == "req-111"
    assert get_current_trace_id() == "req-111"

    # 2. Header variante X-Trace-ID
    cid2 = extract_or_generate_trace_id({"X-Trace-ID": "req-222"})
    assert cid2 == "req-222"
    assert get_current_trace_id() == "req-222"

    # 3. Header minúsculo x-trace-id
    cid3 = extract_or_generate_trace_id({"x-trace-id": "req-333"})
    assert cid3 == "req-333"
    assert get_current_trace_id() == "req-333"


def test_generate_trace_id_when_missing_or_empty():
    # None
    cid1 = extract_or_generate_trace_id(None)
    assert len(cid1) >= 16
    assert get_current_trace_id() == cid1

    # Dicionário vazio
    cid2 = extract_or_generate_trace_id({})
    assert len(cid2) >= 16
    assert get_current_trace_id() == cid2

    # String vazia ou espaços
    cid3 = extract_or_generate_trace_id({"X-Trace-Id": "   "})
    assert len(cid3) >= 16
    assert get_current_trace_id() == cid3


def test_trace_span_decorator_execution():
    @trace_span("operacao_teste")
    def sync_op(x, y):
        return x + y

    res = sync_op(2, 3)
    assert res == 5
    # correlation_id_var deve conter um trace_id após execução
    assert correlation_id_var.get() != "N/A"
