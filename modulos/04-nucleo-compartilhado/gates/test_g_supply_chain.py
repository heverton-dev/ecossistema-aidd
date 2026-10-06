# -*- coding: utf-8 -*-
"""
Testes unitários determinísticos para o Quality Gate G_SUPPLY_CHAIN.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import gates.G_SUPPLY_CHAIN as gate
from gates.G_SUPPLY_CHAIN import (
    PACOTES_PROIBIDOS_SUPPLY_CHAIN,
    VULNERABILIDADES_CONHECIDAS,
    audit_offline_supply_chain,
    parse_requirements_file,
    main,
)



class TestGSupplyChain(unittest.TestCase):
    def test_parse_requirements_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("# Comentario\n")
            f.write("requests==2.31.0 --hash=sha256:123456\n")
            f.write("flask>=2.0.0\n")
            f.write("pyjwt[crypto]==2.8.0\n")
            tmp_path = f.name

        try:
            deps = parse_requirements_file(tmp_path)
            pkg_map = {pkg: ver for _, pkg, ver in deps}
            self.assertIn("requests", pkg_map)
            self.assertEqual(pkg_map["requests"], "2.31.0")
            self.assertIn("flask", pkg_map)
            self.assertEqual(pkg_map["flask"], "2.0.0")
            self.assertIn("pyjwt", pkg_map)
            self.assertEqual(pkg_map["pyjwt"], "2.8.0")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_detecta_pacote_proibido(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req_path = os.path.join(tmpdir, "requirements.txt")
            with open(req_path, "w", encoding="utf-8") as f:
                f.write("colorama-v2==0.1.0\n")

            erros = audit_offline_supply_chain(tmpdir)
            self.assertTrue(any("PACOTE PROIBIDO 'colorama-v2'" in err for err in erros))

    def test_detecta_vulnerabilidade_conhecida(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req_path = os.path.join(tmpdir, "requirements.txt")
            with open(req_path, "w", encoding="utf-8") as f:
                f.write("pyjwt==1.7.1\n")

            erros = audit_offline_supply_chain(tmpdir)
            self.assertTrue(any("CVE-2022-29217" in err for err in erros))

    def test_passa_com_dependencias_seguras(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            req_path = os.path.join(tmpdir, "requirements.txt")
            with open(req_path, "w", encoding="utf-8") as f:
                f.write("pyjwt==2.8.0\n")
                f.write("cryptography==42.0.5\n")

            erros = audit_offline_supply_chain(tmpdir)
            self.assertEqual(erros, [])

    def test_gate_main_reprova_com_pacote_proibido(self):
        """Lei #13: Prova que o gate morde (exit 1) se houver pacote proibido em requirements.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            req_path = os.path.join(tmpdir, "requirements.txt")
            with open(req_path, "w", encoding="utf-8") as f:
                f.write("colorama-v2==0.1.0\n")

            with patch.object(gate, "ROOT_DIR", tmpdir):
                with patch.object(gate, "audit_with_pip_audit", return_value=(True, [])):
                    codigo = gate.main()
                    self.assertEqual(codigo, 1)

    def test_gate_main_aprova_estado_atual(self):
        """Valida que o estado do repositório é aprovado (exit 0)."""
        with patch.object(gate, "audit_with_pip_audit", return_value=(True, [])):
            codigo = gate.main()
            self.assertEqual(codigo, 0)



if __name__ == "__main__":
    unittest.main()
