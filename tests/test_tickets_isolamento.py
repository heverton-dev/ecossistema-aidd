import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts" / "isolamento.py"

def carregar_isolamento():
    spec = importlib.util.spec_from_file_location("tickets_isolamento_mod", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tickets_isolamento_mod"] = mod
    spec.loader.exec_module(mod)
    return mod

def test_tickets_isolamento_bloqueia_escrita_fora_de_docs(tmp_path):
    isolamento = carregar_isolamento()
    manager = isolamento.TicketsWorktreeManager(repo_root=tmp_path)
    permitido = tmp_path / "docs" / "planos" / "export.json"
    assert manager.validar_caminho_escrita(permitido) is True

    proibido = tmp_path / "root_perigoso.json"
    with pytest.raises(isolamento.SandboxViolationError):
        manager.validar_caminho_escrita(proibido)
