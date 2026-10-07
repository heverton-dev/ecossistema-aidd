# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

ROOT = next((p.parent for p in Path(__file__).resolve().parents if p.name == "modulos"), Path(__file__).resolve().parent.parent)  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)

def test_gate_g_aidd_handoff_reprova_invalido(tmp_path):
    arquivo = tmp_path / "invalido.md"
    arquivo.write_text("# Incompleto\n", encoding="utf-8")

    gate_script = ROOT / "modulos" / "01-governanca-e-qualidade" / "gates" / "G_aidd_handoff.py"
    res = subprocess.run(
        [sys.executable, str(gate_script), str(arquivo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 1

def test_gate_g_aidd_handoff_aprova_valido(tmp_path):
    arquivo = tmp_path / "valido.md"
    arquivo.write_text("""# Sessao Handoff
## Initial Goal
Meta
## Completed Work
Trabalho
## Quality Gate State
OK
## Next Actions
Acoes
## Discovered Invariants & Gotchas
Invariantes
""", encoding="utf-8")

    gate_script = ROOT / "modulos" / "01-governanca-e-qualidade" / "gates" / "G_aidd_handoff.py"
    res = subprocess.run(
        [sys.executable, str(gate_script), str(arquivo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
