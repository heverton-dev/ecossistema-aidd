import importlib.util
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts" / "observabilidade.py"

def carregar_observabilidade():
    spec = importlib.util.spec_from_file_location("tickets_obs_mod", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tickets_obs_mod"] = mod
    spec.loader.exec_module(mod)
    return mod

def test_tickets_observabilidade_calcula_metricas(tmp_path):
    observabilidade = carregar_observabilidade()

    tickets = [
        {"id": "T1", "target_files": ["src/a.py", "tests/test_a.py"], "blocked_by": []},
        {"id": "T2", "target_files": ["src/b.py", "tests/test_b.py"], "blocked_by": ["T1"]},
        {"id": "T3", "target_files": ["src/c.py", "tests/test_c.py"], "blocked_by": ["T1"]}
    ]

    rastreador = observabilidade.RastreadorTickets()
    metricas = rastreador.analisar_tickets(tickets)

    assert metricas["total_tickets"] == 3
    assert metricas["total_arquivos_distintos"] == 6
    assert metricas["tickets_paralelos_iniciais"] == 1
    assert metricas["profundidade_maxima_dag"] == 2

    out_file = tmp_path / "metricas_tickets.json"
    rastreador.salvar_metricas(out_file)
    assert out_file.exists()
