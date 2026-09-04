"""Tests for src.core.fleet_discovery — Fleet Auto-Discovery & Fallback."""

from __future__ import annotations

import os
import sys
import shutil
from unittest.mock import patch

# Ensure src/ is on sys.path so core.fleet_discovery resolves
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import pytest

from core.fleet_discovery import (
    KNOWN_AGENTS,
    FleetDiscovery,
    AgentRouter,
    OrcaRunner,
)


# ===========================================================================
# FleetDiscovery
# ===========================================================================


class TestFleetDiscovery:
    def test_discover_agents_returns_all_known_agents(self):
        fd = FleetDiscovery()
        result = fd.discover_agents()
        # Should contain at least the keys from KNOWN_AGENTS
        for name in KNOWN_AGENTS:
            assert name in result
            assert "path" in result[name]
            assert "available" in result[name]
            assert "display" in result[name]
            assert "specialty" in result[name]

    def test_discover_agents_available_is_bool(self):
        fd = FleetDiscovery()
        result = fd.discover_agents()
        for info in result.values():
            assert isinstance(info["available"], bool)

    def test_discover_agents_path_is_str_or_none(self):
        fd = FleetDiscovery()
        result = fd.discover_agents()
        for info in result.values():
            assert info["path"] is None or isinstance(info["path"], str)

    def test_available_agents_filters_unavailable(self):
        fd = FleetDiscovery()
        available = fd.available_agents()
        for info in available.values():
            assert info["available"] is True

    def test_available_agents_subset_of_discover(self):
        fd = FleetDiscovery()
        all_agents = fd.discover_agents()
        available = fd.available_agents()
        assert len(available) <= len(all_agents)
        for name in available:
            assert name in all_agents

    def test_classify_specialty_known_agents(self):
        assert FleetDiscovery.classify_specialty("claude") == "architect"
        assert FleetDiscovery.classify_specialty("codex") == "backend"
        assert FleetDiscovery.classify_specialty("antigravity") == "frontend"
        assert FleetDiscovery.classify_specialty("agy") == "frontend"
        assert FleetDiscovery.classify_specialty("ollama") == "backend"
        assert FleetDiscovery.classify_specialty("openai") == "backend"

    def test_classify_specialty_unknown_defaults_backend(self):
        assert FleetDiscovery.classify_specialty("unknown_agent") == "backend"

    def test_extra_agents_merged(self):
        extra = {"myagent": {"binary": "myagent", "display": "My Agent", "default_specialty": "docs"}}
        fd = FleetDiscovery(extra_agents=extra)
        result = fd.discover_agents()
        assert "myagent" in result
        assert result["myagent"]["display"] == "My Agent"

    @patch("core.fleet_discovery.shutil.which", return_value="/usr/bin/fake")
    def test_discover_agents_mock_available(self, mock_which):
        fd = FleetDiscovery(extra_agents={"fake": {"binary": "fake", "display": "Fake", "default_specialty": "backend"}})
        result = fd.discover_agents()
        assert result["fake"]["available"] is True
        assert result["fake"]["path"] == "/usr/bin/fake"

    @patch("core.fleet_discovery.shutil.which", return_value=None)
    def test_discover_agents_mock_unavailable(self, mock_which):
        fd = FleetDiscovery()
        result = fd.discover_agents()
        for info in result.values():
            assert info["available"] is False
            assert info["path"] is None


# ===========================================================================
# AgentRouter
# ===========================================================================


class TestAgentRouter:
    def _make_router(self, available: dict | None = None):
        """Helper: create a router with a mocked FleetDiscovery."""
        fd = FleetDiscovery()
        if available is not None:
            fd.available_agents = lambda: available
        return AgentRouter(fd)

    def test_route_returns_string(self):
        router = self._make_router(available={"claude": {"available": True}})
        result = router.route("architect")
        assert isinstance(result, str)

    def test_route_prefers_correct_agent_for_task(self):
        available = {
            "claude": {"available": True},
            "codex": {"available": True},
            "antigravity": {"available": True},
        }
        router = self._make_router(available=available)
        assert router.route("frontend") == "antigravity"
        assert router.route("backend") == "codex"
        assert router.route("architect") == "claude"

    def test_route_fallback_to_default(self):
        # Only codex available, but task prefers claude first
        available = {"codex": {"available": True}}
        router = self._make_router(available=available)
        # architect prefers claude, but only codex is available
        result = router.route("architect")
        assert result == "codex"

    def test_route_raises_when_no_agents(self):
        router = self._make_router(available={})
        with pytest.raises(RuntimeError, match="Nenhum agente encontrado"):
            router.route("backend")

    def test_read_env_config_returns_dict(self):
        config = AgentRouter.read_env_config()
        assert isinstance(config, dict)

    def test_read_env_config_reads_orca_vars(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('ORCA_DEFAULT_HARNESS=codex\nOTHER_VAR=ignored\n')
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            config = AgentRouter.read_env_config()
            assert config.get("ORCA_DEFAULT_HARNESS") == "codex"
            assert "OTHER_VAR" not in config
        finally:
            os.chdir(old_cwd)


# ===========================================================================
# OrcaRunner
# ===========================================================================


class TestOrcaRunner:
    def test_infer_task_type_frontend(self):
        assert OrcaRunner._infer_task_type("frontend-ui") == "frontend"
        assert OrcaRunner._infer_task_type("react-app") == "frontend"
        assert OrcaRunner._infer_task_type("web-dashboard") == "frontend"

    def test_infer_task_type_database(self):
        assert OrcaRunner._infer_task_type("db-migrations") == "database"
        assert OrcaRunner._infer_task_type("schema-manager") == "database"

    def test_infer_task_type_security(self):
        assert OrcaRunner._infer_task_type("auth-service") == "security"
        assert OrcaRunner._infer_task_type("jwt-provider") == "security"
        assert OrcaRunner._infer_task_type("rls-policies") == "security"

    def test_infer_task_type_testing(self):
        assert OrcaRunner._infer_task_type("test-runner") == "testing"
        assert OrcaRunner._infer_task_type("bdd-specs") == "testing"

    def test_infer_task_type_docs(self):
        assert OrcaRunner._infer_task_type("api-docs") == "docs"
        assert OrcaRunner._infer_task_type("readme-gen") == "docs"

    def test_infer_task_type_devops(self):
        assert OrcaRunner._infer_task_type("docker-deploy") == "devops"
        assert OrcaRunner._infer_task_type("ci-pipeline") == "devops"

    def test_infer_task_type_default_backend(self):
        assert OrcaRunner._infer_task_type("crm") == "backend"
        assert OrcaRunner._infer_task_type("erp") == "backend"
        assert OrcaRunner._infer_task_type("helpdesk") == "backend"

    @patch.object(FleetDiscovery, "available_agents")
    def test_run_compose_multi_agent(self, mock_avail):
        mock_avail.return_value = {
            "claude": {"available": True, "path": "/usr/bin/claude", "display": "Claude Code", "specialty": "architect"},
            "codex": {"available": True, "path": "/usr/bin/codex", "display": "OpenAI Codex", "specialty": "backend"},
        }
        runner = OrcaRunner()
        result = runner.run_compose(["crm", "frontend-ui", "auth-service"])
        assert result["strategy"] == "multi-agent"
        assert "crm" in result["assignments"]
        assert "frontend-ui" in result["assignments"]
        assert "auth-service" in result["assignments"]

    @patch.object(FleetDiscovery, "available_agents")
    def test_run_compose_single_agent(self, mock_avail):
        mock_avail.return_value = {
            "claude": {"available": True, "path": "/usr/bin/claude", "display": "Claude Code", "specialty": "architect"},
        }
        runner = OrcaRunner()
        result = runner.run_compose(["crm", "erp"])
        assert result["strategy"] == "single-agent"
        assert result["assignments"]["crm"] == "claude"
        assert result["assignments"]["erp"] == "claude"

    @patch.object(FleetDiscovery, "available_agents")
    def test_run_compose_no_agents_raises(self, mock_avail):
        mock_avail.return_value = {}
        runner = OrcaRunner()
        with pytest.raises(RuntimeError, match="Nenhum agente"):
            runner.run_compose(["crm"])
