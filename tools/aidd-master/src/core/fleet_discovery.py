"""
Fleet Auto-Discovery & Fallback for ORCA ADE
=============================================
Detects available agent CLIs on PATH, classifies them by specialty,
and routes tasks to the best available agent with a fallback cascade.

Classes:
    FleetDiscovery  — scans PATH for known agent CLIs
    AgentRouter     — picks the best agent for a given task type
    OrcaRunner      — orchestrates compose with auto-discovered agents
"""

from __future__ import annotations

import os
import shutil
from typing import Any


# ---------------------------------------------------------------------------
# Known agent CLIs and their metadata
# ---------------------------------------------------------------------------

KNOWN_AGENTS: dict[str, dict[str, Any]] = {
    "claude": {
        "binary": "claude",
        "display": "Claude Code",
        "default_specialty": "architect",
    },
    "codex": {
        "binary": "codex",
        "display": "OpenAI Codex",
        "default_specialty": "backend",
    },
    "antigravity": {
        "binary": "antigravity",
        "display": "Antigravity (AGY)",
        "default_specialty": "frontend",
    },
    "agy": {
        "binary": "agy",
        "display": "Antigravity (AGY alias)",
        "default_specialty": "frontend",
    },
    "ollama": {
        "binary": "ollama",
        "display": "Ollama",
        "default_specialty": "backend",
    },
    "openai": {
        "binary": "openai",
        "display": "OpenAI CLI",
        "default_specialty": "backend",
    },
}

# Specialty mapping: task_type -> preferred agent name
_TASK_AGENT_PREFS: dict[str, list[str]] = {
    "architect":  ["claude", "codex", "antigravity", "agy", "ollama", "openai"],
    "database":   ["claude", "codex", "ollama", "openai", "antigravity", "agy"],
    "frontend":   ["antigravity", "agy", "claude", "codex", "ollama", "openai"],
    "backend":    ["codex", "claude", "ollama", "openai", "antigravity", "agy"],
    "security":   ["claude", "codex", "ollama", "openai", "antigravity", "agy"],
    "testing":    ["codex", "claude", "ollama", "openai", "antigravity", "agy"],
    "devops":     ["claude", "codex", "ollama", "openai", "antigravity", "agy"],
    "docs":       ["claude", "codex", "antigravity", "agy", "ollama", "openai"],
}


# ===========================================================================
# FleetDiscovery
# ===========================================================================

class FleetDiscovery:
    """Scans PATH for known agent CLIs and classifies them by specialty."""

    def __init__(self, extra_agents: dict[str, dict[str, Any]] | None = None):
        self._agents: dict[str, dict[str, Any]] = {**KNOWN_AGENTS}
        if extra_agents:
            self._agents.update(extra_agents)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover_agents(self) -> dict[str, dict[str, Any]]:
        """Scan PATH for every known agent CLI.

        Returns:
            dict mapping agent_name -> {'path': str | None, 'available': bool}
        """
        result: dict[str, dict[str, Any]] = {}
        for name, meta in self._agents.items():
            binary = meta.get("binary", name)
            found = shutil.which(binary)
            result[name] = {
                "path": found,
                "available": found is not None,
                "display": meta.get("display", name),
                "specialty": meta.get("default_specialty", "backend"),
            }
        return result

    def available_agents(self) -> dict[str, dict[str, Any]]:
        """Return only agents that are actually available on PATH."""
        return {k: v for k, v in self.discover_agents().items() if v["available"]}

    @staticmethod
    def classify_specialty(agent_name: str) -> str:
        """Map an agent name to its primary specialty / role.

        Returns one of: architect, database, frontend, backend, security,
        testing, devops, docs.
        """
        _specialty_map: dict[str, str] = {
            "claude": "architect",
            "codex": "backend",
            "antigravity": "frontend",
            "agy": "frontend",
            "ollama": "backend",
            "openai": "backend",
        }
        return _specialty_map.get(agent_name, "backend")


# ===========================================================================
# AgentRouter
# ===========================================================================

class AgentRouter:
    """Picks the best available agent for a given task type.

    Fallback cascade:
        preferred_agent -> default_agent -> any_available -> RuntimeError
    """

    DEFAULT_AGENT = "claude"

    def __init__(self, discovery: FleetDiscovery):
        self._discovery = discovery
        self._env_config = self.read_env_config()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, task_type: str) -> str:
        """Return the agent name best suited for *task_type*.

        Raises RuntimeError if no agent is available at all.
        """
        available = self._discovery.available_agents()
        if not available:
            raise RuntimeError(
                "Nenhum agente encontrado no PATH. "
                "Instale pelo menos um: claude, codex, antigravity, ollama, openai."
            )

        # 1. Preferred agents for this task type
        prefs = _TASK_AGENT_PREFS.get(task_type, [])
        for agent_name in prefs:
            if agent_name in available:
                return agent_name

        # 2. Default agent from env or class constant
        default = self._env_config.get("ORCA_DEFAULT_HARNESS", self.DEFAULT_AGENT)
        if default in available:
            return default

        # 3. Any available agent
        return next(iter(available))

    @staticmethod
    def read_env_config() -> dict[str, str]:
        """Read ORCA_DEFAULT_HARNESS (and future vars) from .env if present."""
        config: dict[str, str] = {}
        env_paths = [".env", os.path.join(".orca", ".env")]
        for env_path in env_paths:
            if os.path.isfile(env_path):
                try:
                    with open(env_path, encoding="utf-8") as fh:
                        for line in fh:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if "=" in line:
                                key, _, value = line.partition("=")
                                key = key.strip()
                                value = value.strip().strip("\"'")
                                if key.startswith("ORCA_"):
                                    config[key] = value
                except OSError:
                    pass
                break  # first .env found wins
        return config


# ===========================================================================
# OrcaRunner
# ===========================================================================

class OrcaRunner:
    """Orchestrates compose with auto-discovered agents.

    Strategy:
    - Multiple agents detected: route each module to the best agent by specialty.
    - Only 1 agent: use it for all workers (in separate worktrees).
    - No agents: raise a clear error.
    """

    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)
        self._discovery = FleetDiscovery()
        self._router = AgentRouter(self._discovery)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_compose(self, modules: list[str]) -> dict[str, Any]:
        """Orchestrate compose across *modules* with auto-discovered agents.

        Returns a dict with:
            - 'assignments': dict[module_name] -> agent_name
            - 'available_agents': list of discovered agent names
            - 'strategy': 'multi-agent' | 'single-agent'
            - 'diagnostics': human-readable lines
        """
        available = self._discovery.available_agents()
        agent_names = list(available.keys())
        assignments: dict[str, str] = {}
        diagnostics: list[str] = []

        if len(agent_names) >= 2:
            # Multi-agent: route by specialty
            strategy = "multi-agent"
            diagnostics.append(
                f"[Fleet] {len(agent_names)} agentes detectados — roteamento por especialidade"
            )
            for mod in modules:
                task_type = self._infer_task_type(mod)
                agent = self._router.route(task_type)
                assignments[mod] = agent
                specialty = FleetDiscovery.classify_specialty(agent)
                diagnostics.append(
                    f"  📦 {mod:<20s} → {agent:<12s} (especialidade: {specialty})"
                )
        elif len(agent_names) == 1:
            # Single agent: use it for everything
            sole = agent_names[0]
            strategy = "single-agent"
            diagnostics.append(
                f"[Fleet] Apenas 1 agente detectado ({sole}) — usando para todos os workers"
            )
            for mod in modules:
                assignments[mod] = sole
                diagnostics.append(f"  📦 {mod:<20s} → {sole:<12s} (único disponível)")
        else:
            strategy = "none"
            diagnostics.append("[Fleet] ⚠ Nenhum agente detectado no PATH!")
            raise RuntimeError(
                "Nenhum agente de IA encontrado no PATH. "
                "Instale claude, codex, antigravity, ollama ou openai."
            )

        # Print diagnostics
        print("=" * 70)
        print("🤖 [Fleet Discovery] Diagnóstico de Agentes")
        print("=" * 70)
        for line in diagnostics:
            print(line)
        print("=" * 70)

        return {
            "assignments": assignments,
            "available_agents": agent_names,
            "strategy": strategy,
            "diagnostics": diagnostics,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_task_type(module_name: str) -> str:
        """Heuristic: infer task type from a module name.

        Examples:
            'crm'       -> 'backend'
            'frontend'  -> 'frontend'
            'auth'      -> 'security'
            'database'  -> 'database'
            'docs'      -> 'docs'
        """
        name = module_name.lower()
        if any(kw in name for kw in ("front", "ui", "web", "react", "vue", "svelte")):
            return "frontend"
        if any(kw in name for kw in ("db", "database", "migration", "schema")):
            return "database"
        if any(kw in name for kw in ("auth", "security", "rls", "jwt", "oidc")):
            return "security"
        if any(kw in name for kw in ("test", "spec", "bdd", "qa")):
            return "testing"
        if any(kw in name for kw in ("deploy", "infra", "docker", "ci-pipeline")):
            return "devops"
        if any(kw in name for kw in ("docs", "readme", "api-doc")):
            return "docs"
        return "backend"
