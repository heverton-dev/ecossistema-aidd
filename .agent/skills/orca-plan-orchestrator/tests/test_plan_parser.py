"""Tests for plan_parser.py — parse real fixture folders."""

import pytest
from pathlib import Path

# Ensure the scripts package is importable
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from plan_parser import parse_plan, Plan, Front


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent

FIXTURES = {
    "evolucao-notas-auditoria": REPO_ROOT / "docs/planos/evolucao-notas-auditoria",
    "refinamento-notas-auditoria": REPO_ROOT / "docs/planos/refinamento-notas-auditoria",
    "testes-completos-ecossistema": REPO_ROOT / "docs/planos/testes-completos-ecossistema",
    "skill-gerador-planos-auditoria": REPO_ROOT / "docs/planos/skill-gerador-planos-auditoria",
}

# Manually verified front counts (NN-*.md files, excluding 00-PROCESSO-E-DECISOES.md)
EXPECTED_COUNTS = {
    "evolucao-notas-auditoria": 7,   # 01..07
    "refinamento-notas-auditoria": 6, # 01..06
    "testes-completos-ecossistema": 5, # 01..05
    "skill-gerador-planos-auditoria": 1, # 01
}


class TestParseRealFixtures:
    """Parse each of the 4 real fixture folders."""

    @pytest.mark.parametrize(
        "folder_name",
        list(FIXTURES.keys()),
        ids=list(FIXTURES.keys()),
    )
    def test_parse_without_error(self, folder_name: str) -> None:
        folder = FIXTURES[folder_name]
        plan = parse_plan(folder)

        assert isinstance(plan, Plan)
        assert plan.front_count == EXPECTED_COUNTS[folder_name]

    def test_evolution_fronts_have_correct_names(self) -> None:
        plan = parse_plan(FIXTURES["evolucao-notas-auditoria"])
        names = [f.name for f in plan.fronts]
        assert names == [
            "transparencia-e-gates",
            "testabilidade-e-determinismo",
            "modularizacao-injector",
            "cobertura-comandos-restantes",
            "economia-tokens-e-agentico",
            "universalidade",
            "agnosticismo-distribuicao-componentes",
        ]

    def test_master_content_is_populated(self) -> None:
        plan = parse_plan(FIXTURES["testes-completos-ecossistema"])
        assert len(plan.master_content) > 100
        assert "PROCESSO" in plan.master_content.upper()

    def test_fronts_are_sorted_by_index(self) -> None:
        plan = parse_plan(FIXTURES["refinamento-notas-auditoria"])
        indices = [f.index for f in plan.fronts]
        assert indices == sorted(indices)

    def test_invalid_folder_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_plan("/nonexistent/path/xyz")

    def test_folder_without_master_raises(self, tmp_path: Path) -> None:
        (tmp_path / "01-algo.md").write_text("content")
        with pytest.raises(FileNotFoundError, match="Master file"):
            parse_plan(tmp_path)

    def test_folder_without_fronts_raises(self, tmp_path: Path) -> None:
        (tmp_path / "00-PROCESSO-E-DECISOES.md").write_text("master")
        with pytest.raises(ValueError, match=r"No NN-\*\.md"):
            parse_plan(tmp_path)

    def test_parse_dot_relative(self, tmp_path: Path) -> None:
        """Parser accepts '.' or relative paths."""
        (tmp_path / "00-PROCESSO-E-DECISOES.md").write_text("master content")
        (tmp_path / "01-frente-a.md").write_text("front a content")
        (tmp_path / "02-frente-b.md").write_text("front b content")

        plan = parse_plan(tmp_path)
        assert plan.front_count == 2
        assert plan.fronts[0].name == "frente-a"
        assert plan.fronts[1].name == "frente-b"


class TestParseFrontContent:
    """Verify that front content is actually read from files."""

    def test_front_content_matches_file(self) -> None:
        plan = parse_plan(FIXTURES["skill-gerador-planos-auditoria"])
        assert plan.front_count == 1
        front = plan.fronts[0]
        assert front.name == "criar-skill-planos-auditoria-runner"
        # Content should be read from disk
        disk_content = front.file_path.read_text(encoding="utf-8")
        assert front.content == disk_content
