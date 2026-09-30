import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_grafo_dag_ordena_topologicamente():
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts"))
    import grafo_dag

    tickets = [
        {"id": "T3", "blocked_by": ["T2"]},
        {"id": "T1", "blocked_by": []},
        {"id": "T2", "blocked_by": ["T1"]}
    ]

    valido, ordem, erro = grafo_dag.ordenar_topologicamente_kahn(tickets)
    assert valido is True
    assert ordem == ["T1", "T2", "T3"]
    assert erro == ""

def test_grafo_dag_detecta_ciclo_circular():
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts"))
    import grafo_dag

    tickets_ciclicos = [
        {"id": "T1", "blocked_by": ["T2"]},
        {"id": "T2", "blocked_by": ["T1"]}
    ]

    valido, ordem, erro = grafo_dag.ordenar_topologicamente_kahn(tickets_ciclicos)
    assert valido is False
    assert "ciclo" in erro.lower() or "deadlock" in erro.lower()
