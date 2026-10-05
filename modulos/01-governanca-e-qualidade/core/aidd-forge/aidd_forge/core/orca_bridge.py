"""Compilador de configuracao ORCA a partir da frota real do host.

Gera `01_orca_inventory.json` contendo apenas as ferramentas realmente
instaladas e `02_routing_rules.json` com fallback em cascata: multiplos
agentes sao roteados por especialidade, um unico agente assume todos os
workers em worktrees isoladas (sem erro), e `ORCA_DEFAULT_HARNESS` sobrepoe
qualquer deteccao automatica.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from aidd_forge.core.detector import HostReport

ENV_DEFAULT_HARNESS = "ORCA_DEFAULT_HARNESS"

# Ordem de preferencia por especialidade quando ha mais de um agente no host.
ROLE_PREFERENCES: dict[str, tuple[str, ...]] = {
    "architect": ("claude", "codex", "cursor", "agy", "ollama"),
    "database": ("codex", "claude", "cursor", "agy", "ollama"),
    "frontend": ("cursor", "claude", "codex", "agy", "ollama"),
    "backend": ("codex", "claude", "cursor", "agy", "ollama"),
    "security": ("claude", "codex", "cursor", "agy", "ollama"),
    "qa": ("claude", "codex", "cursor", "agy", "ollama"),
}

MODE_OVERRIDE = "single_harness_override"
MODE_SINGLE_AGENT = "single_agent_isolated"
MODE_MULTI_AGENT = "multi_agent_specialized"
MODE_UNCONFIGURED = "unconfigured"

INVENTORY_FILENAME = "01_orca_inventory.json"
ROUTING_FILENAME = "02_routing_rules.json"


@dataclass(frozen=True)
class OrcaBridgeResult:
    """Caminhos e conteudo gerado por `write_orca_config`."""

    inventory_path: Path
    routing_path: Path
    inventory: dict
    routing: dict


def resolve_default_harness(explicit: str | None = None) -> str | None:
    """Resolve o override de harness: parametro explicito vence a env var."""
    if explicit:
        return explicit
    return os.environ.get(ENV_DEFAULT_HARNESS) or None


def build_inventory(host: HostReport) -> dict:
    """Monta o inventario contendo apenas ferramentas realmente detectadas."""
    return {
        "os": host.os_name,
        "orca_present": host.orca_present,
        "harnesses": list(host.available_tools),
        "harness_count": len(host.available_tools),
    }


def build_routing_rules(host: HostReport, default_harness: str | None = None) -> dict:
    """Monta as regras de roteamento com fallback em cascata.

    Precedencia: override (`ORCA_DEFAULT_HARNESS` ou parametro explicito) >
    nenhum agente detectado > agente unico (isolado por worktree) > multiplos
    agentes roteados por especialidade.
    """
    override = resolve_default_harness(default_harness)
    if override:
        roles = {role: _route(override) for role in ROLE_PREFERENCES}
        return _rules(MODE_OVERRIDE, override, roles)

    if host.has_no_agent:
        roles = {role: _route(None) for role in ROLE_PREFERENCES}
        return _rules(MODE_UNCONFIGURED, None, roles)

    if host.has_single_agent:
        sole = host.available_tools[0]
        roles = {role: _route(sole) for role in ROLE_PREFERENCES}
        return _rules(MODE_SINGLE_AGENT, None, roles)

    roles = {
        role: _route(_pick_preferred(preferences, host.available_tools))
        for role, preferences in ROLE_PREFERENCES.items()
    }
    return _rules(MODE_MULTI_AGENT, None, roles)


def write_orca_config(
    host: HostReport, output_dir: Path, default_harness: str | None = None
) -> OrcaBridgeResult:
    """Gera e grava `01_orca_inventory.json` e `02_routing_rules.json`."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = build_inventory(host)
    routing = build_routing_rules(host, default_harness)

    inventory_path = output_dir / INVENTORY_FILENAME
    routing_path = output_dir / ROUTING_FILENAME
    _write_json(inventory_path, inventory)
    _write_json(routing_path, routing)

    return OrcaBridgeResult(
        inventory_path=inventory_path,
        routing_path=routing_path,
        inventory=inventory,
        routing=routing,
    )


def _pick_preferred(preferences: tuple[str, ...], available: tuple[str, ...]) -> str:
    for tool in preferences:
        if tool in available:
            return tool
    return available[0]


def _route(harness: str | None) -> dict:
    return {"harness": harness, "worktree_isolated": True}


def _rules(mode: str, default_harness_override: str | None, roles: dict) -> dict:
    return {
        "mode": mode,
        "default_harness_override": default_harness_override,
        "roles": roles,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
