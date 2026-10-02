# -*- coding: utf-8 -*-
"""
AIDD v6.1 — Structured Logging & OpenTelemetry Configuration
============================================================
Zero-Dependency Fallback: structlog + OTel configured centrally.
Production: JSON logs.  Development: human-readable pretty-printed logs.
Configurable via LOG_LEVEL env var (default: INFO).

Usage:
    from logging_config import setup_logging, setup_otel
    setup_logging()
    tracer = setup_otel(service_name="aidd-enterprise")
"""

import logging
import os
import sys
from typing import Optional

import structlog

# ---------------------------------------------------------------------------
# Structured Logging
# ---------------------------------------------------------------------------
_ENV = os.environ.get("AIDD_ENV", os.environ.get("ENV", "development"))
_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def _add_pid_context(logger, method_name, event_dict):
    """Inject PID into every log line for distributed tracing correlation."""
    import os
    event_dict["pid"] = os.getpid()
    return event_dict


def _add_trace_context(logger, method_name, event_dict):
    """Inject OpenTelemetry trace/span IDs into log context if available."""
    try:
        from opentelemetry import trace
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    except Exception:
        pass
    return event_dict


def setup_logging() -> None:
    """Configure structlog with environment-aware processors."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        _add_pid_context,
        _add_trace_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if _ENV == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, _LOG_LEVEL, logging.INFO))

    # Quiet noisy third-party loggers
    for name in ("uvicorn.access", "uvicorn.error", "httpcore", "httpx"):
        logging.getLogger(name).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# OpenTelemetry Distributed Tracing
# ---------------------------------------------------------------------------
def setup_otel(service_name: str = "aidd-enterprise") -> Optional[object]:
    """
    Initialize OpenTelemetry with OTLP exporter (if configured) or
    fall back to a no-op tracer. Returns the tracer instance.

    Environment variables:
        OTEL_EXPORTER_OTLP_ENDPOINT  — collector URL (e.g. http://localhost:4317)
        OTEL_SERVICE_NAME            — overrides service_name param
        OTEL_TRACES_EXPORTER         — "otlp", "console", or "none" (default: auto)
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource

        svc = os.environ.get("OTEL_SERVICE_NAME", service_name)
        resource = Resource.create({SERVICE_NAME: svc})
        provider = TracerProvider(resource=resource)

        exporter_mode = os.environ.get("OTEL_TRACES_EXPORTER", "auto")
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")

        if exporter_mode == "none":
            pass  # no exporter — tracer still active for context propagation
        elif exporter_mode == "console" or (exporter_mode == "auto" and not otlp_endpoint):
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        else:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )
                kwargs = {}
                if otlp_endpoint:
                    kwargs["endpoint"] = otlp_endpoint
                provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(**kwargs)))
            except Exception:
                # OTLP exporter not configured/available — degrade gracefully
                pass

        trace.set_tracer_provider(provider)
        return trace.get_tracer(service_name, "1.0.0")

    except ImportError:
        # opentelemetry not installed — return a no-op compatible object
        class _NoopTracer:
            def start_span(self, name, **kw):
                return _NoopSpan()
            def start_as_current_span(self, name, **kw):
                return _NoopSpan()

        class _NoopSpan:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
            def set_attribute(self, *a):
                pass
            def add_event(self, *a, **kw):
                pass

        return _NoopTracer()
