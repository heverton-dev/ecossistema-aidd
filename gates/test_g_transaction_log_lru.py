# -*- coding: utf-8 -*-
"""
Testes do gate G_TRANSACTION_LOG_LRU.
"""

import os
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE_PATH = os.path.join(ROOT_DIR, "gates", "G_TRANSACTION_LOG_LRU.py")


class TestGTransactionLogLru:
    def test_gate_exit_0(self):
        """O gate deve passar com exit 0 quando a entrega está íntegra e espelhada."""
        resultado = subprocess.run(
            [sys.executable, GATE_PATH],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            timeout=30,
        )
        assert resultado.returncode == 0, (
            f"Gate falhou com exit {resultado.returncode}.\n"
            f"STDOUT:\n{resultado.stdout}\n"
            f"STDERR:\n{resultado.stderr}"
        )
        assert "SUCESSO" in resultado.stdout

    def test_gate_detecta_fonte_ausente(self, tmp_path, monkeypatch):
        """O gate deve falhar (exit 1) se a fonte do módulo for removida."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("g_transaction_log_lru", GATE_PATH)
        assert spec is not None and spec.loader is not None
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        raiz_fake = tmp_path
        monkeypatch.setattr(modulo, "ROOT_DIR", str(raiz_fake))

        saida = modulo.executar()
        assert saida == 1

    def test_gate_existe_e_e_executavel(self):
        assert os.path.isfile(GATE_PATH)
        with open(GATE_PATH, "r", encoding="utf-8") as f:
            import ast

            ast.parse(f.read(), filename=GATE_PATH)