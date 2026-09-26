"""Testes unitarios dos 15 verificadores de conformidade (audit_checks.py)."""

from pathlib import Path

import pytest

from aidd_forge.core.audit_checks import (
    AuditItem,
    check_g01_agents_md_exists,
    check_g02_agents_md_language,
    check_g03_ide_pointers,
    check_g04_agents_md_generic,
    check_g05_thinking_constraint,
    check_g06_execution_limit,
    check_g07_output_format,
    check_g08_bash_rule,
    check_g09_graph_first,
    check_g10_context_budget,
    check_g11_skills_frontmatter,
    check_g12_gitignore,
    check_g13_gitattributes,
    check_g14_no_duplicates,
    check_g15_cache_prefix,
    MAX_CONTEXT_TOKENS,
    CHARS_PER_TOKEN,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- G01: AGENTS.md exists ---------------------------------------------------


def test_g01_passes_when_agents_md_in_root(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n")
    result = check_g01_agents_md_exists(tmp_path)
    assert result.status == "PASS"
    assert result.fixable is True


def test_g01_passes_when_agents_md_in_governance(tmp_path: Path) -> None:
    _write(tmp_path / "governance" / "AGENTS.md", "# Rules\n")
    result = check_g01_agents_md_exists(tmp_path)
    assert result.status == "PASS"


def test_g01_fails_when_no_agents_md(tmp_path: Path) -> None:
    result = check_g01_agents_md_exists(tmp_path)
    assert result.status == "FAIL"


# --- G02: Language check -----------------------------------------------------


def test_g02_passes_for_english_content(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nThink strictly in compact English.\n")
    result = check_g02_agents_md_language(tmp_path)
    assert result.status == "PASS"


def test_g02_fails_for_ptbr_content(tmp_path: Path) -> None:
    content = "# Regras\n\n" + "esta configuracao deve ser implementada corretamente " * 10
    _write(tmp_path / "AGENTS.md", content)
    result = check_g02_agents_md_language(tmp_path)
    assert result.status == "FAIL"


def test_g02_skips_when_no_agents_md(tmp_path: Path) -> None:
    result = check_g02_agents_md_language(tmp_path)
    assert result.status == "SKIP"


# --- G03: IDE pointers -------------------------------------------------------


def test_g03_passes_with_pointer(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n")
    _write(tmp_path / "CLAUDE.md", "# Claude\n\n@AGENTS.md\n")
    result = check_g03_ide_pointers(tmp_path)
    assert result.status == "PASS"


def test_g03_fails_when_pointer_missing(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n")
    result = check_g03_ide_pointers(tmp_path)
    assert result.status == "FAIL"


def test_g03_fails_when_pointer_has_no_reference(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "# Claude\n\nSome other content.\n")
    result = check_g03_ide_pointers(tmp_path)
    assert result.status == "FAIL"


# --- G04: Generic AGENTS.md --------------------------------------------------


def test_g04_passes_for_generic_content(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nThink in compact English.\n")
    result = check_g04_agents_md_generic(tmp_path)
    assert result.status == "PASS"


def test_g04_fails_for_tool_specific_content(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nRun `python ecossistema.py audit`.\n")
    result = check_g04_agents_md_generic(tmp_path)
    assert result.status == "FAIL"


def test_g04_skips_when_no_agents_md(tmp_path: Path) -> None:
    result = check_g04_agents_md_generic(tmp_path)
    assert result.status == "SKIP"


# --- G05-G09: Execution directives -------------------------------------------


def test_g05_passes_with_thinking_constraint(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nThinking constraint: Think strictly in compact English.\n")
    result = check_g05_thinking_constraint(tmp_path)
    assert result.status == "PASS"


def test_g05_fails_without_thinking_constraint(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nSome other rule.\n")
    result = check_g05_thinking_constraint(tmp_path)
    assert result.status == "FAIL"


def test_g06_passes_with_step_limit(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nExecution limit: 3 to 5 steps.\n")
    result = check_g06_execution_limit(tmp_path)
    assert result.status == "PASS"


def test_g07_passes_with_silent_executor(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nOutput format: Silent executor.\n")
    result = check_g07_output_format(tmp_path)
    assert result.status == "PASS"


def test_g08_passes_with_bash_rule(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nBash rule: Always pipe to tail/grep.\n")
    result = check_g08_bash_rule(tmp_path)
    assert result.status == "PASS"


def test_g09_passes_with_graph_first(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nGraph-first: query code-review-graph.\n")
    result = check_g09_graph_first(tmp_path)
    assert result.status == "PASS"


# --- G10: Context budget -----------------------------------------------------


def test_g10_passes_when_under_budget(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "short content\n")
    result = check_g10_context_budget(tmp_path)
    assert result.status == "PASS"


def test_g10_fails_when_over_budget(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "x" * ((MAX_CONTEXT_TOKENS + 1) * CHARS_PER_TOKEN))
    result = check_g10_context_budget(tmp_path)
    assert result.status == "FAIL"


def test_g10_skips_when_no_agents_md(tmp_path: Path) -> None:
    result = check_g10_context_budget(tmp_path)
    assert result.status == "SKIP"


# --- G11: Skills frontmatter -------------------------------------------------


def test_g11_passes_for_single_line_description(tmp_path: Path) -> None:
    _write(tmp_path / "my-skill" / "SKILL.md", "---\ndescription: A short skill description\n---\n# Skill\n")
    result = check_g11_skills_frontmatter(tmp_path)
    assert result.status == "PASS"


def test_g11_fails_for_long_description(tmp_path: Path) -> None:
    long_desc = "word " * 25  # 25 words, exceeds limit of 20
    content = f'---\ndescription: "{long_desc.strip()}"\n---\n# Skill\n'
    _write(tmp_path / "my-skill" / "SKILL.md", content)
    result = check_g11_skills_frontmatter(tmp_path)
    assert result.status == "FAIL"


def test_g11_skips_when_no_skills(tmp_path: Path) -> None:
    result = check_g11_skills_frontmatter(tmp_path)
    assert result.status == "SKIP"


# --- G12: .gitignore ---------------------------------------------------------


def test_g12_passes_with_required_patterns(tmp_path: Path) -> None:
    _write(tmp_path / ".gitignore", "node_modules/\n")
    result = check_g12_gitignore(tmp_path)
    assert result.status == "PASS"


def test_g12_does_not_require_ignoring_lockfiles(tmp_path: Path) -> None:
    # Regressao: exigir lockfiles no .gitignore quebrava `npm ci` (caso rotaprime-replica).
    _write(tmp_path / ".gitignore", "node_modules/\n")
    result = check_g12_gitignore(tmp_path)
    assert result.status == "PASS"
    assert "lock" not in result.details


def test_g12_fails_when_missing_patterns(tmp_path: Path) -> None:
    _write(tmp_path / ".gitignore", "*.pyc\n")
    result = check_g12_gitignore(tmp_path)
    assert result.status == "FAIL"
    assert "node_modules" in result.details


def test_g12_fails_when_no_gitignore(tmp_path: Path) -> None:
    result = check_g12_gitignore(tmp_path)
    assert result.status == "FAIL"


# --- G13: .gitattributes -----------------------------------------------------


def test_g13_passes_with_lf_enforcement(tmp_path: Path) -> None:
    _write(tmp_path / ".gitattributes", "* text=auto eol=lf\n")
    result = check_g13_gitattributes(tmp_path)
    assert result.status == "PASS"


def test_g13_fails_without_lf(tmp_path: Path) -> None:
    _write(tmp_path / ".gitattributes", "*.py linguist-language=Python\n")
    result = check_g13_gitattributes(tmp_path)
    assert result.status == "FAIL"


def test_g13_fails_when_missing(tmp_path: Path) -> None:
    result = check_g13_gitattributes(tmp_path)
    assert result.status == "FAIL"


# --- G14: No duplicates ------------------------------------------------------


def test_g14_passes_without_componentes(tmp_path: Path) -> None:
    result = check_g14_no_duplicates(tmp_path)
    assert result.status == "PASS"


def test_g14_passes_when_no_duplicates(tmp_path: Path) -> None:
    _write(tmp_path / "componentes" / "skill" / "SKILL.md", "# Skill\n")
    _write(tmp_path / ".agent" / "skills" / "other" / "SKILL.md", "# Other\n")
    result = check_g14_no_duplicates(tmp_path)
    assert result.status == "PASS"


def test_g14_warns_on_duplicates(tmp_path: Path) -> None:
    _write(tmp_path / "componentes" / "skill" / "SKILL.md", "# Skill\n")
    _write(tmp_path / ".agent" / "skill" / "SKILL.md", "# Skill\n")
    result = check_g14_no_duplicates(tmp_path)
    assert result.status == "WARN"


def test_g14_detecta_duplicata_em_harness_que_faltava_na_lista_antiga(tmp_path: Path) -> None:
    # Achado real 2026-09-15: a lista hardcoded antiga so cobria .agent/.claude/
    # .cursor/.gemini/.mimocode — uma duplicata em .opencode/ passava batido.
    _write(tmp_path / "componentes" / "skill" / "SKILL.md", "# Skill\n")
    _write(tmp_path / ".opencode" / "skill" / "SKILL.md", "# Skill\n")
    result = check_g14_no_duplicates(tmp_path)
    assert result.status == "WARN"


# --- G15: Cache prefix -------------------------------------------------------


def test_g15_passes_without_timestamps(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nThink in compact English.\n")
    result = check_g15_cache_prefix(tmp_path)
    assert result.status == "PASS"


def test_g15_fails_with_timestamps(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nLast updated: 2024-01-15\n")
    result = check_g15_cache_prefix(tmp_path)
    assert result.status == "FAIL"


def test_g15_fails_with_absolute_paths(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# Rules\n\nConfig at C:\\Users\\test\\config\n")
    result = check_g15_cache_prefix(tmp_path)
    assert result.status == "FAIL"


def test_g15_skips_when_no_agents_md(tmp_path: Path) -> None:
    result = check_g15_cache_prefix(tmp_path)
    assert result.status == "SKIP"
