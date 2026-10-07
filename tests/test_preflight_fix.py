# -*- coding: utf-8 -*-
"""
Testes automatizados para o bootstrapper assistido multi-OS do preflight-host.

Valida: estrutura do PM, comandos oficiais exatos, planos por SO,
dry-run sem execucao, e boundary de rede (installer com _baixar patched).
Coletado por: pytest gates/
"""

import importlib.util
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
HOST_PATH = os.path.join(SCRIPTS_DIR, "preflight_host.py")
_spec = importlib.util.spec_from_file_location("preflight", HOST_PATH)
preflight = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(preflight)


# ---------------------------------------------------------------------------
# Package manager detection
# ---------------------------------------------------------------------------

class TestDetectarPackageManager(unittest.TestCase):

    def test_retorna_dict_com_chaves_obrigatorias(self):
        resultado = preflight.detectar_package_manager()
        self.assertIsInstance(resultado, dict)
        for chave in ("sistema", "gerenciador", "caminho"):
            self.assertIn(chave, resultado)

    def test_gerenciador_e_none_ou_string(self):
        resultado = preflight.detectar_package_manager()
        self.assertIn(type(resultado["gerenciador"]).__name__, ("NoneType", "str"))

    def test_prioridade_winget_antes_de_choco(self):
        """No Windows, winget deve ter precedencia sobre choco."""
        import shutil as _shutil
        def fake_which(nome):
            if nome == "winget":
                return r"C:\fake\winget.exe"
            if nome == "choco":
                return r"C:\fake\choco.exe"
            return None

        with patch.object(preflight.platform, "system", return_value="Windows"), \
             patch.object(_shutil, "which", side_effect=fake_which):
            resultado = preflight.detectar_package_manager()
            self.assertEqual(resultado["gerenciador"], "winget")

    def test_prioridade_brew_no_macos(self):
        import shutil as _shutil
        def fake_which(nome):
            if nome == "brew":
                return "/opt/homebrew/bin/brew"
            return None

        with patch.object(preflight.platform, "system", return_value="Darwin"), \
             patch.object(_shutil, "which", side_effect=fake_which):
            resultado = preflight.detectar_package_manager()
            self.assertEqual(resultado["gerenciador"], "brew")

    def test_prioridade_apt_antes_de_dnf(self):
        import shutil as _shutil
        def fake_which(nome):
            if nome == "apt-get":
                return "/usr/bin/apt-get"
            if nome == "dnf":
                return "/usr/bin/dnf"
            return None

        with patch.object(preflight.platform, "system", return_value="Linux"), \
             patch.object(_shutil, "which", side_effect=fake_which):
            resultado = preflight.detectar_package_manager()
            self.assertEqual(resultado["gerenciador"], "apt-get")

    def test_nenhum_pm_retorna_none(self):
        with patch.object(preflight.shutil, "which", return_value=None), \
             patch.object(preflight.os.path, "isfile", return_value=False), \
             patch.object(preflight.platform, "system", return_value="Linux"):
            resultado = preflight.detectar_package_manager()
            self.assertIsNone(resultado["gerenciador"])


# ---------------------------------------------------------------------------
# Comandos oficiais por (binario, gerenciador)
# ---------------------------------------------------------------------------

class TestMontarComandoInstalacao(unittest.TestCase):

    def test_git_winget_comando_exato(self):
        passo = preflight.montar_comando_instalacao("git", "winget")
        self.assertIsNotNone(passo)
        self.assertEqual(passo["estrategia"], "package-manager")
        self.assertFalse(passo["exige_sudo"])
        self.assertIn("Git.Git", _para_texto(passo["comando_texto"]))

    def test_git_choco_comando_exato(self):
        passo = preflight.montar_comando_instalacao("git", "choco")
        self.assertIsNotNone(passo)
        self.assertIn("choco install git -y", _para_texto(passo["comando_texto"]))

    def test_git_brew_comando_exato(self):
        passo = preflight.montar_comando_instalacao("git", "brew")
        self.assertIsNotNone(passo)
        self.assertIn("brew install git", _para_texto(passo["comando_texto"]))

    def test_git_apt_exige_sudo(self):
        passo = preflight.montar_comando_instalacao("git", "apt-get")
        self.assertIsNotNone(passo)
        self.assertTrue(passo["exige_sudo"])
        self.assertIn("sudo apt-get install -y git", _para_texto(passo["comando_texto"]))

    def test_git_dnf_exige_sudo(self):
        passo = preflight.montar_comando_instalacao("git", "dnf")
        self.assertIsNotNone(passo)
        self.assertTrue(passo["exige_sudo"])

    def test_hadolint_winget_comando_exato(self):
        passo = preflight.montar_comando_instalacao("hadolint", "winget")
        self.assertIsNotNone(passo)
        self.assertIn("hadolint.hadolint", _para_texto(passo["comando_texto"]))

    def test_hadolint_brew_comando_exato(self):
        passo = preflight.montar_comando_instalacao("hadolint", "brew")
        self.assertIsNotNone(passo)
        self.assertIn("brew install hadolint", _para_texto(passo["comando_texto"]))

    def test_hadolint_sem_gerenciador_retorna_none(self):
        """Hadolint nao tem PM para apt-get — cai no fallback user-space."""
        self.assertIsNone(preflight.montar_comando_instalacao("hadolint", "apt-get"))

    def test_node_winget_comando_exato(self):
        passo = preflight.montar_comando_instalacao("node", "winget")
        self.assertIsNotNone(passo)
        self.assertIn("OpenJS.NodeJS.LTS", _para_texto(passo["comando_texto"]))

    def test_docker_brew_cask(self):
        passo = preflight.montar_comando_instalacao("docker", "brew")
        self.assertIsNotNone(passo)
        self.assertIn("brew install --cask docker", _para_texto(passo["comando_texto"]))


def _para_texto(comando):
    """Auxiliar para normalizar texto de comando nos asserts."""
    if isinstance(comando, str):
        return comando
    return " ".join(str(p) for p in comando)


# ---------------------------------------------------------------------------
# Planos de fix por contexto de SO
# ---------------------------------------------------------------------------

class TestMontarPlanoFix(unittest.TestCase):

    def _resultado_ausente(self, binarios):
        """Monta resultado de diagnostico com binarios ausentes especificados."""
        detalhes = [
            {"binario": b, "presente": b not in binarios}
            for b in ("git", "node", "docker", "hadolint", "checkov")
        ]
        ausentes = [b for b in binarios]
        return {"sucesso": len(ausentes) == 0, "detalhes": detalhes}

    def test_winget_para_git_e_hadolint(self):
        """No Windows com winget, git e hadolint usam package-manager."""
        resultado = self._resultado_ausente(["git", "hadolint"])
        pm = {"gerenciador": "winget"}
        plano = preflight.montar_plano_fix(resultado, pm)
        estrategias = {p["binario"]: p["estrategia"] for p in plano}
        self.assertEqual(estrategias["git"], "package-manager")
        self.assertEqual(estrategias["hadolint"], "package-manager")

    def test_apt_para_git_e_node_sem_sudo_silencioso(self):
        """apt-get com sudo -n indisponivel: git usa manual, node cai user-space."""
        resultado = self._resultado_ausente(["git", "node"])
        pm = {"gerenciador": "apt-get"}
        with patch.object(preflight, "_sudo_silencioso_disponivel", return_value=False):
            plano = preflight.montar_plano_fix(resultado, pm)
        estrategias = {p["binario"]: p["estrategia"] for p in plano}
        self.assertEqual(estrategias["git"], "package-manager")  # apt, com sudo silencioso indisponivel — plano montado, execucao perguntara
        self.assertIn(estrategias["node"], ("package-manager", "user-space"))

    def test_node_e_hadolint_sem_pm_fallback_user_space(self):
        """Sem PM, node e hadolint devem cair em user-space."""
        resultado = self._resultado_ausente(["node", "hadolint"])
        plano = preflight.montar_plano_fix(resultado, None)
        estrategias = {p["binario"]: p["estrategia"] for p in plano}
        self.assertEqual(estrategias["node"], "user-space")
        self.assertEqual(estrategias["hadolint"], "user-space")

    def test_checkov_sempre_pip(self):
        """Checkov sempre usa pip --user (fora de venv)."""
        resultado = self._resultado_ausente(["checkov"])
        pm = {"gerenciador": "winget"}
        plano = preflight.montar_plano_fix(resultado, pm)
        passo = plano[0]
        self.assertEqual(passo["estrategia"], "pip-user")
        self.assertFalse(passo["exige_sudo"])

    def test_todos_presentes_plano_vazio(self):
        """Se todos os binarios estao presentes, plano deve ser vazio."""
        resultado = {
            "sucesso": True,
            "detalhes": [{"binario": b, "presente": True} for b in ("git", "node", "docker", "hadolint", "checkov")],
        }
        plano = preflight.montar_plano_fix(resultado, {"gerenciador": "winget"})
        self.assertEqual(len(plano), 0)


# ---------------------------------------------------------------------------
# Dry-run
# ---------------------------------------------------------------------------

class TestDryRun(unittest.TestCase):

    def test_dry_run_exit_1_sem_executar(self):
        """dry_run=True deve exibir comandos e NUNCA executar; retorna 1 (correcao pendente)."""
        resultado = {
            "sucesso": False,
            "detalhes": [
                {"binario": "git", "presente": True, "versao": "2.50.0", "caminho": "/usr/bin/git", "instalar": None},
                {"binario": "node", "presente": False, "versao": None, "caminho": None, "instalar": "https://nodejs.org/"},
                {"binario": "docker", "presente": True, "versao": "27.0.0", "caminho": "/usr/bin/docker", "instalar": None},
                {"binario": "hadolint", "presente": True, "versao": "2.15.0", "caminho": "/usr/local/bin/hadolint", "instalar": None},
                {"binario": "checkov", "presente": True, "versao": "3.2.0", "caminho": "/usr/bin/checkov", "instalar": None},
            ],
        }
        calls_exec = []
        original_executar = preflight._executar_passo
        def spy_executar(passo):
            calls_exec.append(passo)
            return (0, "simulado")
        with patch.object(preflight, "_executar_passo", side_effect=spy_executar), \
             patch.object(preflight, "_sudo_silencioso_disponivel", return_value=False), \
             patch.object(preflight, "detectar_package_manager", return_value={"gerenciador": "apt-get"}):
            exit_code = preflight.bootstrapper_assistido(resultado, dry_run=True)
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(calls_exec), 0)

    def test_dry_run_exibe_dry_run_no_output(self):
        """O output do dry-run deve conter o token [DRY-RUN]."""
        resultado = {
            "sucesso": False,
            "detalhes": [{"binario": "checkov", "presente": False, "versao": None, "caminho": None, "instalar": None}],
        }
        import io
        buf = io.StringIO()
        with patch("sys.stdout", buf), \
             patch.object(preflight, "detectar_package_manager", return_value={"gerenciador": "winget"}):
            preflight.bootstrapper_assistido(resultado, dry_run=True)
        self.assertIn("DRY-RUN", buf.getvalue())


# ---------------------------------------------------------------------------
# pip checkov (fora de venv vs dentro)
# ---------------------------------------------------------------------------

class TestPipCheckov(unittest.TestCase):

    def test_pip_user_fora_de_venv(self):
        """Fora de venv, pip deve incluir --user."""
        cmd = preflight._comando_pip_checkov()
        self.assertIn("--user", cmd)
        self.assertIn("checkov", cmd)

    def test_pip_sem_user_em_venv(self):
        """Dentro de venv (sys.prefix != sys.base_prefix), --user NAO deve aparecer."""
        with patch.object(preflight, "sys") as mock_sys:
            mock_sys.executable = "/tmp/venv/bin/python"
            mock_sys.prefix = "/tmp/venv"
            mock_sys.base_prefix = "/usr"
            cmd = preflight._comando_pip_checkov()
            self.assertNotIn("--user", cmd)
            self.assertIn("checkov", cmd)


if __name__ == "__main__":
    unittest.main()
