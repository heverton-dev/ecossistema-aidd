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

    # Carregar nicho spec
    res_spec = _carregar_nicho_spec(nicho_slug)
    if not res_spec.sucesso:
        return res_spec
    nicho_spec = res_spec.valor

    # Carregar requisitos
    requisitos = _carregar_requisitos()

    # Mapear componentes
    blocos = _mapear_blocos(nicho_spec)
    bancos = _mapear_bancos(nicho_spec)
    ferramentas_com_req = _mapear_ferramentas_com_requisitos(ferramentas, requisitos)

    analysis = {
        "nicho_slug": nicho_slug,
        "nicho_nome_exibicao": nicho_nome,
        "ferramentas": ferramentas_com_req,
        "bancos_logicos": bancos,
        "blocos": blocos,
        "vps": sizing["vps"],
        "portas_host": nicho_spec.get("portas_host", {}),
        "ferramentas_sem_bloco": nicho_spec.get("ferramentas_sem_bloco", []),
    }

    return Result.ok(analysis)
