# -*- coding: utf-8 -*-
"""
Testes automatizados para o Quality Gate G_HADOLINT.
Valida descoberta de binário, auditoria de Dockerfiles válidos e inválidos,
e execução ponta a ponta.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

GATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_HADOLINT.py")
_spec = importlib.util.spec_from_file_location("g_hadolint", GATE_PATH)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


class TestGHadolint(unittest.TestCase):
    def test_hadolint_ausente_reprova_com_mensagem_estruturada(self):
        """Quando o hadolint não está instalado, o gate deve reprovar informando como instalar."""
        with patch.object(gate, "encontrar_binario_hadolint", return_value=None):
            codigo = gate.escanear()
            self.assertEqual(codigo, 1)

    def test_dockerfile_invalido_reprova_com_detalhes(self):
        """Um Dockerfile com instrução não recomendada (ex: CMD shell em vez de exec) deve falhar."""
        hadolint_bin = gate.encontrar_binario_hadolint()
        if not hadolint_bin:
            self.skipTest("hadolint não disponível no ambiente para teste ao vivo")

        with tempfile.TemporaryDirectory() as tmpdir:
            df_invalido = os.path.join(tmpdir, "Dockerfile")
            with open(df_invalido, "w", encoding="utf-8") as f:
                f.write(
                    "FROM python:3.12-slim\n"
                    "HEALTHCHECK CMD python -c 'import sys; sys.exit(0)'\n"
                    "CMD python app.py\n"
                )

            code, achados = gate.auditar_dockerfile(hadolint_bin, df_invalido)
            self.assertNotEqual(code, 0)
            self.assertTrue(any(a.get("code") == "DL3025" for a in achados))

    def test_dockerfile_valido_aprova(self):
        """Um Dockerfile bem construído deve ser 100% aprovado pelo hadolint."""
        hadolint_bin = gate.encontrar_binario_hadolint()
        if not hadolint_bin:
            self.skipTest("hadolint não disponível no ambiente para teste ao vivo")

        with tempfile.TemporaryDirectory() as tmpdir:
            df_valido = os.path.join(tmpdir, "Dockerfile")
            with open(df_valido, "w", encoding="utf-8") as f:
                f.write(
                    "FROM python:3.12-slim\n"
                    "WORKDIR /app\n"
                    "COPY . /app\n"
                    'CMD ["python", "app.py"]\n'
                )

            code, achados = gate.auditar_dockerfile(hadolint_bin, df_valido)
            self.assertEqual(code, 0)
            self.assertEqual(len([a for a in achados if a.get("level") in ("error", "warning")]), 0)

    def test_gate_executa_e_aprova_no_repositorio_real(self):
        """Verifica que todos os Dockerfiles reais do ecossistema estão em conformidade estrita."""
        hadolint_bin = gate.encontrar_binario_hadolint()
        if not hadolint_bin:
            self.skipTest("hadolint não disponível no ambiente para teste ao vivo")

        codigo = gate.escanear()
        self.assertEqual(codigo, 0)

    def test_argumentos_especificos_validam_apenas_alvos(self):
        """Quando alvos específicos são informados, apenas eles são auditados."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df1 = os.path.join(tmpdir, "Dockerfile")
            with open(df1, "w", encoding="utf-8") as f:
                f.write("FROM python:3.12-slim\n")

            dfs = gate.listar_dockerfiles([df1])
            self.assertEqual(len(dfs), 1)
            self.assertEqual(dfs[0], os.path.abspath(df1))


if __name__ == "__main__":
    unittest.main()
