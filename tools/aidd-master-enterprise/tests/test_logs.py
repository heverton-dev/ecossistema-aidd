import pytest
import json
import io
import logging
from src.core.logs import get_logger, correlation_id_var, JSONFormatter

def test_json_formatter():
    logger = get_logger("test_json")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    
    logger.handlers = []
    logger.addHandler(handler)
    
    correlation_id_var.set("test-123")
    logger.info("Hello World")
    
    output = stream.getvalue()
    data = json.loads(output)
    
    assert data["level"] == "INFO"
    assert data["message"] == "Hello World"
    assert data["correlation_id"] == "test-123"
    assert data["logger"] == "test_json"
