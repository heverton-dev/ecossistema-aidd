# -*- coding: utf-8 -*-
"""
Logs Estruturados Universais
Formato JSON com suporte a contextvars para propagação de Correlation ID (X-Correlation-ID).
"""
import logging
import json
import traceback
from datetime import datetime, timezone
import contextvars

# Variável de contexto para o correlation ID
correlation_id_var = contextvars.ContextVar('correlation_id', default='N/A')

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "correlation_id": correlation_id_var.get(),
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
