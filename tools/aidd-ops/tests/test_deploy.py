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


def _gerar_plano_real(tmp_path, texto: str, dir_projeto: str = None) -> str:
    """Roda o pipeline real (Fases 1-3) e devolve o caminho do
    PLANO-INFRAESTRUTURA.json gerado — mesmo mecanismo real usado por
    `ops plan`, não um plano fabricado à mão."""
    import json as _json
    sys.path.insert(0, os.path.join(TOOL_ROOT, "scripts"))
    from pipeline_ops import montar_plano_em_memoria

    resultado = montar_plano_em_memoria(texto, dir_projeto=dir_projeto)
    plano_path = os.path.join(str(tmp_path), "PLANO-INFRAESTRUTURA.json")
    with open(plano_path, "w", encoding="utf-8") as f:
        _json.dump(resultado.valor, f)
    return plano_path


class TestDeployStackDinamica(unittest.TestCase):
    """Achado real corrigido: a Etapa 5 ignorava completamente o plano
    carregado e sempre montava a mesma stack fixa (Twenty/Chatwoot/Calcom/
    Postgres/UptimeKuma, o "nicho" clínicas) via Coolify — rodar `deploy`
    para qualquer outro nicho curado implantava exatamente a mesma stack."""

    def _servicos_implantados(self, plano_path):
        orc = DeployOrchestrator(
            ambiente="teste", host="127.0.0.1", plano_path=plano_path, dry_run=True,
        )
        res = orc.executar_deploy_completo()
        self.assertTrue(res.sucesso, res.erro if not res.sucesso else None)
        etapa_deploy = next(e for e in res.valor["historico"] if e["etapa"] == "deploy_coolify")
        apps = etapa_deploy["detalhes"]["plano_stack"]["apps"]
        return sorted(a["nome_servico"] for a in apps)

    def test_stacks_diferentes_para_nichos_diferentes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            plano_clinicas = _gerar_plano_real(tmp1, "Clinica odontologica com agendamento de pacientes")
            plano_delivery = _gerar_plano_real(tmp2, "Lanchonete de delivery com cardapio pelo WhatsApp")

            servicos_clinicas = self._servicos_implantados(plano_clinicas)
            servicos_delivery = self._servicos_implantados(plano_delivery)

            self.assertNotEqual(
                servicos_clinicas, servicos_delivery,
                "deploy montou a MESMA stack para nichos diferentes — voltou a ser hardcoded",
            )


class TestDeployMonolitoComposeNativo(unittest.TestCase):
    """Motor 'compose-nativo': implanta o docker-compose.yml real do
    projeto (aidd-master), selecionado automaticamente quando o plano vem
    de `ops plan --dir-projeto`."""

    def _criar_monolito_fake(self, base_dir, nome_projeto="app"):
        projeto_dir = os.path.join(base_dir, "projeto")
        os.makedirs(projeto_dir, exist_ok=True)
        with open(os.path.join(projeto_dir, "PLANO-EXECUCAO-ESTRUTURADO.json"), "w", encoding="utf-8") as f:
            import json as _json
            _json.dump({"projeto": {"nome": nome_projeto}, "modulos": [{"slug": "principal"}]}, f)
        with open(os.path.join(projeto_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
            f.write("services:\n  app:\n    build: .\n  nginx:\n    image: nginx:alpine\n")
        with open(os.path.join(projeto_dir, "Dockerfile"), "w", encoding="utf-8") as f:
            f.write("FROM python:3.12-slim\n")
        return projeto_dir

    def test_motor_selecionado_automaticamente_para_monolito(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            dir_projeto = self._criar_monolito_fake(tmp)
            plano_path = _gerar_plano_real(tmp, dir_projeto, dir_projeto=dir_projeto)

            orc = DeployOrchestrator(ambiente="teste", host="127.0.0.1", plano_path=plano_path, dry_run=True)
            res = orc.executar_deploy_completo()

            self.assertTrue(res.sucesso, res.erro if not res.sucesso else None)
            self.assertEqual(orc.motor, "compose-nativo")
            etapa_deploy = next(e for e in res.valor["historico"] if e["etapa"] == "deploy_compose_nativo")
            self.assertEqual(sorted(etapa_deploy["detalhes"]["servicos_iniciados"]), ["app", "nginx"])

    def test_deploy_real_falha_honestamente_sem_fingir_sucesso(self):
        """Achado real corrigido: o modo não-Coolify em produção real só
        gravava um log de sucesso fake sem executar nenhum comando de
        verdade. Agora falha explicitamente (REAL_NAO_IMPLEMENTADO) em vez
        de mentir."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            dir_projeto = self._criar_monolito_fake(tmp)
            plano_path = _gerar_plano_real(tmp, dir_projeto, dir_projeto=dir_projeto)

            orc = DeployOrchestrator(
                ambiente="teste", host="127.0.0.1", plano_path=plano_path,
                dry_run=False, motor="compose-nativo", motor_explicito=True,
            )
            # Isola a etapa sob teste (5): bootstrap/DNS reais de VPS não são
            # o alvo aqui, mesmo padrão hermético já usado nesta suíte
            # (ver test_fail_fast_quando_bootstrap_falha).
            with patch.object(orc, "etapa_2_bootstrap_vps", return_value=Result.ok([])), \
                 patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "fake-token-teste"}):
                res = orc.executar_deploy_completo()
            self.assertFalse(res.sucesso)
            self.assertEqual(res.codigo, "REAL_NAO_IMPLEMENTADO")


if __name__ == "__main__":
    unittest.main()
