"""Tests for flight_plan.py — deterministic flight plan generation."""

import json
from pathlib import Path

import pytest

from scripts.flight_plan import gerar_plano_de_voo, renderizar_plano_de_voo

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
PROFILES_PATH = REPO_ROOT / "componentes/compartilhado/skills/orca-plan-orchestrator/.orca/harness_profiles.json.example"

FIXTURES = {
    "evolucao-notas-auditoria": REPO_ROOT / "docs/planos/evolucao-notas-auditoria",
    "refinamento-notas-auditoria": REPO_ROOT / "docs/planos/refinamento-notas-auditoria",
    "testes-completos-ecossistema": REPO_ROOT / "docs/planos/testes-completos-ecossistema",
    "skill-gerador-planos-auditoria": REPO_ROOT / "docs/planos/skill-gerador-planos-auditoria",
}

EXPECTED_FRONT_COUNTS = {
    "evolucao-notas-auditoria": 7,
    "refinamento-notas-auditoria": 6,
    "testes-completos-ecossistema": 5,
    "skill-gerador-planos-auditoria": 1,
}

HARNESSES = ["mimo", "opencode", "claude", "agy"]


# ---------------------------------------------------------------------------
# gerar_plano_de_voo basic structure
# ---------------------------------------------------------------------------
class TestGerarPlanoDeVoo:
    """Verify flight plan generation across real fixtures."""

    @pytest.mark.parametrize("folder_name", list(FIXTURES.keys()), ids=list(FIXTURES.keys()))
    def test_returns_dict_with_required_keys(self, folder_name: str) -> None:
        result = gerar_plano_de_voo(FIXTURES[folder_name], PROFILES_PATH, harness="mimo")
        assert isinstance(result, dict)
        for key in ("plan_dir", "harness", "profile_binary", "fronts"):
            assert key in result, f"Missing key: {key}"

    @pytest.mark.parametrize("folder_name", list(FIXTURES.keys()), ids=list(FIXTURES.keys()))
    def test_front_count_matches_plan(self, folder_name: str) -> None:
        result = gerar_plano_de_voo(FIXTURES[folder_name], PROFILES_PATH, harness="mimo")
        assert len(result["fronts"]) == EXPECTED_FRONT_COUNTS[folder_name]

    def test_skill_fixture_single_front_branch_and_worktree(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["skill-gerador-planos-auditoria"], PROFILES_PATH, harness="mimo"
        )
        front = result["fronts"][0]
        assert front["name"] == "criar-skill-planos-auditoria-runner"
        assert front["branch"] == "orca/criar-skill-planos-auditoria-runner"
        assert front["worktree"] == "wt-criar-skill-planos-auditoria-runner"

    def test_skill_fixture_command_is_mimo(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["skill-gerador-planos-auditoria"], PROFILES_PATH, harness="mimo"
        )
        cmd = result["fronts"][0]["command"]
        assert cmd[0] == "mimo"
        assert "--yolo" in cmd
        assert "--prompt" in cmd

    def test_harness_field_matches_input(self) -> None:
        for h in HARNESSES:
            result = gerar_plano_de_voo(
                FIXTURES["skill-gerador-planos-auditoria"], PROFILES_PATH, harness=h
            )
            assert result["harness"] == h


# ---------------------------------------------------------------------------
# All 4 harnesses compile without error
# ---------------------------------------------------------------------------
class TestHarnessCompilation:
    """Ensure every harness compiles commands for all fixtures."""

    @pytest.mark.parametrize("harness", HARNESSES)
    def test_all_fixtures_compile(self, harness: str) -> None:
        for folder_name, folder_path in FIXTURES.items():
            result = gerar_plano_de_voo(folder_path, PROFILES_PATH, harness=harness)
            assert len(result["fronts"]) > 0
            for front in result["fronts"]:
                assert isinstance(front["command"], list)
                assert len(front["command"]) >= 2  # at minimum binary + auto_approve


# ---------------------------------------------------------------------------
# Branch/worktree naming convention
# ---------------------------------------------------------------------------
class TestNamingConvention:
    """Branch and worktree names follow the expected pattern."""

    def test_all_fronts_have_orca_branch_prefix(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["evolucao-notas-auditoria"], PROFILES_PATH, harness="mimo"
        )
        for front in result["fronts"]:
            assert front["branch"].startswith("orca/")

    def test_all_fronts_have_wt_worktree_prefix(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["evolucao-notas-auditoria"], PROFILES_PATH, harness="mimo"
        )
        for front in result["fronts"]:
            assert front["worktree"].startswith("wt-")

    def test_branch_and_worktree_match_front_name(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["evolucao-notas-auditoria"], PROFILES_PATH, harness="claude"
        )
        for front in result["fronts"]:
            assert front["branch"] == f"orca/{front['name']}"
            assert front["worktree"] == f"wt-{front['name']}"


# ---------------------------------------------------------------------------
# renderizar_plano_de_voo
# ---------------------------------------------------------------------------
class TestRenderizarPlanoDeVoo:
    """Verify ASCII/markdown rendering of a flight plan."""

    def test_render_contains_header(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["skill-gerador-planos-auditoria"], PROFILES_PATH, harness="mimo"
        )
        rendered = renderizar_plano_de_voo(result)
        assert "# Flight Plan" in rendered
        assert "mimo" in rendered

    def test_render_contains_table_header(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["skill-gerador-planos-auditoria"], PROFILES_PATH, harness="claude"
        )
        rendered = renderizar_plano_de_voo(result)
        assert "| Front |" in rendered
        assert "| Branch |" in rendered
        assert "| Worktree |" in rendered

    def test_render_contains_front_name(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["skill-gerador-planos-auditoria"], PROFILES_PATH, harness="mimo"
        )
        rendered = renderizar_plano_de_voo(result)
        assert "criar-skill-planos-auditoria-runner" in rendered

    def test_render_truncates_long_commands(self) -> None:
        """The real front content is long enough to trigger truncation."""
        result = gerar_plano_de_voo(
            FIXTURES["skill-gerador-planos-auditoria"], PROFILES_PATH, harness="mimo"
        )
        rendered = renderizar_plano_de_voo(result)
        # The front content is very long, so the command row should contain "..."
        assert "..." in rendered

    def test_render_row_count_matches_fronts(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["evolucao-notas-auditoria"], PROFILES_PATH, harness="mimo"
        )
        rendered = renderizar_plano_de_voo(result)
        # Count data rows (lines starting with "| " but not the header/separator)
        data_rows = [
            line for line in rendered.splitlines()
            if line.startswith("| ") and not line.startswith("| #")
            and not line.startswith("|---")
        ]
        assert len(data_rows) == 7


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------
class TestErrorPaths:
    """Edge cases and error handling."""

    def test_unknown_harness_raises(self) -> None:
        with pytest.raises(KeyError, match="nao encontrado"):
            gerar_plano_de_voo(
                FIXTURES["skill-gerador-planos-auditoria"], PROFILES_PATH, harness="nonexistent"
            )

    def test_invalid_plan_dir_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            gerar_plano_de_voo("/no/such/dir", PROFILES_PATH, harness="mimo")
