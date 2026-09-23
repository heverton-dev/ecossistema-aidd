# -*- coding: utf-8 -*-
"""
Teste de Tratamento de Exceções e Fallback Operacional (Ticket 4 / D11).
Exige lógica de retry backoff autônomo e fallback graceful em caso de falha transitória ou de I/O.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))


def test_retry_com_backoff_sucesso_apos_tentativas():
    """Garante que operação que falha inicialmente se recupera com retry backoff autônomo."""
    from analisador import executar_com_retry

    mock_func = MagicMock()
    mock_func.side_effect = [TimeoutError("Timeout transitório"), TimeoutError("Timeout transitório"), {"status": "ok"}]

    resultado = executar_com_retry(mock_func, max_tentativas=3, backoff_base=0.01)
    assert resultado == {"status": "ok"}
    assert mock_func.call_count == 3


def test_falha_persistente_aciona_fallback_graceful_sem_perda_de_estado():
    """Garante que falha persistente gera registro formal de erro sem exceção descontrolada."""
    from analisador import executar_com_retry, FallbackOperacionalError

    mock_func = MagicMock()
    mock_func.side_effect = TimeoutError("Falha irrecuperavel na LLM")

    with pytest.raises(FallbackOperacionalError) as exc_info:
        executar_com_retry(mock_func, max_tentativas=2, backoff_base=0.01)

    assert "Falha irrecuperavel" in str(exc_info.value)
