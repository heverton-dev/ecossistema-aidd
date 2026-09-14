"""Testes unitarios do AuditEngine (audit_engine.py)."""

from pathlib import Path

import pytest

from aidd_forge.core.audit_engine import AuditEngine, AuditReport


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_engine_runs_all_checks(tmp_path: Path) -> None:
    engine = AuditEngine(tmp_path)
    report = engine.run()

    assert isinstance(report, AuditReport)
    assert report.total == 15
    assert len(report.items) == 15


def test_engine_empty_project_has_low_compliance(tmp_path: Path) -> None:
    engine = AuditEngine(tmp_path)
    report = engine.run()

    assert report.compliance_rate < 50.0
    assert report.failed > 0


def test_engine_well_bootstrapped_project_has_high_compliance(tmp_path: Path) -> None:
    # Create a well-formed project
    _write(tmp_path / "AGENTS.md", "# AGENTS.md\n\nThinking constraint: Think strictly in compact English.\n\nExecution limit: Resolve tasks in 3 to 5 steps.\n\nOutput format: Silent executor. Return code edits and 1-line execution status.\n\nBash rule: Always pipe verbose commands to tail/grep.\n\nGraph-first: Always query code-review-graph before Grep.\n")
    _write(tmp_path / "CLAUDE.md", "# CLAUDE.md\n\n@AGENTS.md\n")
    _write(tmp_path / ".gitignore", "node_modules/\npackage-lock.json\npnpm-lock.yaml\nyarn.lock\nbun.lockb\n")
    _write(tmp_path / ".gitattributes", "* text=auto eol=lf\n")

    engine = AuditEngine(tmp_path)
    report = engine.run()

    # Should pass most checks
    assert report.compliance_rate >= 60.0
    assert report.passed >= 8


def test_report_compliance_rate_calculation(tmp_path: Path) -> None:
    engine = AuditEngine(tmp_path)
    report = engine.run()

    expected_rate = (report.passed / report.total) * 100.0
    assert abs(report.compliance_rate - expected_rate) < 0.01


def test_report_fixable_count(tmp_path: Path) -> None:
    engine = AuditEngine(tmp_path)
    report = engine.run()

    fixable = report.fixable_items
    assert len(fixable) == report.fixable_count
    assert all(item.fixable for item in fixable)
    assert all(item.status != "PASS" for item in fixable)


def test_report_timestamp_is_set(tmp_path: Path) -> None:
    engine = AuditEngine(tmp_path)
    report = engine.run()

    assert report.timestamp != ""
    assert "T" in report.timestamp  # ISO format
