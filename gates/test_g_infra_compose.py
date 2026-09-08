# -*- coding: utf-8 -*-
"""
Testes automatizados para o gate G_INFRA_COMPOSE (Anti-NIH #3).
Valida integração com o scanner Checkov (scan real em compose file, detecção
de segredos/violações, ausência de scanner), detecção de colisão de portas
via PyYAML estruturado, variáveis faltantes no .env.example e pré-requisito Docker.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

GATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_INFRA_COMPOSE.py")
_spec = importlib.util.spec_from_file_location("g_infra_compose", GATE_PATH)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


class TestGInfraCompose(unittest.TestCase):
    def test_checkov_disponivel_detectado(self):
        """Verifica se o scanner Checkov está instalado e é detectado no ambiente."""
        self.assertTrue(gate.verificar_checkov_disponivel())

    def test_checkov_ausente_reprova_com_mensagem_estruturada(self):
        """Simula ausência do Checkov e garante reprovação com exit 1 e sem exceção."""
        with patch.object(gate, "verificar_checkov_disponivel", return_value=False):
            with patch("sys.stdout"):
                codigo = gate.auditar()
                self.assertEqual(codigo, 1)

    def test_docker_ausente_reprova_com_mensagem_estruturada(self):
        """Simula ausência do binário docker e garante reprovação com exit 1."""
        with patch.object(gate, "verificar_docker_disponivel", return_value=False):
            with patch("sys.stdout"):
                codigo = gate.auditar()
                self.assertEqual(codigo, 1)

    def test_checkov_scan_real_compose_valido(self):
        """Executa scan real do Checkov sobre um arquivo docker-compose válido e limpo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            compose_file = os.path.join(tmpdir, "docker-compose.yml")
            with open(compose_file, "w", encoding="utf-8") as f:
                f.write(
                    "services:\n"
                    "  web:\n"
                    "    image: nginx:alpine\n"
                    "    ports:\n"
                    "      - '8080:80'\n"
                )
            sucesso, erros = gate.executar_scan_checkov([compose_file])
            self.assertTrue(sucesso)
            self.assertEqual(len(erros), 0)

    def test_checkov_scan_real_compose_com_violacao(self):
        """Executa scan real do Checkov sobre um compose contendo credencial hardcoded e valida detecção."""
        with tempfile.TemporaryDirectory() as tmpdir:
            compose_file = os.path.join(tmpdir, "docker-compose.yml")
            with open(compose_file, "w", encoding="utf-8") as f:
                f.write(
                    "services:\n"
                    "  app:\n"
                    "    image: myapp:1.0\n"
                    "    environment:\n"
                    "      AWS_SECRET_KEY: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'\n"
                )
            sucesso, erros = gate.executar_scan_checkov([compose_file])
            self.assertFalse(sucesso)
            self.assertGreater(len(erros), 0)
            self.assertTrue(any("Checkov" in e for e in erros))

    def test_extrair_variaveis_compose(self):
        conteudo = """
services:
  app:
    image: ${APP_IMAGE:-app:latest}
    environment:
      SECRET: ${APP_SECRET:?Defina}
      NAME: $APP_NAME
"""
        vars_found = gate.extrair_variaveis_compose(conteudo)
        self.assertIn("APP_IMAGE", vars_found)
        self.assertIn("APP_SECRET", vars_found)
        self.assertIn("APP_NAME", vars_found)

    def test_extrair_portas_host_sem_colisao(self):
        conteudo = """
services:
  web:
    ports:
      - "80:80"
      - "443:443"
"""
        portas = gate.extrair_portas_host(conteudo)
        self.assertEqual(len(portas), 2)
        self.assertEqual(portas[0][1], "80")
        self.assertEqual(portas[1][1], "443")

    def test_extrair_portas_host_com_colisao(self):
        conteudo = """
services:
  web1:
    ports:
      - "8080:80"
  web2:
    ports:
      - "8080:8080"
"""
        portas = gate.extrair_portas_host(conteudo)
        resolvidas = [p[1] for p in portas]
        self.assertEqual(resolvidas.count("8080"), 2)

    def test_variavel_ausente_no_env_example(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            compose_file = os.path.join(tmpdir, "docker-compose.yml")
            env_file = os.path.join(tmpdir, ".env.example")

            with open(compose_file, "w") as f:
                f.write("services:\n  db:\n    environment:\n      KEY: ${SECRET_KEY}\n")

            with open(env_file, "w") as f:
                f.write("OTHER_VAR=value\n")

            env_dict = gate.carregar_env_example(env_file)
            with open(compose_file, "r") as f:
                conteudo = f.read()
            vars_ref = gate.extrair_variaveis_compose(conteudo)
            faltantes = vars_ref - set(env_dict.keys())
            self.assertIn("SECRET_KEY", faltantes)

    def test_gate_real_executa_com_sucesso(self):
        # Executa a auditoria completa real no ambiente atual com Checkov
        codigo = gate.auditar()
        self.assertEqual(codigo, 0)


if __name__ == "__main__":
    unittest.main()

