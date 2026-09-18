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

    def test_gateway_generator_com_hifens_e_espacos(self):
        """Garante que ferramentas como Evolution API geram funcoes Python sintaticamente validas."""
        from core.gateway_generator import gerar_gateway
        import py_compile

        analysis = {
            "nicho_slug": "delivery",
            "nicho_nome_exibicao": "Lanchonetes & Delivery",
            "ferramentas": [
                {"nome": "Typebot"},
                {"nome": "Evolution API"},
                {"nome": "Cal.com"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            res = gerar_gateway(analysis, tmp)
            assert res.sucesso, f"Geracao do gateway falhou: {res.erro}"
            gw_dir = os.path.join(tmp, "src", "gateway")
            for arquivo in ["main.py", "models.py", "routes.py"]:
                caminho = os.path.join(gw_dir, arquivo)
                assert os.path.isfile(caminho), f"Arquivo {arquivo} ausente"
                # Deve compilar sem SyntaxError
                py_compile.compile(caminho, doraise=True)

    def test_pipeline_completo_delivery_e2e(self):
        """Teste ponta a ponta executando executar_pipeline com LLM e validacao cross-service."""
        from pipeline_factory import executar_pipeline
        import copy

        plano = copy.deepcopy(NICHOS_FIXTURE["delivery"])
        with tempfile.TemporaryDirectory() as tmp:
            plano_path = os.path.join(tmp, "PLANO-INFRAESTRUTURA.json")
            with open(plano_path, "w", encoding="utf-8") as f:
                json.dump(plano, f)
            dest = os.path.join(tmp, "output")
            codigo = executar_pipeline(plano_path, dest, incluir_llm=True)
            assert codigo == 0, "Pipeline E2E completo deve retornar exit code 0"
            assert os.path.isfile(os.path.join(dest, "FACTORY_OUTPUT.json"))
            assert os.path.isfile(os.path.join(dest, "factory_analysis.json"))
            assert os.path.isfile(os.path.join(dest, "docker-compose.yml"))
            assert os.path.isfile(os.path.join(dest, "init-multiple-databases.sh"))
            # Validar VSA e Quarteto (Studios nativos do backend)
            assert os.path.isfile(os.path.join(dest, "src", "server.py"))
            assert os.path.isfile(os.path.join(dest, "src", "static", "swagger.html"))
            assert os.path.isfile(os.path.join(dest, "src", "static", "webhook_studio.html"))
            assert os.path.isfile(os.path.join(dest, "src", "static", "mcp_studio.html"))
            assert os.path.isfile(os.path.join(dest, "src", "static", "docs.html"))
            # Lei Inviolável #11: frontend de produto é Next.js por padrão
            # (Fase 3), não mais src/static/index.html.
            assert os.path.isfile(os.path.join(dest, "frontend", "package.json"))
            assert os.path.isfile(os.path.join(dest, "frontend", "app", "layout.tsx"))
            assert not os.path.isfile(os.path.join(dest, "src", "static", "index.html"))

    def test_vsa_generator_fatias_e_quarteto(self):
        """Valida que vsa_generator gera Shared Kernel, fatias com repositorios e estúdios."""
        from core.vsa_generator import gerar_aplicacao_vsa
        import py_compile

        analysis = {
            "nicho_slug": "clinicas",
            "nicho_nome_exibicao": "Clínicas & Consultórios",
            "ferramentas": [
                {"nome": "Typebot"},
                {"nome": "Twenty CRM"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            res = gerar_aplicacao_vsa(analysis, tmp)
            assert res.sucesso, f"Geracao VSA falhou: {res.erro}"
            
            # 1. Shared Kernel
            assert os.path.isfile(os.path.join(tmp, "src", "core", "database.py"))
            assert os.path.isfile(os.path.join(tmp, "src", "core", "events.py"))
            assert os.path.isfile(os.path.join(tmp, "src", "core", "mcp_server.py"))
            
            # 2. Fatias Verticais
            for mod in ["typebot", "twenty_crm"]:
                mod_dir = os.path.join(tmp, "src", "modules", mod)
                assert os.path.isdir(mod_dir)
                for f in ["models.py", "repositories.py", "services.py", "routes.py"]:
                    f_path = os.path.join(mod_dir, f)
                    assert os.path.isfile(f_path), f"Arquivo {f} ausente na fatia {mod}"
                    py_compile.compile(f_path, doraise=True)

            # 3. Server e Quarteto Sine Qua Non
            server_path = os.path.join(tmp, "src", "server.py")
            assert os.path.isfile(server_path)
            py_compile.compile(server_path, doraise=True)

            static_dir = os.path.join(tmp, "src", "static")
            for studio in ["swagger.html", "webhook_studio.html", "mcp_studio.html", "docs.html"]:
                assert os.path.isfile(os.path.join(static_dir, studio)), f"Studio {studio} ausente"
            # Lei Inviolável #11: por padrão (frontend_stack="nextjs"),
            # gerar_aplicacao_vsa NÃO gera mais o Super-App index.html — o
            # frontend de produto é gerado por outro passo (NextJSExporter,
            # Fase 3 de pipeline_factory.py), evitando os dois frontends
            # divergentes que existiam antes para o mesmo projeto.
            assert not os.path.isfile(os.path.join(static_dir, "index.html"))

    def test_vsa_generator_index_html_explicito(self):
        """frontend_stack="python-html" continua disponível para quem pedir
        explicitamente o Super-App em HTML/CSS/JS puro (Lei #11: silêncio
        nunca é licença para gerar outra coisa, mas pedido explícito é
        honrado)."""
        from core.vsa_generator import gerar_aplicacao_vsa

        analysis = {
            "nicho_slug": "clinicas",
            "nicho_nome_exibicao": "Clínicas & Consultórios",
            "ferramentas": [{"nome": "Typebot"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            res = gerar_aplicacao_vsa(analysis, tmp, frontend_stack="python-html")
            assert res.sucesso, f"Geracao VSA falhou: {res.erro}"
            assert os.path.isfile(os.path.join(tmp, "src", "static", "index.html"))


import shutil
import subprocess

NPM_DISPONIVEL = shutil.which("npm") is not None


@pytest.mark.skipif(not NPM_DISPONIVEL, reason="npm não disponível neste ambiente")
def test_frontend_gerado_pelo_factory_compila_de_verdade():
    """Teste de fogo: o frontend Next.js gerado pela Fase 3 do pipeline
    factory precisa REALMENTE compilar (npm install && npm run build), não
    só passar em checagem estática de arquivo."""
    from pipeline_factory import executar_pipeline
    import copy

    plano = copy.deepcopy(NICHOS_FIXTURE["delivery"])
    with tempfile.TemporaryDirectory() as tmp:
        plano_path = os.path.join(tmp, "PLANO-INFRAESTRUTURA.json")
        with open(plano_path, "w", encoding="utf-8") as f:
            json.dump(plano, f)
        dest = os.path.join(tmp, "output")
        codigo = executar_pipeline(plano_path, dest, incluir_llm=True)
        assert codigo == 0

        frontend_dir = os.path.join(dest, "frontend")
        res_install = subprocess.run(
            ["npm", "install"], cwd=frontend_dir,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=300, shell=(os.name == "nt"),
        )
        assert res_install.returncode == 0, res_install.stdout + res_install.stderr

        res_build = subprocess.run(
            ["npm", "run", "build"], cwd=frontend_dir,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=300, shell=(os.name == "nt"),
        )
        assert res_build.returncode == 0, res_build.stdout + res_build.stderr
        assert os.path.isfile(os.path.join(frontend_dir, ".next", "standalone", "server.js"))
