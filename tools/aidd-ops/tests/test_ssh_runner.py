# -*- coding: utf-8 -*-
"""
Testes unitários para o SSH Runner determinístico (Pacote 4).
Cobertura de dry-run, lista fechada de operações, tratamento de erros e validação AST.
"""

import os
import socket
import sys
import tempfile
from unittest.mock import MagicMock, patch
import pytest

# Adicionar raiz do pacote ao path
TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_ROOT not in sys.path:
    sys.path.insert(0, TOOL_ROOT)

from src.core.ssh_runner import SSHRunner, OPERACOES_PERMITIDAS
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
        assert "apt-get update" in res.valor["comando"]

    def test_instalar_docker_dry_run(self, runner):
        res = runner.instalar_docker()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert "get.docker.com" in res.valor["comando"]

    def test_configurar_ufw_dry_run(self, runner):
        res = runner.configurar_ufw()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert "ufw allow 22/tcp" in res.valor["comando"]
        assert "ufw allow 80/tcp" in res.valor["comando"]
        assert "ufw allow 443/tcp" in res.valor["comando"]

    def test_instalar_fail2ban_dry_run(self, runner):
        res = runner.instalar_fail2ban()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert "fail2ban" in res.valor["comando"]

    def test_criar_swap_dry_run(self, runner):
        res = runner.criar_swap()
        assert res.sucesso
        assert res.valor["dry_run"] is True
        assert "mkswap" in res.valor["comando"]

    def test_executar_bootstrap_completo_dry_run(self, runner):
        res = runner.executar_bootstrap_completo()
        assert res.sucesso
        assert isinstance(res.valor, list)
        assert len(res.valor) == 5
        operacoes = [item["operacao"] for item in res.valor]
        assert operacoes == [
            "atualizar_pacotes",
            "instalar_docker",
            "configurar_ufw",
            "instalar_fail2ban",
            "criar_swap",
        ]


class TestSSHRunnerExecucaoComMock:
    @patch("src.core.ssh_runner.paramiko")
    def test_execucao_sucesso(self, mock_paramiko):
        mock_client = MagicMock()
        mock_paramiko.SSHClient.return_value = mock_client
        mock_paramiko.AutoAddPolicy.return_value = MagicMock()

        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0

        mock_stdout = MagicMock()
        mock_stdout.channel = mock_channel
        mock_stdout.read.return_value = b"Docker installed successfully"

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        mock_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        res = runner.instalar_docker()

        assert res.sucesso
        assert res.valor["dry_run"] is False
        assert res.valor["exit_code"] == 0
        assert "Docker installed" in res.valor["stdout"]
        mock_client.close.assert_called_once()

    @patch("src.core.ssh_runner.paramiko")
    def test_execucao_falha_exit_code(self, mock_paramiko):
        mock_client = MagicMock()
        mock_paramiko.SSHClient.return_value = mock_client
        mock_paramiko.AutoAddPolicy.return_value = MagicMock()

        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 1

        mock_stdout = MagicMock()
        mock_stdout.channel = mock_channel
        mock_stdout.read.return_value = b""

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"E: Package fail2ban not found"

        mock_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        res = runner.instalar_fail2ban()

        assert not res.sucesso
        assert res.codigo == "FALHA_EXECUCAO_REMOTA"
        assert res.detalhes["exit_code"] == 1

    @patch("src.core.ssh_runner.paramiko")
    def test_falha_autenticacao_sem_vazar_segredos(self, mock_paramiko):
        import paramiko as real_paramiko
        mock_client = MagicMock()
        mock_client.connect.side_effect = real_paramiko.AuthenticationException("Permission denied (publickey)")
        mock_paramiko.SSHClient.return_value = mock_client
        mock_paramiko.AutoAddPolicy.return_value = MagicMock()

        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        res = runner.atualizar_pacotes()

        assert not res.sucesso
        assert res.codigo == "FALHA_AUTENTICACAO"
        assert "chave" in res.erro.lower()

    @patch("src.core.ssh_runner.paramiko")
    def test_falha_timeout(self, mock_paramiko):
        mock_client = MagicMock()
        mock_client.connect.side_effect = socket.timeout("timed out")
        mock_paramiko.SSHClient.return_value = mock_client
        mock_paramiko.AutoAddPolicy.return_value = MagicMock()

        runner = SSHRunner(host="192.168.1.50", dry_run=False)
        res = runner.atualizar_pacotes()

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
OPERACOES_PERMITIDAS = {'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5'}
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
