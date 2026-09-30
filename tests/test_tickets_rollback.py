import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts" / "rollback.py"

def carregar_rollback():
    spec = importlib.util.spec_from_file_location("tickets_rollback_mod", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tickets_rollback_mod"] = mod
    spec.loader.exec_module(mod)
    return mod

def test_tickets_rollback_limpa_artefato_parcial(tmp_path):
    rollback = carregar_rollback()
    arq_parcial = tmp_path / "tickets_parcial.json"
    arq_parcial.write_text("{}", encoding="utf-8")
    assert arq_parcial.exists()

    sucesso = rollback.limpar_artefatos_parciais([arq_parcial])
    assert sucesso is True
    assert not arq_parcial.exists()
