"""Testes de integracao CLI para forge audit e forge conform."""

from pathlib import Path

import pytest

from aidd_forge.cli import cmd_audit, cmd_conform


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- forge audit CLI ---------------------------------------------------------


def test_audit_returns_zero_when_compliant(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nThinking constraint: compact English.\n\nExecution limit: 3 to 5 steps.\n\nOutput format: Silent executor.\n\nBash rule: pipe to tail/grep.\n\nGraph-first: query code-review-graph.\n")
    _write(tmp_path / "CLAUDE.md", "@AGENTS.md\n")
    _write(tmp_path / ".gitignore", "node_modules/\npackage-lock.json\npnpm-lock.yaml\nyarn.lock\nbun.lockb\n")
    _write(tmp_path / ".gitattributes", "* text=auto eol=lf\n")

    exit_code = cmd_audit(str(tmp_path), "json", None)
    assert exit_code == 0


def test_audit_returns_one_when_non_compliant(tmp_path: Path) -> None:
    exit_code = cmd_audit(str(tmp_path), "json", None)
    assert exit_code == 1


def test_audit_json_output(tmp_path: Path, capsys) -> None:
    cmd_audit(str(tmp_path), "json", None)
    captured = capsys.readouterr()
    assert '"metadata"' in captured.out


def test_audit_md_output(tmp_path: Path, capsys) -> None:
    cmd_audit(str(tmp_path), "md", None)
    captured = capsys.readouterr()
    assert "Auditoria de Conformidade" in captured.out


def test_audit_html_output(tmp_path: Path, capsys) -> None:
    cmd_audit(str(tmp_path), "html", None)
    captured = capsys.readouterr()
    assert "<!doctype html>" in captured.out


def test_audit_writes_to_file(tmp_path: Path) -> None:
    output_path = tmp_path / "report.json"
    cmd_audit(str(tmp_path), "json", str(output_path))

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert '"metadata"' in content


# --- forge conform CLI -------------------------------------------------------


def test_conform_dry_run_does_not_modify(tmp_path: Path) -> None:
    cmd_conform(str(tmp_path), dry_run=True, items=())
    assert not (tmp_path / "AGENTS.md").exists()


def test_conform_full_run_creates_files(tmp_path: Path, capsys) -> None:
    exit_code = cmd_conform(str(tmp_path), dry_run=False, items=())
    captured = capsys.readouterr()

    assert exit_code == 0
    assert (tmp_path / "AGENTS.md").exists()
    assert "[forge conform]" in captured.out


def test_conform_item_filter(tmp_path: Path, capsys) -> None:
    exit_code = cmd_conform(str(tmp_path), dry_run=False, items=(1,))
    captured = capsys.readouterr()

    assert exit_code == 0
    # G01 should have been fixed
    assert "G01" in captured.out
