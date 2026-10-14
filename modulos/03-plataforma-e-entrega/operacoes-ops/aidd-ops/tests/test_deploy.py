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
from core_ops.result import Result


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
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            dir_projeto = _criar_projeto_fake(tmp)
            plano_path = _gerar_plano_real(tmp, dir_projeto, dir_projeto=dir_projeto)
            orc = DeployOrchestrator(
                ambiente="clinicas",
                host="127.0.0.1",
                dominio="clinicas.local",
                plano_path=plano_path,
                dry_run=True,
            )
            res = orc.executar_deploy_completo()
        self.assertTrue(res.sucesso, res.erro if not res.sucesso else None)
        self.assertEqual(res.valor["ambiente"], "clinicas")
        self.assertEqual(res.valor["etapas_concluidas"], 6)
        self.assertIn("rollback_plan", res.valor)

    def test_sem_projeto_para_implantar_o_deploy_para_com_erro_claro(self):
        orc = DeployOrchestrator(ambiente="clinicas", host="127.0.0.1", dominio="clinicas.local", dry_run=True)
        res = orc.executar_deploy_completo()
        self.assertFalse(res.sucesso)
        self.assertEqual(res.codigo, "DIR_PROJETO_AUSENTE")

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


def _criar_projeto_fake(base_dir, servicos=("app", "nginx"), nome_projeto="app", subpasta="projeto"):
    """Projeto gerado pelo aidd-master em miniatura: o único motor de deploy implanta o compose dele."""
    import json as _json
    projeto_dir = os.path.join(base_dir, subpasta)
    os.makedirs(projeto_dir, exist_ok=True)
    with open(os.path.join(projeto_dir, "PLANO-EXECUCAO-ESTRUTURADO.json"), "w", encoding="utf-8") as f:
        _json.dump({"projeto": {"nome": nome_projeto}, "modulos": [{"slug": "principal"}]}, f)
    linhas = ["services:"]
    for nome in servicos:
        linhas += [f"  {nome}:", "    image: nginx:alpine" if nome == "nginx" else "    build: ."]
    with open(os.path.join(projeto_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    with open(os.path.join(projeto_dir, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write("FROM python:3.12-slim\n")
    return projeto_dir


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


class TestDeployStackDoProjeto(unittest.TestCase):
    """Achado real (18/09/2026): a Etapa 5 ignorava o plano carregado e implantava sempre a mesma stack fixa.
    Com o motor único `compose-nativo`, o que sobe é o compose do PRÓPRIO projeto: projetos diferentes,
    serviços diferentes."""

    def _servicos_implantados(self, dir_projeto, tmp):
        plano_path = _gerar_plano_real(tmp, dir_projeto, dir_projeto=dir_projeto)
        orc = DeployOrchestrator(ambiente="teste", host="127.0.0.1", plano_path=plano_path, dry_run=True)
        res = orc.executar_deploy_completo()
        self.assertTrue(res.sucesso, res.erro if not res.sucesso else None)
        etapa = next(e for e in res.valor["historico"] if e["etapa"] == "deploy_compose_nativo")
        return sorted(etapa["detalhes"]["servicos_iniciados"])

    def test_projetos_diferentes_implantam_servicos_diferentes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            a = _criar_projeto_fake(tmp, servicos=("api", "db"), subpasta="a")
            b = _criar_projeto_fake(tmp, servicos=("web", "worker", "cache"), subpasta="b")
            self.assertEqual(self._servicos_implantados(a, tmp), ["api", "db"])
            self.assertEqual(self._servicos_implantados(b, tmp), ["cache", "web", "worker"])

    def test_o_unico_motor_e_compose_nativo(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            dir_projeto = _criar_projeto_fake(tmp)
            plano_path = _gerar_plano_real(tmp, dir_projeto, dir_projeto=dir_projeto)
            orc = DeployOrchestrator(ambiente="teste", host="127.0.0.1", plano_path=plano_path, dry_run=True)
            res = orc.executar_deploy_completo()
            self.assertTrue(res.sucesso, res.erro if not res.sucesso else None)
            self.assertEqual(orc.motor, "compose-nativo")

    def test_outro_motor_e_recusado(self):
        orc = DeployOrchestrator(ambiente="teste", host="127.0.0.1", dry_run=True, motor="outro")
        res = orc.etapa_5_deploy_conteineres()
        self.assertFalse(res.sucesso)
        self.assertEqual(res.codigo, "MOTOR_DESCONHECIDO")


class TestDeployRealComInfraInjetada(unittest.TestCase):
    """Deploy real: o encadeamento é provado com SSH e HTTP injetados (sem VPS, sem Cloudflare)."""

    class DeployerFalso:
        def __init__(self, resultado):
            self.resultado, self.chamadas = resultado, []

        def deploy(self, dir_projeto, ambiente):
            self.chamadas.append((dir_projeto, ambiente))
            return self.resultado

    class DnsFalso:
        def __init__(self):
            self.chamadas = []

        def __call__(self, metodo, url, corpo=None, headers=None):
            self.chamadas.append(metodo)
            if metodo == "GET":
                return 200, {"success": True, "result": []}
            return 200, {"success": True, "result": {"id": "r1"}}

    def _rodar(self, resultado_deploy):
        import tempfile
        ambiente_env = {"CLOUDFLARE_API_TOKEN": "tok", "CLOUDFLARE_ZONE_ID": "z" * 32}  # pragma: allowlist secret
        deployer, dns = self.DeployerFalso(resultado_deploy), self.DnsFalso()
        with tempfile.TemporaryDirectory() as tmp:
            dir_projeto = _criar_projeto_fake(tmp)
            plano_path = _gerar_plano_real(tmp, dir_projeto, dir_projeto=dir_projeto)
            orc = DeployOrchestrator(
                ambiente="teste", host="203.0.113.10", dominio="app.exemplo.com.br", plano_path=plano_path,
                dry_run=False, http_dns=dns, fabrica_deployer=lambda host, user, port: deployer,
            )
            with patch.object(orc, "etapa_2_bootstrap_vps", return_value=Result.ok([])), \
                 patch.object(orc, "etapa_6_preflight_verificacao", return_value=Result.ok({})), \
                 patch.dict(os.environ, ambiente_env):
                res = orc.executar_deploy_completo()
        return res, deployer, dns

    def test_deploy_real_cria_dns_e_implanta_o_compose_do_projeto(self):
        res, deployer, dns = self._rodar(Result.ok({"servicos": ["app", "nginx"]}))
        self.assertTrue(res.sucesso, res.erro if not res.sucesso else None)
        self.assertEqual(dns.chamadas, ["GET", "POST"])
        self.assertEqual(len(deployer.chamadas), 1)
        self.assertEqual(deployer.chamadas[0][1], "teste")

    def test_falha_do_deploy_real_nao_vira_sucesso(self):
        res, _, _ = self._rodar(Result.fail("up falhou", codigo="COMPOSE_UP_FALHOU"))
        self.assertFalse(res.sucesso)
        self.assertEqual(res.codigo, "COMPOSE_UP_FALHOU")

    def test_dns_real_exige_a_zona(self):
        orc = DeployOrchestrator(ambiente="teste", host="1.2.3.4", dominio="app.exemplo.com.br", dry_run=False)
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "tok"}, clear=True):
            res = orc.etapa_3_configurar_dns()
        self.assertFalse(res.sucesso)
        self.assertEqual(res.codigo, "DNS_ZONA_AUSENTE")


if __name__ == "__main__":
    unittest.main()
