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


def test_reprova_quando_gate_usa_saida_nao_binaria():
    """Prova que o portão morde (Lei #13): synthetic gate com sys.exit(2) retorna exit 1."""
    synthetic_gate = os.path.join(GATES_DIR, "G_SYNTHETIC_EXIT_TRAP.py")
    try:
        with open(synthetic_gate, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("import sys\n\n")
            f.write("if __name__ == '__main__':\n")
            f.write("    sys.exit(2)\n")

        res = subprocess.run(
            [sys.executable, GATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            encoding="utf-8",
            errors="replace",
        )
        assert res.returncode == 1, f"Deveria reprovar com exit 1, retornou {res.returncode}"
        assert "G_SYNTHETIC_EXIT_TRAP.py" in res.stdout
        assert "Código de saída '2' inválido" in res.stdout
    finally:
        if os.path.exists(synthetic_gate):
            os.remove(synthetic_gate)


def test_reprova_quando_gate_carece_de_sys_exit_no_main():
    """Prova que o portão morde quando bloco __main__ não chama sys.exit (fall-through)."""
    synthetic_gate = os.path.join(GATES_DIR, "G_SYNTHETIC_FALLTHROUGH_TRAP.py")
    try:
        with open(synthetic_gate, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("def run():\n    pass\n\n")
            f.write("if __name__ == '__main__':\n")
            f.write("    run()\n")

        res = subprocess.run(
            [sys.executable, GATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            encoding="utf-8",
            errors="replace",
        )
        assert res.returncode == 1, f"Deveria reprovar com exit 1, retornou {res.returncode}"
        assert "G_SYNTHETIC_FALLTHROUGH_TRAP.py" in res.stdout
        assert "não contém chamada explícita a sys.exit" in res.stdout
    finally:
        if os.path.exists(synthetic_gate):
            os.remove(synthetic_gate)
