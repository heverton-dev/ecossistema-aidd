"""Tests for orca_real_plan.py — flight plan compiler for the real ORCA app.

Verifies that the compiled plan never bakes the prompt into the launch
command (real ORCA sends it separately via `orca terminal send`), always
defaults to a child worktree (--parent-worktree, never --no-parent), and
resolves the base branch from the real repo instead of fabricating it.
"""

import subprocess
from pathlib import Path

import pytest

from scripts.orca_real_plan import compilar_plano_orca, renderizar_plano_orca, PARENT_WORKTREE_PADRAO

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
FIXTURE = _plano("skill-gerador-planos-auditoria")


@pytest.fixture
def repo_git_real(tmp_path):
    """Real git repo with a real commit, so _branch_atual has something to read."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "arquivo.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "arquivo.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "inicial"], cwd=repo, check=True)
    return repo


class TestCompilarPlanoOrca:
    def test_returns_dict_with_required_keys(self, repo_git_real):
        result = compilar_plano_orca(FIXTURE, PROFILES_PATH, repo_git_real, harness="claude")
        for key in ("plan_dir", "mode", "repo_path", "parent_worktree", "base_branch", "fronts"):
            assert key in result, f"Missing key: {key}"
        assert result["mode"] == "orca"

    def test_parent_worktree_defaults_to_active_never_solta(self, repo_git_real):
        result = compilar_plano_orca(FIXTURE, PROFILES_PATH, repo_git_real, harness="claude")
        assert result["parent_worktree"] == "active" == PARENT_WORKTREE_PADRAO

    def test_parent_worktree_can_be_overridden_but_still_explicit(self, repo_git_real):
        result = compilar_plano_orca(
            FIXTURE, PROFILES_PATH, repo_git_real, harness="claude",
            parent_worktree="branch:outra-mesa",
        )
        assert result["parent_worktree"] == "branch:outra-mesa"

    def test_base_branch_is_real_git_branch_not_fabricated(self, repo_git_real):
        result = compilar_plano_orca(FIXTURE, PROFILES_PATH, repo_git_real, harness="claude")
        real_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_git_real, capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert result["base_branch"] == real_branch

    def test_base_branch_falls_back_to_main_outside_git_repo(self, tmp_path):
        nao_repo = tmp_path / "nao-e-repo"
        nao_repo.mkdir()
        result = compilar_plano_orca(FIXTURE, PROFILES_PATH, nao_repo, harness="claude")
        assert result["base_branch"] == "main"

    def test_front_launch_command_never_contains_prompt(self, repo_git_real):
        result = compilar_plano_orca(FIXTURE, PROFILES_PATH, repo_git_real, harness="claude")
        front = result["fronts"][0]
        assert front["prompt"] not in " ".join(front["launch_command"])
        # Claude profile: bare launch = binary + auto_approve + model flag/value (no -p, no prompt)
        assert front["launch_command"] == [
            "claude", "--dangerously-skip-permissions", "--model", "claude-sonnet-5",
        ]

    def test_front_prompt_is_populated_separately(self, repo_git_real):
        result = compilar_plano_orca(FIXTURE, PROFILES_PATH, repo_git_real, harness="claude")
        front = result["fronts"][0]
        assert len(front["prompt"]) > 20

    def test_front_branch_uses_orca_prefix(self, repo_git_real):
        result = compilar_plano_orca(FIXTURE, PROFILES_PATH, repo_git_real, harness="claude")
        for front in result["fronts"]:
            assert front["branch"] == f"orca/{front['rotulo']}"
            # o rotulo diz plano e fase: PLAN-0016-fase-04-...
            assert front["rotulo"].startswith("PLAN-")
            assert "-fase-" in front["rotulo"]

    def test_harness_map_overrides_per_front(self, repo_git_real):
        result = compilar_plano_orca(
            FIXTURE, PROFILES_PATH, repo_git_real, harness="claude",
            harness_map={"criar-skill-planos": "opencode"},
        )
        front = result["fronts"][0]
        assert front["harness"] == "opencode"
        assert front["launch_command"][0] == "opencode"


class TestRenderizarPlanoOrca:
    def test_render_contains_parent_worktree_warning(self, repo_git_real):
        result = compilar_plano_orca(FIXTURE, PROFILES_PATH, repo_git_real, harness="claude")
        rendered = renderizar_plano_orca(result)
        assert "mesa sempre filha, nunca solta" in rendered
        assert "ORCA" in rendered

    def test_render_never_executed_disclaimer(self, repo_git_real):
        result = compilar_plano_orca(FIXTURE, PROFILES_PATH, repo_git_real, harness="claude")
        rendered = renderizar_plano_orca(result)
        assert "Nenhuma worktree/terminal real foi criado" in rendered
