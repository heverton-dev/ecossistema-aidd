import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

EXEMPLO_MARKDOWN = """
### [TICKET-01] Implementar login básico
- **Target Files:** src/auth.py, tests/test_auth.py
- **Validation Command:** `pytest tests/test_auth.py`
- **Blocked by:** none

### [TICKET-02] Adicionar refresh token
- **Target Files:** src/auth.py, tests/test_refresh.py
- **Validation Command:** `pytest tests/test_refresh.py`
- **Blocked by:** TICKET-01
"""

EXEMPLO_SEM_TESTE = """
### [TICKET-01] Modulo sem teste
- **Target Files:** src/auth.py
- **Validation Command:** `pytest tests/test_auth.py`
- **Blocked by:** none
"""

def test_tickets_parser_parseia_markdown_valido():
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts"))
    import parser

    tickets, erros = parser.parsear_tickets_markdown(EXEMPLO_MARKDOWN)
    assert len(erros) == 0
    assert len(tickets) == 2
    assert tickets[0]["id"] == "TICKET-01"
    assert tickets[0]["blocked_by"] == []
    assert tickets[1]["id"] == "TICKET-02"
    assert tickets[1]["blocked_by"] == ["TICKET-01"]

def test_tickets_parser_reprova_ticket_sem_arquivo_de_teste():
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts"))
    import parser

    tickets, erros = parser.parsear_tickets_markdown(EXEMPLO_SEM_TESTE)
    assert len(erros) > 0
    assert any("pelo menos um arquivo de teste" in e.lower() for e in erros)
