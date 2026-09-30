import importlib.util
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts" / "handoff.py"

def carregar_handoff():
    spec = importlib.util.spec_from_file_location("tickets_handoff_mod", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tickets_handoff_mod"] = mod
    spec.loader.exec_module(mod)
    return mod

def test_tickets_handoff_hmac(tmp_path):
    handoff = carregar_handoff()

    tickets = [
        {"id": "T1", "target_files": ["src/app.py", "tests/test_app.py"], "blocked_by": []}
    ]

    out_json = tmp_path / "handoff-tickets.json"
    sucesso = handoff.gerar_handoff_tickets(tickets, ["T1"], out_json, chave="chave_teste")
    assert sucesso is True
    assert out_json.exists()

    valido = handoff.verificar_handoff_tickets(out_json, chave="chave_teste")
    assert valido is True

    # Adulterar
    with open(out_json, "r", encoding="utf-8") as f:
        dados = json.load(f)
    dados["payload"]["total_tickets"] = 99
    out_json.write_text(json.dumps(dados), encoding="utf-8")

    assert handoff.verificar_handoff_tickets(out_json, chave="chave_teste") is False
