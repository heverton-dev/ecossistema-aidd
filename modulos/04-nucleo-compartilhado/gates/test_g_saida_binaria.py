#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DE PROVA QUE MORDE: test_g_saida_binaria.py
=============================================================================
Validação estrita em runtime (Lei #13 / ISSUE-0021):
  1. Caminho feliz: suíte de gates atual é 100% binária (exit 0).
  2. Cenário de reprovação deliberada: synthetic gate file com sys.exit(2)
     ou sem sys.exit no main() causa exit 1 imediato.
"""

import os
import subprocess
import sys
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES_DIR = os.path.join(ROOT_DIR, "gates")
GATE_SCRIPT = os.path.join(GATES_DIR, "G_SAIDA_BINARIA.py")


def test_aprova_gates_com_saida_binaria_conforme():
    """Valida caminho feliz: todos os gates atuais usam saídas 0 ou 1."""
    res = subprocess.run(
        [sys.executable, GATE_SCRIPT],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0, f"Gate reprovou indevidamente:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"
    assert "SUCESSO" in res.stdout
    assert "LIMITE METROLÓGICO" in res.stdout


def test_reprova_quando_gate_usa_saida_nao_binaria(tmp_path):
    """Prova que o portão morde (Lei #13): synthetic gate com sys.exit(2) retorna exit 1."""
    synthetic_gate = tmp_path / "G_SYNTHETIC_EXIT_TRAP.py"
    synthetic_gate.write_text(
        "#!/usr/bin/env python3\nimport sys\n\nif __name__ == '__main__':\n    sys.exit(2)\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, GATE_SCRIPT, str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 1, f"Deveria reprovar com exit 1, retornou {res.returncode}"
    assert "G_SYNTHETIC_EXIT_TRAP.py" in res.stdout
    assert "Código de saída '2' inválido" in res.stdout


def test_reprova_quando_gate_carece_de_sys_exit_no_main(tmp_path):
    """Prova que o portão morde quando bloco __main__ não chama sys.exit (fall-through)."""
    synthetic_gate = tmp_path / "G_SYNTHETIC_FALLTHROUGH_TRAP.py"
    synthetic_gate.write_text(
        "#!/usr/bin/env python3\ndef run():\n    pass\n\nif __name__ == '__main__':\n    run()\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, GATE_SCRIPT, str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 1, f"Deveria reprovar com exit 1, retornou {res.returncode}"
    assert "G_SYNTHETIC_FALLTHROUGH_TRAP.py" in res.stdout
    assert "não contém chamada explícita a sys.exit" in res.stdout
