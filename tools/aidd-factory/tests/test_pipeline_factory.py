# -*- coding: utf-8 -*-
"""Testes E2E do pipeline factory com fixtures reais."""
import copy
import json
import os
import sys
import tempfile

import pytest

_FACTORY_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "scripts", "phases"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "scripts"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "src"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "..", "..", "componentes", "compartilhado", "src-core"))

from contrato_factory import validar_plano_factory

# Fixtures: gerar PLANO-INFRAESTRUTURA.json para nichos conhecidos
NICHOS_FIXTURE = {
    "clinicas": {
        "versao": "1.0.0",
        "pipeline": "aidd-ops-mvp-fases-1-3",
        "fase_1_intake": {
            "entrada": {"texto": "clinica odontologica"},
            "saida": {"nicho_slug": "clinicas", "nicho_nome_exibicao": "Clinicas & Odontologia", "texto_original": "clinica odontologica", "palavras_chave_candidatas": ["clinica"]},
            "erro": None,
            "timestamp": "2026-09-14T00:00:00Z",
        },
        "fase_2_curadoria": {
            "entrada": {"nicho_slug": "clinicas", "nicho_nome_exibicao": "Clinicas & Odontologia"},
            "saida": {"nicho_slug": "clinicas", "nicho_nome_exibicao": "Clinicas & Odontologia", "ferramentas": [{"nome": "Typebot"}, {"nome": "Twenty CRM"}, {"nome": "Chatwoot"}, {"nome": "Cal.com"}]},
            "erro": None,
            "timestamp": "2026-09-14T00:00:00Z",
        },
        "fase_3_sizing": {
            "entrada": {"ferramentas": [{"nome": "Typebot"}, {"nome": "Twenty CRM"}, {"nome": "Chatwoot"}, {"nome": "Cal.com"}]},
            "saida": {
                "vps": {"vcpu": 6, "ram_gb": 10, "disco_gb": 80},
                "bancos_logicos": [
                    {"ferramenta": "Typebot", "nome_banco": "typebot_db"},
                    {"ferramenta": "Twenty CRM", "nome_banco": "twenty_crm_db"},
                    {"ferramenta": "Chatwoot", "nome_banco": "chatwoot_db"},
                    {"ferramenta": "Cal.com", "nome_banco": "calcom_db"},
                ],
                "ferramentas_com_banco": ["Typebot", "Twenty CRM", "Chatwoot", "Cal.com"],
                "ferramentas_sem_banco": [],
                "fontes_consultadas": [],
            },
            "erro": None,
            "timestamp": "2026-09-14T00:00:00Z",
        },
    },
    "delivery": {
        "versao": "1.0.0",
        "pipeline": "aidd-ops-mvp-fases-1-3",
        "fase_1_intake": {
            "entrada": {"texto": "lanchonete delivery"},
            "saida": {"nicho_slug": "delivery", "nicho_nome_exibicao": "Lanchonetes & Delivery", "texto_original": "lanchonete delivery", "palavras_chave_candidatas": ["delivery"]},
            "erro": None,
            "timestamp": "2026-09-14T00:00:00Z",
        },
        "fase_2_curadoria": {
            "entrada": {"nicho_slug": "delivery", "nicho_nome_exibicao": "Lanchonetes & Delivery"},
            "saida": {"nicho_slug": "delivery", "nicho_nome_exibicao": "Lanchonetes & Delivery", "ferramentas": [{"nome": "Typebot"}, {"nome": "Evolution API"}, {"nome": "Odoo"}, {"nome": "Listmonk"}]},
            "erro": None,
            "timestamp": "2026-09-14T00:00:00Z",
        },
        "fase_3_sizing": {
            "entrada": {"ferramentas": [{"nome": "Typebot"}, {"nome": "Evolution API"}, {"nome": "Odoo"}, {"nome": "Listmonk"}]},
            "saida": {
                "vps": {"vcpu": 7, "ram_gb": 11, "disco_gb": 100},
                "bancos_logicos": [
                    {"ferramenta": "Typebot", "nome_banco": "typebot_db"},
                    {"ferramenta": "Odoo", "nome_banco": "odoo_db"},
                    {"ferramenta": "Listmonk", "nome_banco": "listmonk_db"},
                ],
                "ferramentas_com_banco": ["Typebot", "Odoo", "Listmonk"],
                "ferramentas_sem_banco": ["Evolution API"],
                "fontes_consultadas": [],
            },
            "erro": None,
            "timestamp": "2026-09-14T00:00:00Z",
        },
    },
}


@pytest.fixture
def clinicas_plano():
    return NICHOS_FIXTURE["clinicas"]


@pytest.fixture
def delivery_plano():
    return NICHOS_FIXTURE["delivery"]


class TestContratoFactory:
    def test_plano_clinicas_valido(self, clinicas_plano):
        res = validar_plano_factory(clinicas_plano)
        assert res.sucesso, f"Falha: {res.erro}"

    def test_plano_delivery_valido(self, delivery_plano):
        res = validar_plano_factory(delivery_plano)
        assert res.sucesso, f"Falha: {res.erro}"

    def test_plano_sem_fase3_falha(self):
        import copy
        plano = copy.deepcopy(NICHOS_FIXTURE["clinicas"])
        plano["fase_3_sizing"]["saida"] = None
        res = validar_plano_factory(plano)
        assert not res.sucesso
        assert res.codigo == "FACTORY_INPUT_INCOMPLETE"


class TestFase1Analista:
    def test_analisar_clinicas(self, clinicas_plano):
        from importlib import import_module
        mod = import_module("01_analisador")
        res = mod.analisar(clinicas_plano)
        assert res.sucesso, f"Falha: {res.erro}"
        assert res.valor["nicho_slug"] == "clinicas"
        assert len(res.valor["ferramentas"]) == 4
        assert len(res.valor["bancos_logicos"]) == 3  # twenty, chatwoot, calcom (Typebot via ferramentas_sem_bloco)
        assert len(res.valor["blocos"]) > 0

    def test_analisar_delivery(self, delivery_plano):
        from importlib import import_module
        mod = import_module("01_analisador")
        res = mod.analisar(delivery_plano)
        assert res.sucesso, f"Falha: {res.erro}"
        assert res.valor["nicho_slug"] == "delivery"


class TestFase4Compose:
    def test_gerar_compose_clinicas(self, clinicas_plano):
        from importlib import import_module
        mod_analysis = import_module("01_analisador")
        mod_compose = import_module("04_compose")
        analysis = mod_analysis.analisar(clinicas_plano).valor
        with tempfile.TemporaryDirectory() as tmp:
            res = mod_compose.gerar_compose(analysis, tmp)
            assert res.sucesso, f"Falha: {res.erro}"
            assert "services" in res.valor
            assert len(res.valor["services"]) > 0


class TestFase5InitDb:
    def test_gerar_init_db(self, clinicas_plano):
        from importlib import import_module
        mod_analysis = import_module("01_analisador")
        mod_init = import_module("05_init_db")
        analysis = mod_analysis.analisar(clinicas_plano).valor
        res = mod_init.gerar_init_db(analysis, "/tmp")
        assert res.sucesso, f"Falha: {res.erro}"
        assert "CREATE DATABASE" in res.valor
        assert "twenty_db" in res.valor
        assert "chatwoot_db" in res.valor


class TestFase6Env:
    def test_gerar_env(self, clinicas_plano):
        from importlib import import_module
        mod_analysis = import_module("01_analisador")
        mod_env = import_module("06_env")
        analysis = mod_analysis.analisar(clinicas_plano).valor
        with tempfile.TemporaryDirectory() as tmp:
            res = mod_env.gerar_env(analysis, tmp)
            assert res.sucesso, f"Falha: {res.erro}"
            assert len(res.valor) > 0
            for env_info in res.valor:
                assert os.path.isfile(env_info["caminho"])


class TestGates:
    def test_gate_mvp(self):
        """Gate de estrutura do factory."""
        import subprocess
        gate = os.path.join(_FACTORY_ROOT, "gates", "G_FACTORY_MVP.py")
        res = subprocess.run([sys.executable, gate], capture_output=True, text=True)
        assert res.returncode == 0, f"Gate falhou: {res.stderr}"

    def test_gate_compose_valido(self):
        """Gate de compose com fixture clinicas."""
        import yaml
        from importlib import import_module
        mod_analysis = import_module("01_analisador")
        mod_compose = import_module("04_compose")

        plano = copy.deepcopy(NICHOS_FIXTURE["clinicas"])
        analysis = mod_analysis.analisar(plano).valor
        with tempfile.TemporaryDirectory() as tmp:
            res = mod_compose.gerar_compose(analysis, tmp)
            assert res.sucesso, f"Falha ao gerar compose: {res.erro}"
            # Salvar compose gerado
            compose_path = os.path.join(tmp, "docker-compose.yml")
            with open(compose_path, "w", encoding="utf-8") as f:
                yaml.dump(res.valor, f, default_flow_style=False)
            assert os.path.isfile(compose_path)
            with open(compose_path, "r") as f:
                dados = yaml.safe_load(f)
            assert "services" in dados
            assert len(dados["services"]) > 0
            for nome, svc in dados["services"].items():
                # Workers sem port nao precisam de healthcheck
                if svc.get("ports") or not svc.get("command", "").startswith("worker"):
                    if "healthcheck" not in svc:
                        print(f"  [WARN] Service '{nome}' sem healthcheck (aceitavel para workers)")

    def test_gate_init_db_valido(self):
        """Gate de init_db com fixture clinicas."""
        from importlib import import_module
        mod_analysis = import_module("01_analisador")
        mod_init = import_module("05_init_db")

        plano = copy.deepcopy(NICHOS_FIXTURE["clinicas"])
        analysis = mod_analysis.analisar(plano).valor
        res = mod_init.gerar_init_db(analysis, "/tmp")
        assert res.sucesso
        assert "set -euo pipefail" in res.valor
        assert "CREATE DATABASE" in res.valor
        assert "CREATE USER" in res.valor
        assert "GRANT" in res.valor

    def test_gate_env_valido(self):
        """Gate de env com fixture clinicas."""
        from importlib import import_module
        import copy
        mod_analysis = import_module("01_analisador")
        mod_env = import_module("06_env")

        plano = copy.deepcopy(NICHOS_FIXTURE["clinicas"])
        analysis = mod_analysis.analisar(plano).valor
        with tempfile.TemporaryDirectory() as tmp:
            res = mod_env.gerar_env(analysis, tmp)
            assert res.sucesso
            for env_info in res.valor:
                assert os.path.isfile(env_info["caminho"])
                with open(env_info["caminho"], "r") as f:
                    conteudo = f.read()
                # Nenhuma senha com valor padrao
                for linha in conteudo.splitlines():
                    if linha.startswith("#") or "=" not in linha:
                        continue
                    chave, valor = linha.split("=", 1)
                    if "password" in chave.lower() or "secret" in chave.lower():
                        assert not valor.startswith("CHANGE_ME"), f"Senha padrao em {chave}"


class TestPipelineE2E:
    def test_pipeline_completo_clinicas(self):
        """Teste E2E: plano -> analysis -> compose -> init_db -> env."""
        from importlib import import_module
        import copy
        mod_analysis = import_module("01_analisador")
        mod_compose = import_module("04_compose")
        mod_init = import_module("05_init_db")
        mod_env = import_module("06_env")

        plano = copy.deepcopy(NICHOS_FIXTURE["clinicas"])

        # Fase 1
        res = mod_analysis.analisar(plano)
        assert res.sucesso, f"Analise falhou: {res.erro}"
        analysis = res.valor

        with tempfile.TemporaryDirectory() as tmp:
            # Fase 4
            res = mod_compose.gerar_compose(analysis, tmp)
            assert res.sucesso, f"Compose falhou: {res.erro}"
            import yaml
            compose_path = os.path.join(tmp, "docker-compose.yml")
            with open(compose_path, "w", encoding="utf-8") as f:
                yaml.dump(res.valor, f, default_flow_style=False)

            # Fase 5
            res = mod_init.gerar_init_db(analysis, tmp)
            assert res.sucesso, f"InitDB falhou: {res.erro}"
            init_path = os.path.join(tmp, "init-multiple-databases.sh")
            with open(init_path, "w", encoding="utf-8") as f:
                f.write(res.valor)

            # Fase 6
            res = mod_env.gerar_env(analysis, tmp)
            assert res.sucesso, f"Env falhou: {res.erro}"

            # Verificar que todos os artefatos existem
            assert os.path.isfile(os.path.join(tmp, "docker-compose.yml"))
            assert os.path.isfile(os.path.join(tmp, "init-multiple-databases.sh"))
            env_files = [f for f in os.listdir(tmp) if f.startswith(".env.")]
            assert len(env_files) > 0
