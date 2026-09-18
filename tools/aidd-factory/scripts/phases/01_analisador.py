# -*- coding: utf-8 -*-
"""
AIDD-Factory — Fase 1: Analisador Deterministico.

Le PLANO-INFRAESTRUTURA.json e extrai requisitos estruturados para o factory.
Cruza com templates/infra/nichos/<nicho>.json para mapear blocos construtivos.
100% deterministico — zero LLM.
"""
import json
import os
import sys

_FACTORY_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "src"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "..", "..", "componentes", "compartilhado", "src-core"))

from core.result import Result

_AIDD_OPS_ROOT = os.path.join(_FACTORY_ROOT, "..", "aidd-ops")
_NICHOS_DIR = os.path.join(_AIDD_OPS_ROOT, "templates", "infra", "nichos")
_INFRA_DIR = os.path.join(_AIDD_OPS_ROOT, "templates", "infra")
_REQUISITOS_PATH = os.path.join(_AIDD_OPS_ROOT, "data", "requisitos_recursos.json")

# Reusa o discriminador de nicho dinamico do aidd-ops (fonte unica —
# 01_intake.eh_nicho_dinamico) em vez de duplicar o prefixo "dinamico_"
# aqui. Precedente ja existente neste arquivo: _AIDD_OPS_ROOT acima ja le
# templates/data de aidd-ops diretamente.
sys.path.insert(0, os.path.join(_AIDD_OPS_ROOT, "scripts", "phases"))
from importlib import import_module as _imod  # noqa: E402
_mod_intake_ops = _imod("01_intake")


def _carregar_nicho_spec(nicho_slug: str) -> Result:
    """Carrega o nicho spec JSON de templates/infra/nichos/."""
    caminho = os.path.join(_NICHOS_DIR, f"{nicho_slug}.json")
    if not os.path.isfile(caminho):
        return Result.fail(
            f"Nicho spec nao encontrado: {caminho}",
            codigo="NICHO_SPEC_AUSENTE",
        )
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return Result.ok(json.load(f))
    except (OSError, json.JSONDecodeError) as exc:
        return Result.fail(f"Erro ao ler nicho spec: {exc}", codigo="NICHO_SPEC_INVALID")


def _carregar_requisitos() -> dict:
    """Carrega requisitos_recursos.json."""
    with open(_REQUISITOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _mapear_blocos(nicho_spec: dict) -> list:
    """Extrai blocos do nicho spec com status de existencia."""
    # O caminho no nicho spec e relativo a raiz do repo (ecossistema-aidd/)
    repo_root = os.path.normpath(os.path.join(_FACTORY_ROOT, "..", ".."))
    blocos = []
    for bloco in nicho_spec.get("blocos", []):
        caminho_relativo = bloco.get("caminho", "")
        caminho_absoluto = os.path.normpath(os.path.join(repo_root, caminho_relativo)) if caminho_relativo else ""
        existe = os.path.isdir(caminho_absoluto) if caminho_absoluto else False
        compose_path = os.path.join(caminho_absoluto, "docker-compose.yml") if existe else ""
        compose_existe = os.path.isfile(compose_path) if compose_path else False

        blocos.append({
            "slug": bloco["slug"],
            "obrigatorio": bloco.get("obrigatorio", False),
            "motivo": bloco.get("motivo", ""),
            "caminho_template": caminho_relativo,
            "compose_existe": compose_existe,
        })
    return blocos


def _mapear_bancos(nicho_spec: dict) -> list:
    """Extrai bancos logicos do nicho spec."""
    return [
        {
            "nome": b["nome"],
            "usuario": b["usuario"],
            "consumer": b.get("bloco_consumer"),
            "notas": b.get("notas", ""),
        }
        for b in nicho_spec.get("bancos_logicos", [])
    ]


def _mapear_ferramentas_com_requisitos(ferramentas: list, requisitos: dict) -> list:
    """Cruza ferramentas do plano com requisitos de recursos."""
    ferramentas_req = requisitos.get("ferramentas", {})
    resultado = []
    for f in ferramentas:
        nome = f["nome"]
        req = ferramentas_req.get(nome, {})
        resultado.append({
            "nome": nome,
            "vcpu": req.get("vcpu", 1),
            "ram_gb": req.get("ram_gb", 1),
            "disco_gb": req.get("disco_gb", 20),
            "requer_banco": req.get("requer_banco_relacional", False),
            "banco_detectado": req.get("banco_detectado"),
            "requisitos_oficiais": req.get("requisitos_oficiais", False),
        })
    return resultado


def _blocos_dinamicos(ferramentas_com_req: list) -> list:
    """Blocos de infra para um nicho dinamico (fora do catalogo fixo de 5
    nichos): baseline universal observado em TODOS os 5 nichos reais
    (traefik + postgres — ver templates/infra/nichos/*.json) em vez de
    exigir um nicho_spec.json pre-cadastrado. Postgres so entra se alguma
    ferramenta do plano de fato precisar de banco relacional (mesmo
    criterio usado no sizing, requisitos_recursos.json)."""
    repo_root = os.path.normpath(os.path.join(_FACTORY_ROOT, "..", ".."))

    def _bloco(slug, obrigatorio, motivo):
        caminho_relativo = f"tools/aidd-ops/templates/infra/{slug}/"
        caminho_absoluto = os.path.normpath(os.path.join(repo_root, caminho_relativo))
        existe = os.path.isdir(caminho_absoluto)
        compose_existe = os.path.isfile(os.path.join(caminho_absoluto, "docker-compose.yml")) if existe else False
        return {
            "slug": slug, "obrigatorio": obrigatorio, "motivo": motivo,
            "caminho_template": caminho_relativo, "compose_existe": compose_existe,
        }

    blocos = [_bloco("traefik", True, "Reverse proxy e terminacao TLS (baseline universal de todos os nichos)")]
    if any(f.get("requer_banco") for f in ferramentas_com_req):
        blocos.append(_bloco("postgres", True, "Banco centralizado — pelo menos 1 ferramenta do plano requer banco relacional"))
    return blocos


def _bancos_dinamicos(ferramentas_com_req: list) -> list:
    """Bancos logicos para um nicho dinamico: 1 entrada por ferramenta que
    o sizing (Fase 3, generico por nome) ja marcou como requer_banco —
    mesma fonte de verdade, sem depender de nicho_spec.bancos_logicos."""
    bancos = []
    for f in ferramentas_com_req:
        if not f.get("requer_banco"):
            continue
        slug = f["nome"].lower().replace(" ", "_").replace("-", "_").replace(".", "")
        bancos.append({
            "nome": f"{slug}_db",
            "usuario": f"{slug}_user",
            "consumer": None,
            "notas": "Nicho dinamico: banco derivado do sizing (Fase 3) por nome de ferramenta, sem nicho_spec fixo.",
        })
    return bancos


def analisar(plano: dict) -> Result:
    """Analisa PLANO-INFRAESTRUTURA.json e produz factory_analysis.json.

    Args:
        plano: Dicionario do PLANO-INFRAESTRUTURA.json ja validado.

    Returns:
        Result.ok(factory_analysis) ou Result.fail com codigo apropriado.
    """
    nicho_slug = plano["fase_1_intake"]["saida"]["nicho_slug"]
    nicho_nome = plano["fase_1_intake"]["saida"]["nicho_nome_exibicao"]
    ferramentas = plano["fase_2_curadoria"]["saida"]["ferramentas"]
    sizing = plano["fase_3_sizing"]["saida"]

    # Carregar requisitos e cruzar com as ferramentas do plano ANTES de
    # decidir blocos/bancos — o caminho dinamico decide o que compor a
    # partir dessa lista, nao de um nicho_spec.json fixo.
    requisitos = _carregar_requisitos()
    ferramentas_com_req = _mapear_ferramentas_com_requisitos(ferramentas, requisitos)

    if _mod_intake_ops.eh_nicho_dinamico(nicho_slug):
        # Fluxo 02 dinamico (fora dos 5 nichos fixos): compoe a partir da
        # stack ja decidida no plano, sem exigir templates/infra/nichos/<slug>.json —
        # gap documentado em docs/features/v2_arquitetura-aidd-ops-factory.md §9.1
        # ("o factory nao precisa conhecer o catalogo de nichos").
        blocos = _blocos_dinamicos(ferramentas_com_req)
        bancos = _bancos_dinamicos(ferramentas_com_req)
        portas_host = {"80": "Traefik HTTP (redirect -> HTTPS)", "443": "Traefik HTTPS"}
        ferramentas_sem_bloco = []
    else:
        res_spec = _carregar_nicho_spec(nicho_slug)
        if not res_spec.sucesso:
            return res_spec
        nicho_spec = res_spec.valor
        blocos = _mapear_blocos(nicho_spec)
        bancos = _mapear_bancos(nicho_spec)
        portas_host = nicho_spec.get("portas_host", {})
        ferramentas_sem_bloco = nicho_spec.get("ferramentas_sem_bloco", [])

    analysis = {
        "nicho_slug": nicho_slug,
        "nicho_nome_exibicao": nicho_nome,
        "ferramentas": ferramentas_com_req,
        "bancos_logicos": bancos,
        "blocos": blocos,
        "vps": sizing["vps"],
        "portas_host": portas_host,
        "ferramentas_sem_bloco": ferramentas_sem_bloco,
    }

    return Result.ok(analysis)
