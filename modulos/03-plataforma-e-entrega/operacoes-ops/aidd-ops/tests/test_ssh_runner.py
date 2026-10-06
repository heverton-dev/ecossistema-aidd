# -*- coding: utf-8 -*-
"""
Testes unitários para o Runner de Hardening via Ansible (NIH #15).
Cobertura de dry-run, lista fechada de tags, pré-voo Paramiko, invocação de
ansible-playbook via subprocess e validação AST do gate.
"""

import os
import socket
import subprocess
import sys
import tempfile
from unittest.mock import MagicMock, patch
import pytest

# Adicionar raiz do pacote ao path
TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_ROOT not in sys.path:
    sys.path.insert(0, TOOL_ROOT)

from src.core.ssh_runner import SSHRunner, TAGS_PERMITIDAS, ORDEM_BOOTSTRAP
from src.core.result import Result
from gates.G_OPS_SSH import OpsSshGate


class TestSSHRunnerInicializacao:
    def test_host_vazio_lanca_erro(self):
        with pytest.raises(ValueError, match="Host obrigatorio"):
            SSHRunner(host="")

    def test_host_espacos_lanca_erro(self):
        with pytest.raises(ValueError, match="Host obrigatorio"):
            SSHRunner(host="   ")

    def test_porta_invalida_lanca_erro(self):
        with pytest.raises(ValueError, match="Porta invalida"):
            SSHRunner(host="192.168.1.100", port=70000)

        with pytest.raises(ValueError, match="Porta invalida"):
            SSHRunner(host="192.168.1.100", port=0)

    def test_inicializacao_valida(self):
        runner = SSHRunner(host="10.0.0.1", user="admin", port=2222, dry_run=True)
        assert runner.host == "10.0.0.1"
        assert runner.user == "admin"
        assert runner.port == 2222
        assert runner.dry_run is True


class TestSSHRunnerDryRun:
    @pytest.fixture
    def runner(self):
        return SSHRunner(host="test.local", user="root", dry_run=True)

    def test_operacao_nao_permitida_rejeitada(self, runner):
        res = runner.executar_operacao("comando_arbitrario_rm_rf")
        assert not res.sucesso
        assert res.codigo == "OPERACAO_NAO_PERMITIDA"

    def test_atualizar_pacotes_dry_run(self, runner):
        res = runner.atualizar_pacotes()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert res.valor["operacao"] == "atualizar_pacotes"
        assert res.valor["engine"] == "ansible"

    def test_instalar_docker_dry_run(self, runner):
        res = runner.instalar_docker()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert res.valor["operacao"] == "docker"

    def test_configurar_ufw_dry_run(self, runner):
        res = runner.configurar_ufw()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert res.valor["operacao"] == "firewall"

    def test_instalar_fail2ban_dry_run(self, runner):
        res = runner.instalar_fail2ban()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert res.valor["operacao"] == "fail2ban"

    def test_aplicar_os_hardening_dry_run(self, runner):
        res = runner.aplicar_os_hardening()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert res.valor["operacao"] == "os_hardening"
        assert "devsec.hardening" in res.valor["descricao"]

    def test_aplicar_ssh_hardening_dry_run(self, runner):
        res = runner.aplicar_ssh_hardening()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert res.valor["operacao"] == "ssh_hardening"
        assert "devsec.hardening" in res.valor["descricao"]

    def test_criar_swap_dry_run(self, runner):
        res = runner.criar_swap()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert res.valor["operacao"] == "swap"

    def test_executar_bootstrap_completo_dry_run(self, runner):
        res = runner.executar_bootstrap_completo()
        assert res.sucesso
        assert isinstance(res.valor, list)
        assert len(res.valor) == len(ORDEM_BOOTSTRAP) == 7
        operacoes = [item["operacao"] for item in res.valor]
        assert operacoes == ORDEM_BOOTSTRAP


class TestSSHRunnerPreVooParamiko:
    """Paramiko so e usado agora para o pre-voo de conectividade (testar_conexao)."""

    def test_pre_voo_dry_run_e_simulado(self):
        runner = SSHRunner(host="test.local", dry_run=True)
        res = runner.testar_conexao()
        assert res.sucesso
        assert res.valor["dry_run"] is True

    @patch("src.core.ssh_runner.paramiko")
    def test_pre_voo_sucesso(self, mock_paramiko):
        mock_client = MagicMock()
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_client.get_transport.return_value = mock_transport
        mock_paramiko.SSHClient.return_value = mock_client
        mock_paramiko.AutoAddPolicy.return_value = MagicMock()

        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        res = runner.testar_conexao()

        assert res.sucesso
        assert res.valor["conectividade"] == "ok"
        mock_client.close.assert_called_once()

    @patch("src.core.ssh_runner.paramiko")
    def test_pre_voo_falha_autenticacao_sem_vazar_segredos(self, mock_paramiko):
        import paramiko as real_paramiko
        mock_client = MagicMock()
        mock_client.connect.side_effect = real_paramiko.AuthenticationException("Permission denied (publickey)")
        mock_paramiko.SSHClient.return_value = mock_client
        mock_paramiko.AutoAddPolicy.return_value = MagicMock()

        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        res = runner.testar_conexao()

        assert not res.sucesso
        assert res.codigo == "FALHA_AUTENTICACAO"
        assert "chave" in res.erro.lower()

    @patch("src.core.ssh_runner.paramiko")
    def test_pre_voo_falha_timeout(self, mock_paramiko):
        mock_client = MagicMock()
        mock_client.connect.side_effect = socket.timeout("timed out")
        mock_paramiko.SSHClient.return_value = mock_client
        mock_paramiko.AutoAddPolicy.return_value = MagicMock()

        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        res = runner.testar_conexao()

        assert not res.sucesso
        assert res.codigo == "TIMEOUT_CONEXAO"


class TestSSHRunnerExecucaoAnsibleComMock:
    """Execucao real delega ao ansible-playbook (subprocess), apos pre-voo Paramiko."""

    def _mock_pre_voo_ok(self, monkeypatch, runner):
        monkeypatch.setattr(runner, "testar_conexao", lambda: Result.ok({"conectividade": "ok"}))

    @patch("src.core.ssh_runner.subprocess.run")
    @patch("src.core.ssh_runner.shutil.which", return_value="/usr/bin/ansible-playbook")
    def test_execucao_sucesso(self, mock_which, mock_run, monkeypatch):
        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        self._mock_pre_voo_ok(monkeypatch, runner)

        mock_run.return_value = MagicMock(returncode=0, stdout="PLAY RECAP ok", stderr="")

        res = runner.instalar_docker()

        assert res.sucesso
        assert res.valor["dry_run"] is False
        assert res.valor["exit_code"] == 0
        assert res.valor["engine"] == "ansible"
        assert mock_run.called
        argv = mock_run.call_args.args[0]
        assert argv[0] == "/usr/bin/ansible-playbook"
        assert "--tags" in argv and "docker" in argv

    @patch("src.core.ssh_runner.subprocess.run")
    @patch("src.core.ssh_runner.shutil.which", return_value="/usr/bin/ansible-playbook")
    def test_execucao_falha_exit_code(self, mock_which, mock_run, monkeypatch):
        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        self._mock_pre_voo_ok(monkeypatch, runner)

        mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="fatal: [alvo]: FAILED!")

        res = runner.instalar_fail2ban()

        assert not res.sucesso
        assert res.codigo == "FALHA_EXECUCAO_REMOTA"
        assert res.detalhes["exit_code"] == 2

    @patch("src.core.ssh_runner.shutil.which", return_value=None)
    def test_ansible_nao_instalado(self, mock_which, monkeypatch):
        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        self._mock_pre_voo_ok(monkeypatch, runner)

        res = runner.instalar_docker()

        assert not res.sucesso
        assert res.codigo == "ANSIBLE_NAO_INSTALADO"

    @patch("src.core.ssh_runner.paramiko")
    def test_pre_voo_falha_bloqueia_execucao_ansible(self, mock_paramiko):
        mock_client = MagicMock()
        mock_client.connect.side_effect = socket.timeout("timed out")
        mock_paramiko.SSHClient.return_value = mock_client
        mock_paramiko.AutoAddPolicy.return_value = MagicMock()

        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        res = runner.instalar_docker()

        assert not res.sucesso
        assert res.codigo == "TIMEOUT_CONEXAO"


class TestGateSshRunnerAST:
    def test_gate_aprova_codigo_limpo(self):
        gate = OpsSshGate()
        caminho_real = os.path.join(TOOL_ROOT, "src", "core", "ssh_runner.py")
        assert gate.auditar(caminho_real) == 0

    def test_gate_reprova_concatenacao_insegura(self):
        codigo_inseguro = """
import os
TAGS_PERMITIDAS = {'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5'}
def executar_malicioso(arg):
    os.system("echo " + arg)
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(codigo_inseguro)
            temp_path = f.name

        try:
            gate = OpsSshGate()
            assert gate.auditar(temp_path) == 1
            assert any("concatenacao" in err for err in gate.errors)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
