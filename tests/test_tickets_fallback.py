import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts" / "fallback.py"

def carregar_fallback():
    spec = importlib.util.spec_from_file_location("tickets_fallback_mod", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tickets_fallback_mod"] = mod
    spec.loader.exec_module(mod)
    return mod

def test_tickets_fallback_recupera_tickets_bem_formados():
    fallback = carregar_fallback()
    conteudo_misto = """
    Lixo aleatório no topo do arquivo...
    ### [TICKET-01] Ticket válido
    - **Target Files:** src/app.py, tests/test_app.py
    - **Validation Command:** `pytest`
    - **Blocked by:** none

    Outro bloco corrompido sem campos...
    """

    tickets, avisos = fallback.extrair_tickets_resiliente(conteudo_misto)
    assert len(tickets) == 1
    assert tickets[0]["id"] == "TICKET-01"
    assert len(avisos) >= 1
