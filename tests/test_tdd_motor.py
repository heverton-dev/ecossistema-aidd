import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_motor_tdd_avalia_red_valido_vs_erro_sintaxe():
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import motor_tdd

    # Falha funcional valida para RED
    saida_assert = "FAILED tests/test_demo.py::test_algo - AssertionError: assert 1 == 2"
    valido, tipo = motor_tdd.analisar_resultado_red(saida_assert, exit_code=1)
    assert valido is True
    assert tipo == "ASSERTION_FAILURE"

    # Erro de sintaxe (invalido para RED)
    saida_syntax = "SyntaxError: invalid syntax"
    valido, tipo = motor_tdd.analisar_resultado_red(saida_syntax, exit_code=1)
    assert valido is False
    assert tipo == "SYNTAX_ERROR"

    # Runner com sucesso em RED e invalido (deveria falhar)
    saida_sucesso = "1 passed in 0.01s"
    valido, tipo = motor_tdd.analisar_resultado_red(saida_sucesso, exit_code=0)
    assert valido is False
    assert tipo == "UNEXPECTED_PASS"
