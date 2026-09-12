# -*- coding: utf-8 -*-
"""
Testes reais para scripts/preflight_host.py — sem stubs falsos.
Valida deteccao de binarios reais do ambiente e estrutura de saida.
"""
import json
import os
import sys
import unittest
from unittest.mock import patch

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from preflight_host import (
    executar_preflight,
    _detectar_git,
    _detectar_node,
    _detectar_docker,
    _detectar_hadolint,
    _detectar_checkov,
    _formatar_tabela,
    _versao_de_output,
)


class TestVersaoDeOutput(unittest.TestCase):
    """Testes unitarios para extracao de versao de stdout."""

    def test_extrai_versao_padrao(self):
        self.assertEqual(_versao_de_output("git version 2.42.0"), "2.42.0")

    def test_extrai_versao_com_prefixo_v(self):
        self.assertEqual(_versao_de_output("v18.17.0"), "18.17.0")

    def test_extrai_versao_multipla_linha(self):
        out = "Some info\nDocker version 24.0.5\nBuild abc123"
        self.assertIn("24.0.5", _versao_de_output(out))

    def test_output_vazio_retorna_none(self):
        self.assertIsNone(_versao_de_output(""))

    def test_output_sem_versao_retorna_primeira_linha(self):
        result = _versao_de_output("some random text\nno version here")
        self.assertIsNotNone(result)


class TestDetectoresReais(unittest.TestCase):
    """Testes que rodam contra os binarios REAIS do ambiente."""

    def test_detectar_git_estrutura(self):
        r = _detectar_git()
        self.assertIn("binario", r)
        self.assertIn("presente", r)
        self.assertIn("caminho", r)
        self.assertIn("versao", r)
        self.assertEqual(r["binario"], "git")
        # git geralmente esta instalado em ambientes de dev
        if r["presente"]:
            self.assertIsNotNone(r["caminho"])
            self.assertTrue(os.path.isfile(r["caminho"]))

    def test_detectar_git_versao_formato(self):
        r = _detectar_git()
        if r["presente"] and r["versao"]:
            # Versao deve conter pelo menos um numero
            self.assertTrue(any(c.isdigit() for c in r["versao"]))

    def test_detectar_node_estrutura(self):
        r = _detectar_node()
        self.assertEqual(r["binario"], "node")
        self.assertIn("presente", r)
        if r["presente"]:
            self.assertIsNotNone(r["caminho"])

    def test_detectar_docker_estrutura(self):
        r = _detectar_docker()
        self.assertEqual(r["binario"], "docker")
        self.assertIn("presente", r)

    def test_detectar_hadolint_estrutura(self):
        r = _detectar_hadolint()
        self.assertEqual(r["binario"], "hadolint")
        self.assertIn("presente", r)
        # hadolint pode nao estar instalado — ok, so validamos estrutura
        if r["presente"]:
            self.assertIsNotNone(r["caminho"])

    def test_detectar_checkov_estrutura(self):
        r = _detectar_checkov()
        self.assertEqual(r["binario"], "checkov")
        self.assertIn("presente", r)

    def test_detectar_binario_ausente(self):
        """Binario fake deve retornar presente=False com instrucao de instalacao."""
        with patch("preflight_host.shutil.which", return_value=None):
            r = _detectar_git()
            self.assertFalse(r["presente"])
            self.assertIsNone(r["caminho"])
            self.assertIsNotNone(r["instalar"])


class TestExecutarPreflight(unittest.TestCase):
    """Testes para a orquestracao principal."""

    def test_resultado_estrutura(self):
        r = executar_preflight()
        self.assertIn("sucesso", r)
        self.assertIn("total", r)
        self.assertIn("presentes", r)
        self.assertIn("ausentes", r)
        self.assertIn("detalhes", r)
        self.assertIn("sistema", r)
        self.assertEqual(r["total"], 5)

    def test_sistema_metadata(self):
        r = executar_preflight()
        self.assertIn("os", r["sistema"])
        self.assertIn("arquitetura", r["sistema"])
        self.assertIn("python", r["sistema"])

    def test_detalhes_sao_dicts(self):
        r = executar_preflight()
        for d in r["detalhes"]:
            self.assertIsInstance(d, dict)
            self.assertIn("binario", d)
            self.assertIn("presente", d)


class TestFormatarTabela(unittest.TestCase):
    """Testes para formatacao de tabela."""

    def test_tabela_contem_cabecalho(self):
        r = executar_preflight()
        tabela = _formatar_tabela(r)
        self.assertIn("PREFLIGHT HOST", tabela)
        self.assertIn("Binario", tabela)
        self.assertIn("Status", tabela)

    def test_tabela_menciona_binarios(self):
        r = executar_preflight()
        tabela = _formatar_tabela(r)
        self.assertIn("git", tabela)
        self.assertIn("node", tabela)
        self.assertIn("docker", tabela)
        self.assertIn("hadolint", tabela)
        self.assertIn("checkov", tabela)

    def test_tabela_resultado_ok_quando_tudo_presente(self):
        """Se todos os detectores retornam presente=True, tabela deve mostrar OK."""
        fake = [{"binario": "x", "presente": True, "caminho": "/bin/x", "versao": "1.0", "instalar": None}]
        r = {"sucesso": True, "total": 1, "presentes": 1, "ausentes": [], "detalhes": fake, "sistema": {"os": "Linux", "arquitetura": "x86_64", "python": "3.12"}}
        tabela = _formatar_tabela(r)
        self.assertIn("[OK]", tabela)
        self.assertIn("OK", tabela)

    def test_tabela_resultado_falta_quando_ausente(self):
        fake = [{"binario": "x", "presente": False, "caminho": None, "versao": None, "instalar": "apt install x"}]
        r = {"sucesso": False, "total": 1, "presentes": 0, "ausentes": ["x"], "detalhes": fake, "sistema": {"os": "Linux", "arquitetura": "x86_64", "python": "3.12"}}
        tabela = _formatar_tabela(r)
        self.assertIn("[FALTA]", tabela)
        self.assertIn("AUSENTES", tabela)


if __name__ == "__main__":
    unittest.main()
