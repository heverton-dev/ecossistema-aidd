# -*- coding: utf-8 -*-
"""Testes unitários determinísticos do particionamento federado VSA de subgrafos."""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_CORE = os.path.join(ROOT_DIR, "componentes", "compartilhado", "src-core")
if SRC_CORE not in sys.path:
    sys.path.insert(0, SRC_CORE)

from subgrafos_federados import SubgrafoFederadoVSA, DOMINIOS_VSA


class TestSubgrafosFederados(unittest.TestCase):
    def setUp(self):
        self.fed = SubgrafoFederadoVSA(raiz_repo=ROOT_DIR)

    def test_dominios_mapeados_corretamente(self):
        dominios = self.fed.listar_dominios()
        self.assertIn("01-governanca", dominios)
        self.assertIn("triade-fluxo-pure", dominios)
        self.assertIn("triade-fluxo-open", dominios)
        self.assertIn("triade-fluxo-freedom", dominios)
        self.assertIn("fatiamento-master", dominios)
        self.assertIn("blindagem-enterprise", dominios)
        self.assertIn("operacoes-ops", dominios)
        self.assertIn("04-nucleo", dominios)
        self.assertIn("core-cli", dominios)

    def test_resolucao_de_dominio_por_caminho(self):
        d1 = self.fed.obter_dominio_de_caminho("modulos/01-governanca-e-qualidade/core/aidd-forge")
        self.assertEqual(d1, "01-governanca")

        d2 = self.fed.obter_dominio_de_caminho("modulos/02-triade-motores/fluxo-01-pure")
        self.assertEqual(d2, "triade-fluxo-pure")

        d3 = self.fed.obter_dominio_de_caminho("modulos/03-plataforma-e-entrega/fatiamento-master")
        self.assertEqual(d3, "fatiamento-master")

        d4 = self.fed.obter_dominio_de_caminho("scripts/micro_gates.py")
        self.assertEqual(d4, "core-cli")

        d_global = self.fed.obter_dominio_de_caminho("README.md")
        self.assertEqual(d_global, "global")

    def test_validacao_dominio_invalido(self):
        res = self.fed.indexar_subgrafo("dominio-fantasma")
        self.assertFalse(res["sucesso"])
        self.assertIn("não reconhecido", res["erro"])


if __name__ == "__main__":
    unittest.main()
