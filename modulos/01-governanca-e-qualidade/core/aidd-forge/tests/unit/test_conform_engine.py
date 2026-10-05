"""Testes unitarios do ConformEngine (conform_engine.py)."""

from pathlib import Path

import pytest

from aidd_forge.core.audit_engine import AuditEngine
from aidd_forge.core.conform_engine import ConformEngine, ConformReport


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def empty_project(tmp_path: Path):
    return tmp_path


@pytest.fixture
def engine(empty_project):
    return ConformEngine(empty_project)


# --- Dry run -----------------------------------------------------------------


def test_dry_run_does_not_modify_files(empty_project: Path) -> None:
    engine = ConformEngine(empty_project)
    report = engine.run(dry_run=True)

    assert isinstance(report, ConformReport)
    # No AGENTS.md should be created in dry run
    assert not (empty_project / "AGENTS.md").exists()


def test_dry_run_reports_fixable_items(empty_project: Path) -> None:
    engine = ConformEngine(empty_project)
    report = engine.run(dry_run=True)

    assert report.total_fixes > 0
    assert all("[DRY-RUN]" in f.description for f in report.fixes)


# --- Full run ----------------------------------------------------------------


def test_full_run_creates_agents_md(empty_project: Path) -> None:
    engine = ConformEngine(empty_project)
    report = engine.run(dry_run=False)

    assert (empty_project / "AGENTS.md").exists()
    assert report.successful_fixes > 0


def test_full_run_adds_gitignore_patterns(empty_project: Path) -> None:
    engine = ConformEngine(empty_project)
    report = engine.run(dry_run=False)

    gitignore = (empty_project / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules" in gitignore


def test_full_run_creates_gitattributes(empty_project: Path) -> None:
    engine = ConformEngine(empty_project)
    report = engine.run(dry_run=False)

    gitattributes = (empty_project / ".gitattributes").read_text(encoding="utf-8")
    assert "eol=lf" in gitattributes


def test_full_run_creates_claude_md(empty_project: Path) -> None:
    engine = ConformEngine(empty_project)
    report = engine.run(dry_run=False)

    assert (empty_project / "CLAUDE.md").exists()
    content = (empty_project / "CLAUDE.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in content


# --- Item filter -------------------------------------------------------------


def test_item_filter_applies_only_specified(empty_project: Path) -> None:
    engine = ConformEngine(empty_project)
    report = engine.run(dry_run=True, item_filter=[1])

    # Only G01 should be in fixes, others should be skipped
    fix_ids = [f.audit_item_id for f in report.fixes]
    assert "G01" in fix_ids
    assert len(report.skipped) > 0


# --- Is idempotent -----------------------------------------------------------


def test_conform_is_idempotent(empty_project: Path) -> None:
    engine = ConformEngine(empty_project)
    report1 = engine.run(dry_run=False)
    report2 = engine.run(dry_run=False)

    # Second run should have fewer or equal successful fixes
    assert report2.successful_fixes <= report1.successful_fixes


# --- Summary -----------------------------------------------------------------


def test_summary_output(engine: ConformEngine) -> None:
    report = engine.run(dry_run=True)
    summary = report.summary()

    assert "[forge conform]" in summary
    assert "audit items fixable:" in summary
