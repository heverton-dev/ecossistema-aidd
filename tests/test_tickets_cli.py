import importlib.util
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts" / "cli.py"

def carregar_cli():
    spec = importlib.util.spec_from_file_location("tickets_cli_mod", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tickets_cli_mod"] = mod
    spec.loader.exec_module(mod)
    return mod

EXEMPLO_MD = """
### [TICKET-01] Primeiro passo
- **Target Files:** src/app.py, tests/test_app.py
- **Validation Command:** `pytest tests/test_app.py`
- **Blocked by:** none

### [TICKET-02] Segundo passo
- **Target Files:** src/app.py, tests/test_segundo.py
- **Validation Command:** `pytest tests/test_segundo.py`
- **Blocked by:** TICKET-01
"""

def test_tickets_cli_validar(tmp_path):
    cli = carregar_cli()
    arq = tmp_path / "tickets.md"
    arq.write_text(EXEMPLO_MD, encoding="utf-8")

    res = cli.main(["validar", "--arquivo", str(arq)])
    assert res == 0

def test_tickets_cli_exportar(tmp_path):
    cli = carregar_cli()
    arq = tmp_path / "tickets.md"
    arq.write_text(EXEMPLO_MD, encoding="utf-8")
    out_json = tmp_path / "export.json"

    res = cli.main(["exportar", "--arquivo", str(arq), "--output", str(out_json)])
    assert res == 0
    assert out_json.exists()

    with open(out_json, "r", encoding="utf-8") as f:
        dados = json.load(f)
    assert len(dados["tickets"]) == 2
    assert dados["ordem_topologica"] == ["TICKET-01", "TICKET-02"]
