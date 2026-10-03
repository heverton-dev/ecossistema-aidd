# -*- coding: utf-8 -*-
"""Ticket 16 (D1 / DoD 7): o aidd-ops gera infra para qualquer app.

Na continuação do fluxo 01, `ops plan "Provisionar infraestrutura para Gestao
Tarefas" --pasta <projeto>` reprovava com `NICHO_NAO_RECONHECIDO`: o ops tentava
adivinhar um nicho pelo texto. Agora ele lê o ticket de ops e o `perfil_app` da
planta (`HANDOFF_PLANNER_ENGINE.json`, contrato C2) e monta Dockerfile,
docker-compose.yml, deploy.sh e nginx a partir das peças `moldes/infra/*` do
almoxarifado (`obter_peca`). O nicho vira atalho opcional.

Os testes rodam o comando real (`python ecossistema.py ops plan ...`, o mesmo da
continuação do E2E) em subprocesso e leem o exit code do próprio processo.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[3]
CATALOGO = RAIZ / "componentes" / "compartilhado" / "CATALOGO.json"
TEXTO_CONTINUACAO = "Provisionar infraestrutura para Gestao Tarefas"

PECAS_OPS = (
    "moldes/infra/Dockerfile",
    "moldes/infra/docker-compose.yml",
    "moldes/infra/deploy.sh",
    "moldes/infra/nginx/nginx.conf",
)

PERFIL_POSTGRES_COM_FILA = {
    "modulos": ["tarefas", "projetos"],
    "entidades": ["tarefas.Tarefa", "projetos.Projeto"],
    "banco": "postgresql",
    "filas": ["notificacoes"],
    "integracoes_externas": ["smtp"],
    "rotas_quarteto": ["/api", "/docs", "/webhook", "/mcp", "/docs/guia"],
    "portas": [8000],
}

PERFIL_SQLITE_SEM_FILA = {
    "modulos": ["nucleo"],
    "entidades": ["nucleo.RegistroPrincipal"],
    "banco": "sqlite_wal",
    "filas": [],
    "integracoes_externas": [],
    "rotas_quarteto": ["/api", "/docs", "/webhooks", "/mcp"],
    "portas": [3000],
}


# ---------------------------------------------------------------------------
# Apoio
# ---------------------------------------------------------------------------

def _peca(nome: str) -> dict:
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    for peca in catalogo["pecas"]:
        if peca["nome"] == nome:
            return peca
    raise AssertionError(f"peça {nome} ausente do CATALOGO.json")


def _texto_peca(nome: str) -> str:
    return (RAIZ / _peca(nome)["caminho"]).read_text(encoding="utf-8")


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _sha_catalogo(nome: str) -> str:
    return _peca(nome)["sha256"].split("sha256-", 1)[-1]


def _ticket_ops(perfil: dict) -> dict:
    return {
        "id": "TCK-OPS",
        "ferramenta_destino": "aidd-ops",
        "entrada": {
            "perfil_app": perfil,
            "servicos_declarados": [{"nome": m, "slug": m} for m in perfil["modulos"]],
            "dependencias": ["TCK-ENTERPRISE"],
        },
        "saida_esperada": "Infra gerada a partir do perfil do app",
        "pecas_do_almoxarifado": list(PECAS_OPS),
        "criterio_de_aceite": "docker-compose.yml lista os servicos de perfil_app",
    }


def _projeto(base: Path, nome: str, perfil: dict, tickets: list | None = None) -> Path:
    """Pasta de projeto com a planta (C2) que o planner grava de verdade."""
    pasta = base / nome
    pasta.mkdir(parents=True)
    handoff = {
        "versao_schema": "1.0.0",
        "fluxo_alvo": 1,
        "metadados_projeto": {
            "nome": "Gestao Tarefas",
            "slug": "gestao-tarefas",
            "dominio": "produtividade",
            "descricao": "App generico fora dos nichos fixos",
        },
        "tickets": tickets if tickets is not None else [
            {
                "id": "TCK-MASTER",
                "ferramenta_destino": "aidd-master",
                "entrada": {},
                "saida_esperada": "monolito",
                "pecas_do_almoxarifado": [],
                "criterio_de_aceite": "quarteto sobe",
            },
            _ticket_ops(perfil),
        ],
        "perfil_app": perfil,
    }
    (pasta / "HANDOFF_PLANNER_ENGINE.json").write_text(
        json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return pasta


def _ops_plan(pasta: Path, *extra: str, texto: str = TEXTO_CONTINUACAO):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, "ecossistema.py", "ops", "plan", texto, "--pasta", str(pasta), *extra],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=180,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _servicos(pasta: Path) -> dict:
    return yaml.safe_load((pasta / "docker-compose.yml").read_text(encoding="utf-8"))["services"]


@pytest.fixture(scope="module")
def dois_projetos(tmp_path_factory):
    base = tmp_path_factory.mktemp("ops_infra_generica")
    pasta_a = _projeto(base, "app_postgres_fila", PERFIL_POSTGRES_COM_FILA)
    pasta_b = _projeto(base, "app_sqlite", PERFIL_SQLITE_SEM_FILA)
    return {
        "a": (pasta_a, *_ops_plan(pasta_a)),
        "b": (pasta_b, *_ops_plan(pasta_b)),
    }


# ---------------------------------------------------------------------------
# Entrada pelo perfil do app (o nicho deixa de ser obrigatório)
# ---------------------------------------------------------------------------

def test_ops_plan_aceita_app_generico_pelos_dois_perfis(dois_projetos):
    for chave in ("a", "b"):
        pasta, codigo, saida = dois_projetos[chave]
        assert codigo == 0, f"perfil {chave}: exit {codigo}\n{saida}"
        assert "NICHO_NAO_RECONHECIDO" not in saida


def test_plano_registra_origem_pelo_perfil_e_nao_por_nicho(dois_projetos):
    pasta, codigo, _ = dois_projetos["a"]
    assert codigo == 0
    plano = json.loads((pasta / "PLANO-INFRAESTRUTURA.json").read_text(encoding="utf-8"))
    intake = plano["fase_1_intake"]
    assert intake["erro"] is None
    assert intake["saida"]["nicho_slug"] == "perfil_gestao_tarefas"
    nomes = [f["nome"] for f in plano["fase_2_curadoria"]["saida"]["ferramentas"]]
    assert nomes == ["app", "nginx", "db", "fila"]
    sizing = plano["fase_3_sizing"]["saida"]
    assert sizing["bancos_logicos"] == [{"ferramenta": "app", "nome_banco": "gestao_tarefas"}]


# ---------------------------------------------------------------------------
# Serviços gerados seguem o perfil
# ---------------------------------------------------------------------------

def test_servicos_do_compose_mudam_conforme_o_perfil(dois_projetos):
    servicos_a = _servicos(dois_projetos["a"][0])
    servicos_b = _servicos(dois_projetos["b"][0])
    assert set(servicos_a) == {"app", "nginx", "db", "fila"}
    assert set(servicos_b) == {"app", "nginx"}
    assert set(servicos_a) != set(servicos_b)


def test_compose_liga_banco_fila_modulos_e_porta_do_perfil(dois_projetos):
    servicos = _servicos(dois_projetos["a"][0])
    app = servicos["app"]
    env = dict(item.split("=", 1) for item in app["environment"])
    assert env["PORT"] == "8000"
    assert env["DATABASE_URL"].startswith("postgresql://")
    assert env["DATABASE_URL"].endswith("@db:5432/gestao_tarefas")
    assert env["REDIS_URL"] == "redis://fila:6379/0"
    assert env["AIDD_FILAS"] == "notificacoes"
    assert env["AIDD_MODULOS"] == "tarefas,projetos"
    assert env["AIDD_INTEGRACOES_EXTERNAS"] == "smtp"
    assert "8000" in " ".join(app["healthcheck"]["test"])
    assert set(app["depends_on"]) == {"db", "fila"}
    assert servicos["db"]["image"].startswith("postgres:")
    assert servicos["fila"]["image"].startswith("redis:")

    sqlite = _servicos(dois_projetos["b"][0])["app"]
    env_b = dict(item.split("=", 1) for item in sqlite["environment"])
    assert env_b["PORT"] == "3000"
    assert "DATABASE_URL" not in env_b and "REDIS_URL" not in env_b
    assert "depends_on" not in sqlite


def test_compose_sem_frontend_nao_sobe_servico_web(dois_projetos):
    """A planta não tem `frontend/Dockerfile`: subir `web` quebraria o build."""
    for chave in ("a", "b"):
        servicos = _servicos(dois_projetos[chave][0])
        assert "web" not in servicos
        assert "web" not in (servicos["nginx"].get("depends_on") or {})


def test_frontend_real_no_projeto_sobe_servico_web(tmp_path):
    pasta = _projeto(tmp_path, "app_com_front", PERFIL_SQLITE_SEM_FILA)
    (pasta / "frontend").mkdir()
    (pasta / "frontend" / "Dockerfile").write_text("FROM node:20-alpine\n", encoding="utf-8")
    codigo, saida = _ops_plan(pasta)
    assert codigo == 0, saida
    servicos = _servicos(pasta)
    assert set(servicos) == {"app", "nginx", "web"}
    assert "web" in servicos["nginx"]["depends_on"]
    assert "server web:3000" in (pasta / "nginx" / "nginx.conf").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tudo sai das peças do almoxarifado
# ---------------------------------------------------------------------------

def test_quatro_arquivos_de_infra_gerados(dois_projetos):
    for chave in ("a", "b"):
        pasta = dois_projetos[chave][0]
        for rel in ("Dockerfile", "docker-compose.yml", "deploy.sh",
                    "nginx/nginx.conf", "nginx/ssl/generate_ssl.py"):
            assert (pasta / rel).is_file(), f"perfil {chave}: {rel} não gerado"


def test_deploy_e_ssl_sao_copias_fieis_do_catalogo(dois_projetos):
    pasta = dois_projetos["a"][0]
    assert _sha256(pasta / "deploy.sh") == _sha_catalogo("moldes/infra/deploy.sh")
    assert _sha256(pasta / "nginx" / "ssl" / "generate_ssl.py") == _sha_catalogo(
        "moldes/infra/nginx/ssl/generate_ssl.py"
    )


def test_dockerfile_e_o_molde_do_catalogo_com_a_porta_do_perfil(dois_projetos):
    molde = _texto_peca("moldes/infra/Dockerfile")
    pasta_a, pasta_b = dois_projetos["a"][0], dois_projetos["b"][0]
    assert (pasta_a / "Dockerfile").read_text(encoding="utf-8") == molde.replace("3000", "8000")
    assert (pasta_b / "Dockerfile").read_text(encoding="utf-8") == molde


def test_compose_parte_do_molde_do_catalogo(dois_projetos):
    molde = yaml.safe_load(_texto_peca("moldes/infra/docker-compose.yml"))
    servicos = _servicos(dois_projetos["b"][0])
    assert servicos["nginx"]["image"] == molde["services"]["nginx"]["image"]
    assert servicos["nginx"]["volumes"] == molde["services"]["nginx"]["volumes"]
    assert servicos["app"]["build"] == molde["services"]["app"]["build"]
    assert servicos["app"]["healthcheck"] == molde["services"]["app"]["healthcheck"]
    gerado = yaml.safe_load((dois_projetos["b"][0] / "docker-compose.yml").read_text(encoding="utf-8"))
    assert gerado["networks"] == molde["networks"]


def test_nginx_parte_do_molde_e_aponta_para_o_app_do_perfil(dois_projetos):
    molde = _texto_peca("moldes/infra/nginx/nginx.conf")
    cabecalho = molde.splitlines()[1]
    nginx_a = (dois_projetos["a"][0] / "nginx" / "nginx.conf").read_text(encoding="utf-8")
    nginx_b = (dois_projetos["b"][0] / "nginx" / "nginx.conf").read_text(encoding="utf-8")
    assert cabecalho in nginx_a and cabecalho in nginx_b
    assert "server app:8000" in nginx_a
    assert "server app:3000" in nginx_b
    # Sem front-end: o upstream do front cai no app, nunca num host `web` inexistente.
    assert "server web:" not in nginx_a and "server web:" not in nginx_b
    # Rota canônica do Quarteto desenhada na planta ganha location própria.
    assert "location /webhook " in nginx_a
    assert "location /docs/guia " not in nginx_a  # já coberta pelo prefixo /docs


def test_saida_cita_as_pecas_consumidas(dois_projetos):
    saida = dois_projetos["a"][2]
    for nome in PECAS_OPS + ("moldes/infra/nginx/ssl/generate_ssl.py",):
        assert f"[peça] {nome}" in saida


# ---------------------------------------------------------------------------
# O ops valida os próprios tickets na entrada
# ---------------------------------------------------------------------------

def test_planta_sem_ticket_de_ops_reprova_na_entrada(tmp_path):
    pasta = _projeto(tmp_path, "sem_ticket", PERFIL_SQLITE_SEM_FILA, tickets=[])
    codigo, saida = _ops_plan(pasta)
    assert codigo == 1
    assert "TICKET_OPS_AUSENTE" in saida
    assert not (pasta / "docker-compose.yml").exists()


def test_ticket_de_ops_com_peca_fora_do_catalogo_reprova(tmp_path):
    ticket = _ticket_ops(PERFIL_SQLITE_SEM_FILA)
    ticket["pecas_do_almoxarifado"] = ["moldes/infra/nao-existe.yml"]
    pasta = _projeto(tmp_path, "peca_fantasma", PERFIL_SQLITE_SEM_FILA, tickets=[ticket])
    codigo, saida = _ops_plan(pasta)
    assert codigo == 1
    assert "TICKET_OPS_INVALIDO" in saida
    assert "moldes/infra/nao-existe.yml" in saida


def test_perfil_sem_campo_obrigatorio_reprova(tmp_path):
    perfil = {k: v for k, v in PERFIL_SQLITE_SEM_FILA.items() if k != "portas"}
    pasta = _projeto(tmp_path, "perfil_torto", perfil)
    codigo, saida = _ops_plan(pasta)
    assert codigo == 1
    assert "PERFIL_APP_INVALIDO" in saida


# ---------------------------------------------------------------------------
# Nicho: atalho opcional, comportamento antigo preservado
# ---------------------------------------------------------------------------

def test_sem_planta_o_texto_generico_ainda_cai_no_casamento_de_nicho(tmp_path):
    codigo, saida = _ops_plan(tmp_path / "sem_planta")
    assert codigo == 1
    assert "NICHO_NAO_RECONHECIDO" in saida


def test_nicho_explicito_continua_como_atalho(tmp_path):
    codigo, saida = _ops_plan(tmp_path / "atalho", "--nicho", "clinicas", texto="clinica")
    assert codigo == 0, saida
    plano = json.loads((tmp_path / "atalho" / "PLANO-INFRAESTRUTURA.json").read_text(encoding="utf-8"))
    assert plano["fase_1_intake"]["saida"]["nicho_slug"] == "clinicas"


def test_dockerfile_instala_requirements_antes_de_copiar_o_codigo(dois_projetos):
    """Achado real vindo do aidd-master (Ticket 17): Dockerfile sem `pip install -r
    requirements.txt` antes do src/ quebrava com ModuleNotFoundError no primeiro pacote
    de terceiro."""
    for chave in ("a", "b"):
        conteudo = (dois_projetos[chave][0] / "Dockerfile").read_text(encoding="utf-8")
        assert "pip install" in conteudo and "requirements.txt" in conteudo
        assert conteudo.index("pip install") < conteudo.index("COPY --chown=aidduser:aiddgroup src/")
