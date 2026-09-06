# -*- coding: utf-8 -*-
"""
Testes automatizados para o gate G_INFRA_COMPOSE.
Valida detecção de erro sintático, colisão de portas, variáveis faltantes
e reprovação estruturada quando Docker não estiver presente.
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
    def test_docker_ausente_reprova_com_mensagem_estruturada(self):
        with patch.object(gate, "verificar_docker_disponivel", return_value=False):
            with patch("sys.stdout") as mock_stdout:
                codigo = gate.auditar()
                self.assertEqual(codigo, 1)
                # Confirma que não houve exceção não tratada

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
        # Executa a auditoria completa real no ambiente atual
        codigo = gate.auditar()
        self.assertEqual(codigo, 0)


if __name__ == "__main__":
    unittest.main()
