from pathlib import Path

import pytest

from aidd_forge.core.context_linter import (
    CHARS_PER_TOKEN,
    MAX_CONTEXT_TOKENS,
    ContextLintReport,
    estimate_tokens,
    lint_file,
    lint_tree,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- estimate_tokens ---------------------------------------------------------


def test_estimate_tokens_uses_four_chars_per_token_heuristic() -> None:
    text = "a" * 4000

    assert estimate_tokens(text) == 1000


def test_estimate_tokens_empty_string_is_zero() -> None:
    assert estimate_tokens("") == 0


# --- lint_file -----------------------------------------------------------


def test_lint_file_returns_none_when_under_budget(tmp_path: Path) -> None:
    path = tmp_path / "AGENTS.md"
    _write(path, "regra curta\n")

    assert lint_file(path) is None


def test_lint_file_warns_when_over_budget(tmp_path: Path) -> None:
    path = tmp_path / "AGENTS.md"
    _write(path, "x" * ((MAX_CONTEXT_TOKENS + 1) * CHARS_PER_TOKEN))

    warning = lint_file(path)

    assert warning is not None
    assert warning.path == path
    assert warning.estimated_tokens > MAX_CONTEXT_TOKENS
    assert warning.max_tokens == MAX_CONTEXT_TOKENS


def test_lint_file_respects_custom_max_tokens(tmp_path: Path) -> None:
    path = tmp_path / "AGENTS.md"
    _write(path, "x" * 400)

    assert lint_file(path, max_tokens=50) is not None
    assert lint_file(path, max_tokens=1000) is None


def test_lint_file_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        lint_file(tmp_path / "missing.md")


# --- lint_tree -----------------------------------------------------------


def test_lint_tree_reports_only_files_over_budget(tmp_path: Path) -> None:
    _write(tmp_path / "governance" / "AGENTS.md", "curto\n")
    _write(
        tmp_path / "governance" / "AGENTS-WORKFLOW.md",
        "x" * ((MAX_CONTEXT_TOKENS + 1) * CHARS_PER_TOKEN),
    )

    report = lint_tree(tmp_path)

    assert isinstance(report, ContextLintReport)
    assert report.has_warnings is True
    warned_names = {w.path.name for w in report.warnings}
    assert warned_names == {"AGENTS-WORKFLOW.md"}


def test_lint_tree_ignores_filenames_outside_target_list(tmp_path: Path) -> None:
    _write(tmp_path / "OTHER.md", "x" * ((MAX_CONTEXT_TOKENS + 1) * CHARS_PER_TOKEN))

    report = lint_tree(tmp_path)

    assert report.has_warnings is False


def test_lint_tree_no_warnings_when_all_files_within_budget(tmp_path: Path) -> None:
    _write(tmp_path / "phase_00_bootstrap" / "AGENTS.md", "regra enxuta\n")

    report = lint_tree(tmp_path)

    assert report.has_warnings is False
    assert report.warnings == []


def test_lint_tree_scans_nested_phase_directories(tmp_path: Path) -> None:
    _write(tmp_path / "phase_00_bootstrap" / "AGENTS.md", "curto\n")
    _write(
        tmp_path / "phase_01_requirements" / "AGENTS.md",
        "x" * ((MAX_CONTEXT_TOKENS + 1) * CHARS_PER_TOKEN),
    )

    report = lint_tree(tmp_path)

    assert len(report.warnings) == 1
    assert report.warnings[0].path.parent.name == "phase_01_requirements"


def test_lint_tree_real_templates_stay_within_budget() -> None:
    real_templates_root = Path(__file__).resolve().parents[2] / "aidd_forge" / "templates"

    report = lint_tree(real_templates_root)

    assert report.has_warnings is False, [
        (w.path, w.estimated_tokens) for w in report.warnings
    ]
