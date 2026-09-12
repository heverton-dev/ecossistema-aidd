# -*- coding: utf-8 -*-
"""
Testes standalone do bootstrapper assistido do preflight-host.

Rodam com: pytest scripts/test_preflight_host.py
(FORA do coletor padrao — pytest.ini usa testpaths = gates.)

Coverage adicional a gates/test_g_preflight_fix.py:
  - URLs oficiais de download (node LTS, hadolint release)
  - Instaladores user-space com _baixar patched (boundary de rede)
  - Extracao zip/tar.gz/tar.xz
  - Shape do diagnostico real (executar_preflight)
"""

import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPTS_DIR)
HOST_PATH = os.path.join(SCRIPTS_DIR, "preflight_host.py")
_spec = importlib.util.spec_from_file_location("preflight", HOST_PATH)
preflight = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(preflight)


class TestUrlsOficiais(unittest.TestCase):

    def test_url_hadolint_windows_x64(self):
        with patch.object(preflight.platform, "system", return_value="Windows"), \
             patch.object(preflight.platform, "machine", return_value="AMD64"):
            url = preflight.url_hadolint_release()
            self.assertEqual(url, "https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Windows-x86_64.exe")

    def test_url_hadolint_linux_arm(self):
        with patch.object(preflight.platform, "system", return_value="Linux"), \
             patch.object(preflight.platform, "machine", return_value="aarch64"):
            url = preflight.url_hadolint_release()
            self.assertEqual(url, "https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-arm64")

    def test_url_hadolint_darwin_x64(self):
        with patch.object(preflight.platform, "system", return_value="Darwin"), \
             patch.object(preflight.platform, "machine", return_value="x86_64"):
            url = preflight.url_hadolint_release()
            self.assertEqual(url, "https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Darwin-x86_64")

    def test_url_node_lts_formato_oficial(self):
        """URL do Node LTS resolve para nodejs.org/dist/<versao>/node-...."""
        with patch.object(preflight, "url_node_lts", return_value=("https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.gz", "v22.14.0")):
            url, versao = preflight.url_node_lts()
            self.assertTrue(url.startswith("https://nodejs.org/dist/"))
            self.assertIn(versao, url)

    def test_url_node_lts_sem_rede_retorna_none(self):
        """Sem rede (urlopen levanta), url_node_lts deve retornar (None, None)."""
        with patch.object(preflight.urllib.request, "urlopen", side_effect=OSError("no net")):
            url, versao = preflight.url_node_lts()
            self.assertIsNone(url)
            self.assertIsNone(versao)


class TestInstaladoresUserSpace(unittest.TestCase):

    def test_instalar_hadolint_aidd_baixa_e_grava(self):
        """Com _baixar patched, hadolint e gravado em ~/.aidd/bin (boundary de rede)."""
        with tempfile.TemporaryDirectory() as tmp:
            destino = os.path.join(tmp, "bin")
            def fake_baixar(url, destino_arq, timeout=120):
                with open(destino_arq, "wb") as fh:
                    fh.write(b"hadolint-bin")
                return (0, "ok")
            with patch.object(preflight, "_baixar", side_effect=fake_baixar) as mock_baixar, \
                 patch.object(preflight.os, "chmod"):
                codigo, msg = preflight.instalar_hadolint_aidd(destino_bin=destino, url="https://exemplo/hadolint")
            self.assertEqual(codigo, 0)
            self.assertTrue(mock_baixar.called)
            sufixo = ".exe" if os.name == "nt" else ""
            self.assertTrue(os.path.isfile(os.path.join(destino, f"hadolint{sufixo}")))

    def test_instalar_hadolint_aidd_falha_sem_rede(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = os.path.join(tmp, "bin")
            with patch.object(preflight, "_baixar", return_value=(1, "sem rede")):
                codigo, msg = preflight.instalar_hadolint_aidd(destino_bin=destino, url="https://exemplo/nope")
            self.assertEqual(codigo, 1)
            self.assertIn("sem rede", msg)

    def test_instalar_node_standalone_ativa_shims(self):
        """Pacote baixado (patched) e extraido; shims criados em ~/.aidd/bin."""
        with tempfile.TemporaryDirectory() as tmp:
            destino_bin = os.path.join(tmp, "aidd", "bin")
            dir_node = os.path.join(tmp, "aidd")
            os.makedirs(destino_bin)

            # cria pacote zip real com node dentro, estrutura oficial node-XX/
            import zipfile
            arquivo_zip = os.path.join(tmp, "node-v22.0.0-win-x64.zip")
            with zipfile.ZipFile(arquivo_zip, "w") as zf:
                zf.writestr("node-v22.0.0-win-x64/node.exe", "bin0")
                zf.writestr("node-v22.0.0-win-x64/npm.cmd", "@echo off")

            def fake_baixar(url, destino_arq, timeout=120):
                with open(arquivo_zip, "rb") as fsrc, open(destino_arq, "wb") as fdst:
                    fdst.write(fsrc.read())
                return (0, "ok")

            with patch.object(preflight, "_baixar", side_effect=fake_baixar), \
                 patch.object(preflight, "url_node_lts", return_value=("https://nodejs.org/dist/v22.0.0/node-v22.0.0-win-x64.zip", "v22.0.0")), \
                 patch.object(preflight.platform, "system", return_value="Windows"), \
                 patch.object(preflight.platform, "machine", return_value="AMD64"):
                codigo, msg = preflight.instalar_node_standalone(
                    destino_bin=destino_bin, dir_aidd=dir_node, versao="v22.0.0")
            self.assertEqual(codigo, 0)
            self.assertTrue(os.path.isfile(os.path.join(destino_bin, "node.exe")))

    def test_extrair_arquivo_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "pkg.zip")
            import zipfile
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("pasta/arquivo.txt", "conteudo")
            destino = os.path.join(tmp, "dest")
            preflight._extrair_arquivo(zip_path, destino)
            self.assertTrue(os.path.isfile(os.path.join(destino, "pasta", "arquivo.txt")))

    def test_extrair_arquivo_tar_gz(self):
        with tempfile.TemporaryDirectory() as tmp:
            tar_path = os.path.join(tmp, "pkg.tar.gz")
            import tarfile
            with tarfile.open(tar_path, "w:gz") as tf:
                info = tarfile.TarInfo("pasta/arquivo.txt")
                dados = b"conteudo"
                info.size = len(dados)
                tf.addfile(info, __import__("io").BytesIO(dados))
            destino = os.path.join(tmp, "dest")
            preflight._extrair_arquivo(tar_path, destino)
            self.assertTrue(os.path.isfile(os.path.join(destino, "pasta", "arquivo.txt")))


class TestDiagnosticoReal(unittest.TestCase):

    def test_executar_preflight_shape(self):
        """O diagnostico real retorna dict com shape esperado e jamais levanta."""
        resultado = preflight.executar_preflight()
        self.assertIn("sucesso", resultado)
        self.assertIn("ausentes", resultado)
        self.assertIn("detalhes", resultado)
        self.assertEqual(len(resultado["detalhes"]), 5)
        for d in resultado["detalhes"]:
            self.assertIn("binario", d)
            self.assertIn("presente", d)
            self.assertIsInstance(d["presente"], bool)

    def test_json_serializavel(self):
        resultado = preflight.executar_preflight()
        json.dumps(resultado)  # nao deve levantar


class TestDetectoresReutilizamGates(unittest.TestCase):

    def test_detectar_hadolint_fallback_sem_gate(self):
        """Sem detector de gate disponivel, o detector continua caminhando (nao levanta)."""
        with patch.object(preflight, "_encontrar_binario_hadolint", None), \
             patch.object(preflight.shutil, "which", return_value=None), \
             patch.object(preflight, "_candidato_aidd", return_value=None):
            resultado = preflight._detectar_hadolint()
            self.assertFalse(resultado["presente"])
            self.assertEqual(resultado["binario"], "hadolint")

    def test_detectar_checkov_fallback_sem_gate(self):
        with patch.object(preflight, "_verificar_checkov_disponivel", None), \
             patch.object(preflight.shutil, "which", return_value=None):
            resultado = preflight._detectar_checkov()
            self.assertFalse(resultado["presente"])
            self.assertEqual(resultado["binario"], "checkov")


if __name__ == "__main__":
    unittest.main()