# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — Testes do Intake Web (Streamlit) e artefatos de deploy (Anti-NIH #19)
=============================================================================
Valida que o intake web produz o MESMO plano determinístico do CLI (zero
duplicação de lógica), que os fluxos de erro (ambíguo / não reconhecido)
são estruturados e recuperáveis, e que os artefatos de deploy (Dockerfile,
compose, env) seguem o contrato exigido pelo Coolify e pelos gates.
"""

import importlib
import json
import os
import re
import subprocess
import sys

import pytest

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_INTRAKE = os.path.join(TOOL_ROOT, "apps", "intake")
PIPELINE_SCRIPT = os.path.join(TOOL_ROOT, "scripts", "pipeline_ops.py")

sys.path.insert(0, APPS_INTRAKE)

intake_core = importlib.import_module("intake_core")
listar_nichos = intake_core.listar_nichos
gerar_plano = intake_core.gerar_plano
primeiro_erro = intake_core.primeiro_erro
plano_para_json = intake_core.plano_para_json

NICHOS_REAIS = [
    ("clinicas", "Clinica odontologica com agendamento de pacientes e WhatsApp"),
    ("delivery", "Lanchonete de delivery com cardapio e pedidos pelo WhatsApp"),
    ("farmacias", "Farmacia de manipulacao com receitas medicas e reposicao de remedios"),
    ("b2b_industrial", "Industria B2B com orcamentos tecnicos, contratos e assinatura digital"),
    ("energia_solar", "Empresa de energia solar com simulador fotovoltaico e visitas tecnicas"),
]


def _sem_temporais(plano: dict) -> dict:
    """Remove campos voláteis (timestamps) para comparação de igualdade."""
    import copy

    copia = copy.deepcopy(plano)
    copia.pop("gerado_em", None)
    for fase in ("fase_1_intake", "fase_2_curadoria", "fase_3_sizing"):
        intern = copia.get(fase)
        if intern:
            intern.pop("timestamp", None)
    return copia


def _plano_cli(texto: str, pasta: str) -> dict:
    comando = [sys.executable, PIPELINE_SCRIPT, texto, "--pasta", pasta]
    resultado = subprocess.run(
        comando, capture_output=True, text=True, timeout=30, cwd=TOOL_ROOT
    )
    assert resultado.returncode == 0, f"CLI exit {resultado.returncode}: {resultado.stdout}"
    with open(os.path.join(pasta, "PLANO-INFRAESTRUTURA.json"), "r", encoding="utf-8") as f:
        return json.load(f)


# ── Núcleo: mesmo plano do CLI, zero duplicação ──

@pytest.mark.parametrize("slug,texto", NICHOS_REAIS, ids=[n[0] for n in NICHOS_REAIS])
def test_intake_web_produz_mesmo_plano_do_cli(slug, texto, tmp_path):
    """gerar_plano (web) == pipeline_ops plan (CLI), ignorando timestamps."""
    plano_web = gerar_plano(texto)
    plano_cli = _plano_cli(texto, str(tmp_path))
    assert _sem_temporais(plano_web) == _sem_temporais(plano_cli)
    assert plano_web["fase_1_intake"]["saida"]["nicho_slug"] == slug
    assert plano_web["versao"] == "1.0.0"


def test_nicho_explicito_equivale_ao_texto():
    plano = gerar_plano("", nicho_explicito="clinicas")
    assert primeiro_erro(plano) is None
    assert plano["fase_1_intake"]["saida"]["nicho_slug"] == "clinicas"


def test_listar_nichos_catalogo():
    nichos = listar_nichos()
    assert len(nichos) == 5
    slugs = {n["slug"] for n in nichos}
    assert slugs == {"clinicas", "delivery", "farmacias", "b2b_industrial", "energia_solar"}
    assert all(n["nome_exibicao"] for n in nichos)


# ── Fluxos de erro estruturados e recuperáveis ──

def test_texto_ambiguo_estruturado_e_recuperavel():
    plano = gerar_plano("clinica de delivery de farmacia")
    erro = primeiro_erro(plano)
    assert erro is not None
    assert erro["codigo"] == "NICHO_AMBIGUO"
    candidatos = erro["detalhes"]["candidatos"]
    assert len(candidatos) >= 2
    assert all({"slug", "nome_exibicao", "palavras_bateram"} <= set(c) for c in candidatos)

    slug = candidatos[0]["slug"]
    plano_retomado = gerar_plano("", nicho_explicito=slug)
    assert primeiro_erro(plano_retomado) is None
    assert plano_retomado["fase_1_intake"]["saida"]["nicho_slug"] == slug


def test_texto_nao_reconhecido_estruturado():
    plano = gerar_plano("quero vender courses online no mercado americano")
    erro = primeiro_erro(plano)
    assert erro is not None
    assert erro["codigo"] == "NICHO_NAO_RECONHECIDO"
    assert "slugs_disponiveis" in erro["detalhes"]


def test_texto_vazio_sem_nicho_nao_reconhecido():
    erro = primeiro_erro(gerar_plano(""))
    assert erro is not None
    assert erro["codigo"] == "NICHO_NAO_RECONHECIDO"


# ── Serialização p/ download ──

def test_plano_para_json_round_trip():
    plano = gerar_plano(NICHOS_REAIS[0][1])
    lido = json.loads(plano_para_json(plano))
    assert _sem_temporais(lido) == _sem_temporais(plano)


# ── Artefatos de deploy (contrato Coolify + gates) ──

def test_dockerfile_intake_na_raiz_do_contexto():
    caminho = os.path.join(TOOL_ROOT, "Dockerfile.intake")
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()
    assert "EXPOSE 8501" in conteudo
    assert "streamlit" in conteudo
    assert "_stcore/health" in conteudo
    assert "8501" in conteudo


def test_dockerfile_nao_copia_fora_do_contexto():
    """Dockerfile deve ser raiz do contexto (Base Directory tools/aidd-ops)."""
    caminho = os.path.join(TOOL_ROOT, "Dockerfile.intake")
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()
    assert "COPY apps/intake/" in conteudo
    assert "COPY scripts/" in conteudo
    assert "COPY src/" in conteudo
    assert "COPY data/" in conteudo


def test_compose_usa_contexto_do_tool_root():
    caminho = os.path.join(APPS_INTRAKE, "docker-compose.yml")
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()
    assert "context: ../.." in conteudo
    assert "Dockerfile.intake" in conteudo
    assert "${INTAKE_PORT:-8501}:8501" in conteudo


def test_env_example_declara_porta_do_compose():
    caminho = os.path.join(APPS_INTRAKE, ".env.example")
    com_env = open(caminho, "r", encoding="utf-8").read()
    assert re.search(r"^\s*INTAKE_PORT\s*=.*8501", com_env, re.M)


def test_app_usa_intake_core_nao_replica_logica():
    conteudo = open(os.path.join(APPS_INTRAKE, "app.py"), "r", encoding="utf-8").read()
    assert "intake_core" in conteudo
    assert "gerar_plano" in conteudo
    assert "st.download_button" in conteudo
    assert "st.rerun" in conteudo


def test_requirements_declara_streamlit():
    conteudo = open(os.path.join(APPS_INTRAKE, "requirements.txt"), "r", encoding="utf-8").read()
    assert "streamlit" in conteudo
    assert "returns" in conteudo