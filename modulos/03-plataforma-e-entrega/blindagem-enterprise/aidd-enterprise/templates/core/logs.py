# -*- coding: utf-8 -*-
"""
Logs Estruturados Universais
Formato JSON com suporte a contextvars para propagação de Correlation ID (X-Correlation-ID).
"""
import logging
import json
import traceback
import uuid
from datetime import datetime, timezone
import contextvars

# Variável de contexto para o correlation ID / trace ID
correlation_id_var = contextvars.ContextVar('correlation_id', default='N/A')


def extract_or_generate_trace_id(headers=None) -> str:
    """Extrai trace_id de headers HTTP ('X-Trace-Id', 'X-Trace-ID' ou 'x-trace-id')
    ou gera um UUID v4 hexadecimal caso ausente.
    Propaga imediatamente para correlation_id_var para que logs estruturados e
    chamadas downstream compartilhem o mesmo trace context (LGPD/GDPR audit trail).
    """
    trace_id = ""
    if headers is not None:
        if hasattr(headers, "get"):
            trace_id = (
                headers.get("X-Trace-Id")
                or headers.get("X-Trace-ID")
                or headers.get("x-trace-id")
                or ""
            )
        elif hasattr(headers, "__getitem__"):
            try:
                trace_id = headers["X-Trace-Id"]
            except KeyError:
                trace_id = ""

    if not trace_id or not isinstance(trace_id, str) or not trace_id.strip():
        trace_id = uuid.uuid4().hex
    else:
        trace_id = trace_id.strip()

    correlation_id_var.set(trace_id)
    return trace_id


def get_current_trace_id() -> str:
    """Retorna o trace_id configurado no contexto atual."""
    return correlation_id_var.get()

class JSONFormatter(logging.Formatter):
    def format(self, record):
        cid = getattr(record, "correlation_id", None) or correlation_id_var.get()
        trace_id = getattr(record, "trace_id", None) or cid
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "trace_id": trace_id,
            "correlation_id": cid,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_record["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(log_record, ensure_ascii=False)

def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
