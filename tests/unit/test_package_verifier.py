# -*- coding: utf-8 -*-
"""
Testes determinísticos do validador de pacotes e anti-alucinação.
"""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "componentes", "compartilhado", "src-core"))

from package_verifier import (
    PackageVerifier,
    _levenshtein_distance,
)


class TestPackageVerifier(unittest.TestCase):
    def setUp(self):
        self.verifier = PackageVerifier()

    def test_levenshtein(self):
        self.assertEqual(_levenshtein_distance("requests", "requests"), 0)
        self.assertEqual(_levenshtein_distance("requsts", "requests"), 1)
        self.assertEqual(_levenshtein_distance("pydantic", "pyndatic"), 2)

    def test_pacote_confiado_aprovado(self):
        ok, motivo = self.verifier.verify_package("requests")
        self.assertTrue(ok)
        self.assertIn("confiado", motivo)

    def test_detecta_typosquatting(self):
        # 'requsts' similar a 'requests'
        ok, motivo = self.verifier.verify_package("requsts")
        self.assertFalse(ok)
        self.assertIn("typosquatting", motivo)
        self.assertIn("requests", motivo)

    def test_detecta_slopsquatting_padroes(self):
        ok, motivo = self.verifier.verify_package("jwt-official")
        self.assertFalse(ok)
        self.assertIn("slopsquatting", motivo)

        ok, motivo = self.verifier.verify_package("custom-auth-helper")
        self.assertFalse(ok)
        self.assertIn("slopsquatting", motivo)

    def test_lista_requirements_com_violacoes(self):
        candidatos = ["requests", "requsts", "pydantic", "fastapi-patched"]
        violacoes = self.verifier.verify_requirements_list(candidatos)
        self.assertEqual(len(violacoes), 2)
        self.assertTrue(any("requsts" in v for v in violacoes))
        self.assertTrue(any("fastapi-patched" in v for v in violacoes))


if __name__ == "__main__":
    unittest.main()
