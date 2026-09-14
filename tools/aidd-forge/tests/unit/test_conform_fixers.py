"""Testes unitarios dos fixers de conformidade (conform_fixers.py)."""

from pathlib import Path

import pytest

from aidd_forge.core.conform_fixers import (
    ConformFix,
    fix_g01_agents_md_missing,
    fix_g03_ide_pointers,
    fix_directive,
    fix_g12_gitignore,
    fix_g13_gitattributes,
    DIRECTIVES,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- G01: Create AGENTS.md ---------------------------------------------------


def test_g01_creates_agents_md_when_missing(tmp_path: Path) -> None:
    fix = fix_g01_agents_md_missing(tmp_path)

    assert fix.success is True
    assert (tmp_path / "AGENTS.md").exists()
    content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in content


def test_g01_is_idempotent(tmp_path: Path) -> None:
    fix1 = fix_g01_agents_md_missing(tmp_path)
    fix2 = fix_g01_agents_md_missing(tmp_path)

    assert fix1.success is True
    assert fix2.success is True
    assert fix2.files_touched == []  # No files touched on second run


def test_g01_skips_when_agents_md_exists(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Existing\n")
    fix = fix_g01_agents_md_missing(tmp_path)

    assert fix.success is True
    assert fix.files_touched == []


# --- G03: IDE pointers -------------------------------------------------------


def test_g03_creates_claude_md(tmp_path: Path) -> None:
    fix = fix_g03_ide_pointers(tmp_path)

    assert fix.success is True
    assert (tmp_path / "CLAUDE.md").exists()
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in content


def test_g03_removes_from_gitignore(tmp_path: Path) -> None:
    _write(tmp_path / ".gitignore", "CLAUDE.md\nGEMINI.md\n*.pyc\n")
    fix = fix_g03_ide_pointers(tmp_path)

    assert fix.success is True
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "CLAUDE.md" not in gitignore
    assert "GEMINI.md" not in gitignore
    assert "*.pyc" in gitignore


def test_g03_skips_when_pointer_exists(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "# CLAUDE.md\n\n@AGENTS.md\n")
    fix = fix_g03_ide_pointers(tmp_path)

    assert fix.success is True


# --- Directives (G05-G09) ---------------------------------------------------


def test_directive_injects_when_missing(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nSome existing rule.\n")
    fix = fix_directive(tmp_path, "G05")

    assert fix.success is True
    content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Thinking constraint" in content


def test_directive_is_idempotent(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n")
    fix1 = fix_directive(tmp_path, "G05")
    fix2 = fix_directive(tmp_path, "G05")

    assert fix1.success is True
    assert fix2.success is True
    content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert content.count("Thinking constraint") == 1


def test_directive_fails_without_agents_md(tmp_path: Path) -> None:
    fix = fix_directive(tmp_path, "G05")
    assert fix.success is False


def test_directive_fails_with_unknown_id(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n")
    fix = fix_directive(tmp_path, "G99")
    assert fix.success is False


def test_all_directives_have_patterns() -> None:
    for key in ("G05", "G06", "G07", "G08", "G09"):
        assert key in DIRECTIVES
        assert len(DIRECTIVES[key]) > 10


# --- G12: .gitignore ---------------------------------------------------------


def test_g12_creates_gitignore_when_missing(tmp_path: Path) -> None:
    fix = fix_g12_gitignore(tmp_path)

    assert fix.success is True
    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules" in content


def test_g12_adds_missing_patterns(tmp_path: Path) -> None:
    _write(tmp_path / ".gitignore", "*.pyc\n")
    fix = fix_g12_gitignore(tmp_path)

    assert fix.success is True
    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules" in content
    assert "package-lock.json" in content
    assert "*.pyc" in content  # Preserved


def test_g12_is_idempotent(tmp_path: Path) -> None:
    fix1 = fix_g12_gitignore(tmp_path)
    fix2 = fix_g12_gitignore(tmp_path)

    assert fix1.success is True
    assert fix2.success is True
    assert fix2.files_touched == []


# --- G13: .gitattributes -----------------------------------------------------


def test_g13_creates_gitattributes(tmp_path: Path) -> None:
    fix = fix_g13_gitattributes(tmp_path)

    assert fix.success is True
    content = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
    assert "text=auto" in content
    assert "eol=lf" in content


def test_g13_adds_lf_to_existing(tmp_path: Path) -> None:
    _write(tmp_path / ".gitattributes", "*.py linguist-language=Python\n")
    fix = fix_g13_gitattributes(tmp_path)

    assert fix.success is True
    content = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
    assert "eol=lf" in content
    assert "linguist-language" in content  # Preserved


def test_g13_is_idempotent(tmp_path: Path) -> None:
    fix1 = fix_g13_gitattributes(tmp_path)
    fix2 = fix_g13_gitattributes(tmp_path)

    assert fix1.success is True
    assert fix2.success is True
    assert fix2.files_touched == []
