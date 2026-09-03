# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Injetor Universal: Contrato & Matriz de Perfis
=============================================================================
Valida payloads de InjectorRequest contra 'schema_injector_request.json' e
resolve, para cada 'tipo' de componente, os caminhos físicos de destino, os
espelhos multi-harness e as âncoras de catálogo/governança do projeto alvo.

Nota de detecção de identidade (Fase 1 do Injetor Universal): o perfil abaixo
para 'aidd-master' foi construído a partir de evidência real do repositório
(single 'src/core/mcp_server.py', âncoras 'templates/core/AGENTS.md' +
'CLAUDE.md' + 'GEMINI.md', 'src/core/intent_router.py', 'templates/agents/'),
e não do bloco JSON literal do plano mestre — que assumia 'CAPABILITIES.json'
e 'suite.db' pré-existentes e um layout 'src/core/mcp/{nome}.py' por arquivo
sem registrador central. Os dois não coincidem; este módulo é a fonte da
verdade físico-corrente, não o plano.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from result import Result
except ImportError:
    from core.result import Result


_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_injector_request.json")

TIPOS_VALIDOS: Tuple[str, ...] = ("skill", "mcp", "rule", "spec", "config", "agent")

_NOME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# ---------------------------------------------------------------------------
# Matriz de Perfis: projeto alvo -> tipo -> mapeamento de destino físico
# ---------------------------------------------------------------------------
PROFILES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "aidd-master": {
        "skill": {
            "dest": ".skills/{nome}/SKILL.md",
            "mirrors": [
                ".claude/skills/{nome}/SKILL.md",
                ".agent/skills/{nome}/SKILL.md",
                ".mimocode/skills/{nome}/SKILL.md",
                ".gemini/skills/{nome}/SKILL.md",
            ],
            "registry": "CAPABILITIES.json",
            "camada_alvo": "harness_multiplataforma",
        },
        "mcp": {
            "dest": "src/core/mcp/{nome}.py",
            "registry": "CAPABILITIES.json",
            "camada_alvo": "kernel_core",
        },
        "rule": {
            "dest": "templates/rules/{nome}.md",
            "anchors": [
                "AGENTS.md",
                "templates/core/AGENTS.md",
                "templates/core/CLAUDE.md",
                "templates/core/GEMINI.md",
            ],
            "registry": "CAPABILITIES.json",
            "camada_alvo": "governanca_regras",
        },
        "spec": {
            "dest": "docs/specs/{nome}.md",
            "registry": "CAPABILITIES.json",
            "camada_alvo": "documentacao_oficial",
        },
        "config": {
            "dest": "templates/core/config/{nome}.json",
            "registry": "CAPABILITIES.json",
            "camada_alvo": "templates_scaffold",
        },
        "agent": {
            "dest": "templates/agents/{nome}.md",
            "router_anchor": "src/core/intent_router.py",
            "registry": "CAPABILITIES.json",
            "camada_alvo": "interface_orquestracao",
        },
    }
}

PROJETOS_SUPORTADOS: Tuple[str, ...] = tuple(PROFILES.keys())


def carregar_schema() -> Dict[str, Any]:
    """Carrega o contrato JSON Schema Draft 2020-12 do disco."""
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validar_payload(payload: Dict[str, Any]) -> Result:
    """Valida um payload de InjectorRequest contra o contrato universal.

    Retorna Result.fail com código estruturado para o primeiro problema
    encontrado (campo ausente, tipo inválido, nome fora do padrão kebab-case
    ou descrição fora dos limites de tamanho); nunca lança exceção.
    """
    schema = carregar_schema()
    obrigatorios: List[str] = schema.get("required", [])

    faltantes = [c for c in obrigatorios if not str(payload.get(c, "")).strip()]
    if faltantes:
        return Result.fail(
            f"Campos obrigatórios ausentes ou vazios: {', '.join(faltantes)}",
            codigo="PAYLOAD_INCOMPLETO",
            detalhes={"faltantes": faltantes},
        )

    tipo = payload.get("tipo")
    if tipo not in TIPOS_VALIDOS:
        return Result.fail(
            f"'tipo' inválido: {tipo!r}. Valores aceitos: {', '.join(TIPOS_VALIDOS)}",
            codigo="TIPO_INVALIDO",
            detalhes={"tipo_recebido": tipo, "tipos_validos": list(TIPOS_VALIDOS)},
        )

    nome = str(payload.get("nome", ""))
    if not _NOME_RE.match(nome):
        return Result.fail(
            f"'nome' deve ser kebab-case (ex.: 'seguranca-cibernetica'): {nome!r}",
            codigo="NOME_INVALIDO",
            detalhes={"nome_recebido": nome},
        )

    descricao = str(payload.get("descricao", ""))
    if not (3 <= len(descricao) <= 500):
        return Result.fail(
            "'descricao' deve ter entre 3 e 500 caracteres.",
            codigo="DESCRICAO_INVALIDA",
            detalhes={"tamanho_recebido": len(descricao)},
        )

    return Result.ok(payload)


def obter_perfil(alvo_projeto: str, tipo: str) -> Result:
    """Resolve o mapeamento de destino de um 'tipo' para o 'alvo_projeto'."""
    if alvo_projeto not in PROFILES:
        return Result.fail(
            f"Projeto alvo sem perfil resolvido: {alvo_projeto!r}. "
            f"Suportados nesta instalação: {', '.join(PROJETOS_SUPORTADOS)}",
            codigo="PROJETO_NAO_SUPORTADO",
            detalhes={"suportados": list(PROJETOS_SUPORTADOS)},
        )

    perfil_projeto = PROFILES[alvo_projeto]
    if tipo not in perfil_projeto:
        return Result.fail(
            f"Tipo {tipo!r} sem mapeamento de destino no perfil de {alvo_projeto!r}.",
            codigo="TIPO_SEM_PERFIL",
        )

    return Result.ok(perfil_projeto[tipo])


def obter_camada_alvo(alvo_projeto: str, tipo: str) -> Optional[str]:
    """Retorna o rótulo de camada arquitetural resolvido para 'tipo', ou None."""
    resultado = obter_perfil(alvo_projeto, tipo)
    if not resultado.sucesso:
        return None
    return resultado.valor.get("camada_alvo")


def resolver_destinos(payload: Dict[str, Any], root_dir: str) -> Result:
    """Resolve caminhos absolutos de destino/espelhos/âncoras/registro para o payload.

    Não escreve nada em disco — apenas calcula os caminhos físicos finais a
    partir da matriz de perfis. A escrita transacional é responsabilidade do
    'materializador.py'.
    """
    validado = validar_payload(payload)
    if not validado.sucesso:
        return validado

    alvo_projeto = payload["alvo_projeto"]
    tipo = payload["tipo"]
    nome = payload["nome"]

    perfil_result = obter_perfil(alvo_projeto, tipo)
    if not perfil_result.sucesso:
        return perfil_result

    perfil = perfil_result.valor
    root_dir = os.path.abspath(root_dir)

    def _abs(rel_template: str) -> str:
        return os.path.join(root_dir, *rel_template.format(nome=nome).split("/"))

    dest_principal = _abs(perfil["dest"])
    mirrors = [_abs(m) for m in perfil.get("mirrors", [])]
    anchors = [_abs(a) for a in perfil.get("anchors", [])]
    router_anchor = _abs(perfil["router_anchor"]) if "router_anchor" in perfil else None
    registry_path = os.path.join(root_dir, perfil["registry"]) if "registry" in perfil else None

    return Result.ok({
        "dest_principal": dest_principal,
        "mirrors": mirrors,
        "anchors": anchors,
        "router_anchor": router_anchor,
        "registry": registry_path,
        "camada_alvo": perfil.get("camada_alvo"),
    })
