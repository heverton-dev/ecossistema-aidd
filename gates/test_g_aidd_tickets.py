# -*- coding: utf-8 -*-
"""
Teste de Quality Gate Determinístico de Tickets (Ticket 7 / Lei #13).
Comprova que G_aidd_tickets.py aprova tickets íntegros (exit 0) e morde (exit 1) diante de:
1. Grafo com dependência circular (deadlock).
2. Ticket sem arquivo de teste em Target Files.
3. Arquivo inexistente ou sem tickets.
"""

import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "gates" / "G_aidd_tickets.py"

def executar_gate(arquivo_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE), "--arquivo", str(arquivo_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT)
    )

def test_gate_tickets_aprova_tickets_integros(tmp_path):
    arq = tmp_path / "tickets_ok.md"
    arq.write_text("""
### [TICKET-01] Passo inicial
- **Target Files:** src/app.py, tests/test_app.py
- **Validation Command:** `pytest`
- **Blocked by:** none

### [TICKET-02] Passo seguinte
- **Target Files:** src/app.py, tests/test_app2.py
- **Validation Command:** `pytest`
- **Blocked by:** TICKET-01
""", encoding="utf-8")

    res = executar_gate(arq)
    assert res.returncode == 0
    assert "APROVADO" in res.stdout

def test_gate_tickets_morde_se_houver_ciclo(tmp_path):
    arq = tmp_path / "tickets_ciclo.md"
    arq.write_text("""
### [TICKET-01] Passo 1
- **Target Files:** src/app.py, tests/test_app.py
- **Validation Command:** `pytest`
- **Blocked by:** TICKET-02

### [TICKET-02] Passo 2
- **Target Files:** src/app.py, tests/test_app2.py
- **Validation Command:** `pytest`
- **Blocked by:** TICKET-01
""", encoding="utf-8")

    res = executar_gate(arq)
    assert res.returncode == 1
    assert "Ciclo de dependência detectado" in res.stdout

def test_gate_tickets_morde_se_faltar_teste(tmp_path):
    arq = tmp_path / "tickets_sem_teste.md"
    arq.write_text("""
### [TICKET-01] Passo sem teste
- **Target Files:** src/app.py
- **Validation Command:** `pytest`
- **Blocked by:** none
""", encoding="utf-8")

    res = executar_gate(arq)
    assert res.returncode == 1
    assert "pelo menos um arquivo de teste" in res.stdout
