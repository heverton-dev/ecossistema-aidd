#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROFILES REGISTRY — Mapeamento de rotas de destino por projeto AIDD
aidd-generator — Injetor Universal de Componentes

Replica a Secao 5 (Detalhamento dos Profiles dos 4 Projetos) do plano
mestre ORCA 3. Este worktree implementa apenas o profile 'aidd-generator'
(mesa 'feat-add-skills-mcps-rules-specs') — os demais projetos (aidd-master,
aidd-master-enterprise, aidd-forge) sao de responsabilidade de suas
proprias worktrees/mesas e nao sao resolvidos aqui.
"""

import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# MATRIZ DE PERFIS
# =============================================================================
# dest: caminho relativo ao root do projeto (template com {nome})
# mirrors: copias adicionais em outros harnesses (template com {nome})
# anchor: arquivo(s) que devem ser atualizados para refletir o componente

PROFILES: Dict[str, Dict[str, Dict[str, object]]] = {
    "aidd-generator": {
        "skill": {
            "dest": "skills/{nome}/SKILL.md",
            "mirrors": [".claude/skills/{nome}/SKILL.md"],
            "anchors": ["AGENTS.md"],
        },
        "mcp": {
            "dest": "mcps/{nome}/server.py",
            "mirrors": [],
            "anchors": ["AGENTS.md", "HARNESS-COMPAT.json"],
        },
        "rule": {
            "dest": "rules/{nome}.md",
            "mirrors": [],
            "anchors": ["AGENTS.md"],
        },
        "spec": {
            "dest": "docs/specs/{nome}.md",
            "mirrors": [],
            "anchors": ["AGENTS.md", "PLANO-EXECUCAO-ESTRUTURADO.json"],
        },
        "config": {
            "dest": "config/{nome}.json",
            "mirrors": [],
            "anchors": ["AGENTS.md"],
        },
    },
}

PROJETOS_SUPORTADOS = tuple(PROFILES.keys())


class ProjetoNaoSuportadoError(ValueError):
    """Levantado quando `alvo_projeto` nao possui profile implementado neste worktree."""


class TipoNaoSuportadoError(ValueError):
    """Levantado quando `tipo` nao existe no profile do projeto alvo."""


@dataclass
class RotaResolvida:
    """Rota fisica de destino resolvida para um componente concreto."""

    tipo: str
    nome: str
    alvo_projeto: str
    dest: str
    mirrors: List[str] = field(default_factory=list)
    anchors: List[str] = field(default_factory=list)


def resolver_rota(alvo_projeto: str, tipo: str, nome: str) -> RotaResolvida:
    """
    Resolve a rota fisica de destino (dest + mirrors + anchors) para um
    componente concreto, a partir do profile do projeto alvo.

    Args:
        alvo_projeto: nome do projeto AIDD (ex.: 'aidd-generator').
        tipo: tipo do componente ('skill', 'mcp', 'rule', 'spec', 'config').
        nome: slug do componente (kebab-case).

    Returns:
        RotaResolvida com os caminhos ja formatados com `nome`.

    Raises:
        ProjetoNaoSuportadoError: se o projeto nao tiver profile neste worktree.
        TipoNaoSuportadoError: se o tipo nao existir no profile do projeto.
    """
    profile = PROFILES.get(alvo_projeto)
    if profile is None:
        raise ProjetoNaoSuportadoError(
            f"projeto '{alvo_projeto}' nao possui profile implementado neste worktree "
            f"(suportados aqui: {PROJETOS_SUPORTADOS})"
        )

    rota_tipo = profile.get(tipo)
    if rota_tipo is None:
        raise TipoNaoSuportadoError(
            f"tipo '{tipo}' nao definido no profile de '{alvo_projeto}' "
            f"(suportados: {tuple(profile.keys())})"
        )

    return RotaResolvida(
        tipo=tipo,
        nome=nome,
        alvo_projeto=alvo_projeto,
        dest=rota_tipo["dest"].format(nome=nome),
        mirrors=[m.format(nome=nome) for m in rota_tipo["mirrors"]],
        anchors=list(rota_tipo["anchors"]),
    )


def tipos_suportados(alvo_projeto: str) -> Optional[List[str]]:
    """Lista os tipos suportados para um projeto, ou None se o projeto nao existir."""
    profile = PROFILES.get(alvo_projeto)
    if profile is None:
        return None
    return list(profile.keys())
