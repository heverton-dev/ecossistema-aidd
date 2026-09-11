"""Tests for flight_plan.py — deterministic flight plan generation."""

import json
from pathlib import Path

import pytest

from scripts.flight_plan import gerar_plano_de_voo, renderizar_plano_de_voo

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent


def _plano(nome_curto: str) -> Path:
    """Acha a pasta do plano pelo nome curto, em qualquer subpasta de status.

    Resolve por glob de proposito: o nome fisico carrega o prefixo
    PLAN-<NNNN>_<dd-mm-aaaa>-, e o plano muda de subpasta conforme o status
    real. Fixar o caminho literal quebraria o teste a cada renomeacao ou
    mudanca de status — foi o que aconteceu em 11-09-2026.
    """
    partes = nome_curto.split("-")
    # Tenta o nome inteiro e vai encurtando: o nome fisico guarda so as 3
    # primeiras palavras significativas, entao "skill-gerador-planos-auditoria"
    # precisa casar com "...-skill-gerador-planos".
    while partes:
        alvo = "-".join(partes)
        for sub in ("feitos", "fazendo", "a-fazer", ""):
            base = REPO_ROOT / "docs" / "planos" / sub if sub else REPO_ROOT / "docs" / "planos"
            achados = sorted(p for p in base.glob(f"*{alvo}") if p.is_dir())
            if achados:
                return achados[0]
        partes.pop()
    raise FileNotFoundError(f"Plano '{nome_curto}' nao encontrado em docs/planos/")
PROFILES_PATH = REPO_ROOT / "componentes/compartilhado/skills/orca-plan-orchestrator/.orca/harness_profiles.json.example"

FIXTURES = {
    "evolucao-notas-auditoria": _plano("evolucao-notas-auditoria"),
    "refinamento-notas-auditoria": _plano("refinamento-notas-auditoria"),
    "testes-completos-ecossistema": _plano("testes-completos-ecossistema"),
    "skill-gerador-planos-auditoria": _plano("skill-gerador-planos-auditoria"),
}

EXPECTED_FRONT_COUNTS = {
    "evolucao-notas-auditoria": 7,
    "refinamento-notas-auditoria": 6,
    "testes-completos-ecossistema": 6,
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
        assert front["name"] == "criar-skill-planos"
        assert front["branch"] == f"orca/{front['rotulo']}"
        assert front["worktree"] == front["rotulo"]
        assert "-fase-01-" in front["rotulo"]

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
            assert "-fase-" in front["worktree"]

    def test_branch_and_worktree_match_front_name(self) -> None:
        result = gerar_plano_de_voo(
            FIXTURES["evolucao-notas-auditoria"], PROFILES_PATH, harness="claude"
        )
        for front in result["fronts"]:
            assert front["branch"] == f"orca/{front['rotulo']}"
            assert front["worktree"] == front["rotulo"]


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
        assert "criar-skill-planos" in rendered

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
