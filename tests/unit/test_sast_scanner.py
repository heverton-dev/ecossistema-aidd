# -*- coding: utf-8 -*-
"""
Testes unitários determinísticos para o SAST Scanner do ecossistema AIDD.
"""

import os
import tempfile
import unittest

from componentes.compartilhado.security.sast_scanner import SastScanner


class TestSastScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = SastScanner()

    def test_detecta_sqli_fstring(self):
        code = """
def buscar_usuario(cursor, user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            violations = self.scanner.scan_file_ast(tmp_path)
            self.assertTrue(any(v.rule_id == "aidd-sqli-fstring" for v in violations))
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_detecta_command_injection_shell_true(self):
        code = """
import subprocess

def rodar(cmd):
    subprocess.run(cmd, shell=True)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            violations = self.scanner.scan_file_ast(tmp_path)
            self.assertTrue(any(v.rule_id == "aidd-command-injection-shell-true" for v in violations))
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_detecta_deserialization_pickle(self):
        code = """
import pickle

def carregar(dados):
    return pickle.loads(dados)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            violations = self.scanner.scan_file_ast(tmp_path)
            self.assertTrue(any(v.rule_id == "aidd-insecure-deserialization" for v in violations))
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_passa_com_codigo_seguro(self):
        code = """
import json
import subprocess

def seguro(cursor, user_id):
    cursor.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})
    data = json.loads('{"ok": true}')
    subprocess.run(["echo", "hello"], shell=False)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            violations = self.scanner.scan_file_ast(tmp_path)
            self.assertEqual(len(violations), 0)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
