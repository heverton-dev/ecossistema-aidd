# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v6.0-Enterprise — OpenTelemetry Distributed Tracing (Zero Fricção)
=============================================================================
TracerProvider com fallback para console exporter, decorator @trace_span,
middleware FastAPI para propagação de trace context, e injeção de trace_id
nos logs estruturados via correlation_id_var.

Zero dependência externa obrigatória: usa opentelemetry-api/sdk se disponíveis,
senão opera como no-op silencioso.
"""

import functools
import time
import uuid
from typing import Optional, Any

try:
    from src.core.logs import (
        correlation_id_var,
        get_logger,
        extract_or_generate_trace_id,
        get_current_trace_id,
    )
except ImportError:
    from core.logs import (
        correlation_id_var,
        get_logger,
        extract_or_generate_trace_id,
        get_current_trace_id,
    )

logger = get_logger("core.opentelemetry")

# ---------------------------------------------------------------------------
# Lazy imports — graceful no-op if OpenTelemetry is not installed
# ---------------------------------------------------------------------------
_otel_available = False
_trace = None
_trace_api = None
_Resource = None
_TracerProvider = None
_ConsoleSpanExporter = None
_BatchSpanProcessor = None
_status = None

try:
    from opentelemetry import trace as _trace_api
    from opentelemetry.sdk import trace as _trace
    from opentelemetry.sdk.trace import TracerProvider as _TracerProvider
    from opentelemetry.sdk.trace.export import (
        ConsoleSpanExporter as _ConsoleSpanExporter,
        BatchSpanProcessor as _BatchSpanProcessor,
    )
    from opentelemetry.sdk.resources import Resource as _Resource
    from opentelemetry.trace import StatusCode as _status
    _otel_available = True
except ImportError:
    pass

# ---------------------------------------------------------------------------
# TracerProvider singleton
# ---------------------------------------------------------------------------
_tracer: Optional[object] = None
_provider: Optional[object] = None


def _get_tracer():
    """Return the module-level tracer (lazy-init)."""
    global _tracer, _provider
    if _tracer is not None:
        return _tracer

    if not _otel_available:
        logger.info("opentelemetry_not_installed", extra={"detail": "Tracing disabled (no-op mode)"})
        return None

    try:
        resource = _Resource.create({"service.name": "aidd-enterprise"})
        _provider = _TracerProvider(resource=resource)

        # Always add console exporter as fallback
        console_exporter = _ConsoleSpanExporter()
        _provider.add_span_processor(_BatchSpanProcessor(console_exporter))

        _trace_api.set_tracer_provider(_provider)
        _tracer = _trace_api.get_tracer("aidd-enterprise")
        logger.info("opentelemetry_initialized", extra={"exporter": "console"})
    except Exception as e:
        logger.warning("opentelemetry_init_failed", extra={"error": str(e)})
        _tracer = None

    return _tracer


# ---------------------------------------------------------------------------
# @trace_span(name) decorator
# ---------------------------------------------------------------------------
def trace_span(name: str):
    """Decorator that wraps a function in an OpenTelemetry span.

    Injects trace_id into correlation_id_var so structured logs automatically
    carry the distributed trace identifier.

    Usage::

        @trace_span("my_operation")
        async def my_function():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = _get_tracer()
            if tracer is None:
                return await func(*args, **kwargs)

            with tracer.start_as_current_span(name) as span:
                trace_id = format(span.get_span_context().trace_id, "032x")
                correlation_id_var.set(trace_id)
                try:
                    result = await func(*args, **kwargs)
                    if _otel_available and _status is not None:
                        span.set_status(_status.OK)
                    return result
                except Exception as exc:
                    if _otel_available and _status is not None:
                        span.set_status(_status.ERROR, str(exc))
                    span.record_exception(exc)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = _get_tracer()
            if tracer is None:
                return func(*args, **kwargs)

            with tracer.start_as_current_span(name) as span:
                trace_id = format(span.get_span_context().trace_id, "032x")
                correlation_id_var.set(trace_id)
                try:
                    result = func(*args, **kwargs)
                    if _otel_available and _status is not None:
                        span.set_status(_status.OK)
                    return result
                except Exception as exc:
                    if _otel_available and _status is not None:
                        span.set_status(_status.ERROR, str(exc))
                    span.record_exception(exc)
                    raise

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ---------------------------------------------------------------------------
# Re-exportações de Trace Context (compatibilidade universal)
# ---------------------------------------------------------------------------
__all__ = [
    "trace_span",
    "extract_or_generate_trace_id",
    "get_current_trace_id",
    "_get_tracer",
    "_otel_available",
]


