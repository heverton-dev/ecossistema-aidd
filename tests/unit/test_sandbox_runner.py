# -*- coding: utf-8 -*-
"""
Testes unitários determinísticos para EphemeralSandbox e sanitização de ambiente.
"""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "componentes", "compartilhado", "src-core"))

from sandbox_runner import (
    EphemeralSandbox,
    sanitizar_variaveis_ambiente,
)


class TestSandboxRunner(unittest.TestCase):
    def test_sanitizacao_remove_segredos(self):
        mock_env = {
            "PATH": "/usr/bin",
            "OPENAI_API_KEY": "sk-secret-12345",
            "DATABASE_PASSWORD": "super-secret-pass",
            "AWS_SECRET_ACCESS_KEY": "AKIA...",
            "SAFE_VAR": "normal_value",
        }
        sanitizado = sanitizar_variaveis_ambiente(mock_env)
        self.assertIn("PATH", sanitizado)
        self.assertIn("SAFE_VAR", sanitizado)
        self.assertIn("AIDD_SANDBOX", sanitizado)
        self.assertNotIn("OPENAI_API_KEY", sanitizado)
        self.assertNotIn("DATABASE_PASSWORD", sanitizado)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", sanitizado)

    def test_execucao_process_isolated_sucesso(self):
        sandbox = EphemeralSandbox(prefer_docker=False)
        cmd = [sys.executable, "-c", "import os; print(os.environ.get('AIDD_SANDBOX', '0'))"]
        res = sandbox.run(cmd, timeout_seconds=10)
        self.assertTrue(res.success)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.stdout.strip(), "1")

    def test_execucao_process_isolated_timeout(self):
        sandbox = EphemeralSandbox(prefer_docker=False)
        # Script que dorme por tempo superior ao timeout
        cmd = [sys.executable, "-c", "import time; time.sleep(3)"]
        res = sandbox.run(cmd, timeout_seconds=1)
        self.assertFalse(res.success)
        self.assertTrue(res.timed_out)


if __name__ == "__main__":
    unittest.main()
