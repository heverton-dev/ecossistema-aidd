# -*- coding: utf-8 -*-
"""
Testes unitários herméticos para o orquestrador de deploy (Pacote 9).
Valida o encadeamento determinístico das 10 fases, Fail-Fast e Rollback.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_ROOT not in sys.path:
    sys.path.insert(0, TOOL_ROOT)
if os.path.join(TOOL_ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(TOOL_ROOT, "scripts"))
if os.path.join(TOOL_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(TOOL_ROOT, "src"))

from scripts.pipeline_ops import DeployOrchestrator
from core.result import Result


class TestDeployOrchestrator(unittest.TestCase):
    def test_inicializacao(self):
        orc = DeployOrchestrator(
            ambiente="piloto-teste",
            host="127.0.0.1",
            dominio="teste.local",
            dry_run=True,
        )
        self.assertEqual(orc.ambiente, "piloto-teste")
        self.assertEqual(orc.host, "127.0.0.1")
        self.assertTrue(orc.dry_run)

    def test_deploy_dry_run_completo_sucesso(self):
        orc = DeployOrchestrator(
            ambiente="clinicas",
            host="127.0.0.1",
            dominio="clinicas.local",
            dry_run=True,
        )
        res = orc.executar_deploy_completo()
        self.assertTrue(res.sucesso)
        self.assertEqual(res.valor["ambiente"], "clinicas")
        self.assertEqual(res.valor["etapas_concluidas"], 6)
        self.assertIn("rollback_plan", res.valor)

    def test_fail_fast_quando_plano_corrompido(self):
        orc = DeployOrchestrator(
            ambiente="clinicas",
            host="127.0.0.1",
            plano_path="caminho/inexistente/plano.json",
            dry_run=True,
        )
        # Com caminho inválido explicitamente configurado, deve falhar etapa 1
        with patch("os.path.isfile", return_value=True):
            with patch("builtins.open", side_effect=IOError("Erro ao ler")):
                res = orc.executar_deploy_completo()
                self.assertFalse(res.sucesso)
                self.assertEqual(res.codigo, "PLANO_INVALIDO")
                self.assertEqual(res.detalhes["etapa_com_falha"], "validacao_plano")

    def test_fail_fast_quando_bootstrap_falha(self):
        orc = DeployOrchestrator(
            ambiente="clinicas",
            host="127.0.0.1",
            dry_run=True,
        )
        with patch.object(
            orc,
            "etapa_2_bootstrap_vps",
            return_value=Result.fail(erro="Falha de conexão SSH", codigo="SSH_ERROR")
        ):
            res = orc.executar_deploy_completo()
            self.assertFalse(res.sucesso)
            self.assertEqual(res.codigo, "SSH_ERROR")
            self.assertEqual(res.detalhes["etapa_com_falha"], "bootstrap_vps")

    def test_fail_fast_quando_dns_sem_token_em_modo_real(self):
        orc = DeployOrchestrator(
            ambiente="clinicas",
            host="1.2.3.4",
            dominio="clinicas.exemplo.com",
            dry_run=False,
        )
        with patch.dict(os.environ, {}, clear=True):
            res = orc.etapa_3_configurar_dns()
            self.assertFalse(res.sucesso)
            self.assertEqual(res.codigo, "TOKEN_DNS_MISSING")


if __name__ == "__main__":
    unittest.main()
