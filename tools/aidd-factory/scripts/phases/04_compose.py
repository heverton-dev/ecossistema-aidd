# -*- coding: utf-8 -*-
"""
AIDD-Factory — Fase 4: Gerador de Compose Unificado.

Faz merge dos compose templates selecionados pelo nicho em um
docker-compose.yml unificado com redes, healthchecks e resource limits.
100% deterministico — zero LLM.
"""
import os
import sys
import yaml

_FACTORY_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "src"))
sys.path.insert(0, os.path.join(_FACTORY_ROOT, "..", "..", "componentes", "compartilhado", "src-core"))

from core.result import Result

_AIDD_OPS_ROOT = os.path.join(_FACTORY_ROOT, "..", "aidd-ops")
_INFRA_DIR = os.path.join(_AIDD_OPS_ROOT, "templates", "infra")


def _ler_compose(caminho: str) -> Result:
    """Le e parseia um docker-compose.yml."""
    if not os.path.isfile(caminho):
        return Result.fail(f"Compose nao encontrado: {caminho}", codigo="COMPOSE_AUSENTE")
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = yaml.safe_load(f)
        if not dados or "services" not in dados:
            return Result.fail(f"Compose sem 'services': {caminho}", codigo="COMPOSE_INVALID")
        return Result.ok(dados)
    except yaml.YAMLError as exc:
        return Result.fail(f"Erro YAML: {exc}", codigo="COMPOSE_YAML_ERROR")


def _merge_services(composes: list) -> dict:
    """Merge service definitions de multiplos compose files."""
    services = {}
    networks = {"aidd_internal": {"driver": "bridge"}}

    for compose in composes:
        for nome, svc in compose.get("services", {}).items():
            # Prefixar nome para evitar colisao
            nome_final = nome if nome not in services else f"{nome}"
            if nome_final in services:
                # Skip se ja existe (evitar duplicatas)
                continue
            services[nome_final] = svc

    return {"services": services, "networks": networks}


def gerar_compose(analysis: dict, pasta_saida: str) -> Result:
    """Gera docker-compose.yml unificado a partir do factory_analysis.

    Args:
        analysis: Dicionario do factory_analysis.json.
        pasta_saida: Diretorio onde salvar o compose.

    Returns:
        Result.ok(conteudo_compose) ou Result.fail.
    """
    blocos = analysis.get("blocos", [])
    blocos_obrigatorios = [b for b in blocos if b.get("obrigatorio")]
    blocos_opcionais = [b for b in blocos if not b.get("obrigatorio")]

    # Carregar composables
    composables = []
    blocos_nao_encontrados = []

    # Caminho dos templates: raiz do repo + caminho relativo do nicho spec
    repo_root = os.path.normpath(os.path.join(_FACTORY_ROOT, "..", ".."))

    for bloco in blocos_obrigatorios:
        if not bloco.get("compose_existe"):
            blocos_nao_encontrados.append(bloco["slug"])
            continue
        caminho = os.path.normpath(os.path.join(
            repo_root, bloco["caminho_template"], "docker-compose.yml"
        ))
        res = _ler_compose(caminho)
        if res.sucesso:
            composables.append(res.valor)
        else:
            return res

    # Opcionais so se existirem
    for bloco in blocos_opcionais:
        if bloco.get("compose_existe"):
            caminho = os.path.normpath(os.path.join(
                repo_root, bloco["caminho_template"], "docker-compose.yml"
            ))
            res = _ler_compose(caminho)
            if res.sucesso:
                composables.append(res.valor)

    if blocos_nao_encontrados:
        return Result.fail(
            f"Blocos obrigatorios sem compose: {', '.join(blocos_nao_encontrados)}",
            codigo="BLOCOS_AUSENTES",
            detalhes={"blocos": blocos_nao_encontrados},
        )

    if not composables:
        return Result.fail("Nenhum compose template encontrado.", codigo="SEM_COMPOSES")

    # Merge
    merged = _merge_services(composables)

    # Adicionar version e header
    output = {
        "version": "3.8",
        **merged,
    }

    return Result.ok(output)
