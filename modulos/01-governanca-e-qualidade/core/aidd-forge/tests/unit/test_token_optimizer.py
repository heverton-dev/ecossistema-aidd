import shutil
from pathlib import Path

from aidd_forge.core.token_optimizer import (
    MARKER_BEGIN,
    MARKER_END,
    TokenOptimizerResult,
    has_triad_rule,
    inject_into_content,
    inject_into_file,
    inject_into_tree,
    render_triad_block,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- render_triad_block / has_triad_rule ----------------------------------


def test_render_triad_block_contains_markers_and_all_three_stages() -> None:
    block = render_triad_block()

    assert block.startswith(MARKER_BEGIN)
    assert block.rstrip().endswith(MARKER_END)
    assert "ENTRADA" in block
    assert "PROCESSAMENTO" in block
    assert "SAIDA" in block
    assert "PT-BR" in block


def test_has_triad_rule_detects_marker() -> None:
    assert has_triad_rule(render_triad_block()) is True
    assert has_triad_rule("# AGENTS.md\nregra qualquer") is False


# --- inject_into_content ---------------------------------------------------


def test_inject_into_content_appends_block_to_empty_content() -> None:
    result = inject_into_content("")

    assert has_triad_rule(result)


def test_inject_into_content_appends_block_to_existing_content() -> None:
    original = "# AGENTS.md\n\nregra existente\n"

    result = inject_into_content(original)

    assert result.startswith(original)
    assert has_triad_rule(result)


def test_inject_into_content_is_idempotent() -> None:
    once = inject_into_content("# AGENTS.md\n")
    twice = inject_into_content(once)

    assert once == twice
    assert twice.count(MARKER_BEGIN) == 1


def test_inject_into_content_handles_content_without_trailing_newline() -> None:
    result = inject_into_content("# AGENTS.md\nsem newline final")

    assert has_triad_rule(result)
    assert result.count(MARKER_BEGIN) == 1


# --- inject_into_file -------------------------------------------------------


def test_inject_into_file_writes_marker_and_returns_true(tmp_path: Path) -> None:
    path = tmp_path / "AGENTS.md"
    _write(path, "# AGENTS.md\nregra existente\n")

    injected = inject_into_file(path)

    assert injected is True
    assert has_triad_rule(path.read_text(encoding="utf-8"))


def test_inject_into_file_is_idempotent_on_second_call(tmp_path: Path) -> None:
    path = tmp_path / "AGENTS.md"
    _write(path, "# AGENTS.md\n")

    first = inject_into_file(path)
    second = inject_into_file(path)

    assert first is True
    assert second is False
    assert path.read_text(encoding="utf-8").count(MARKER_BEGIN) == 1


def test_inject_into_file_creates_file_when_missing(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "AGENTS.md"

    injected = inject_into_file(path)

    assert injected is True
    assert has_triad_rule(path.read_text(encoding="utf-8"))


# --- inject_into_tree --------------------------------------------------------


def test_inject_into_tree_injects_only_matching_filenames(tmp_path: Path) -> None:
    _write(tmp_path / "governance" / "AGENTS.md", "# AGENTS.md\n")
    _write(tmp_path / "governance" / "AGENTS-WORKFLOW.md", "# Workflow\n")
    _write(tmp_path / "governance" / "OTHER.md", "# Outro arquivo\n")

    result = inject_into_tree(tmp_path)

    assert isinstance(result, TokenOptimizerResult)
    injected_names = {p.name for p in result.injected}
    assert injected_names == {"AGENTS.md", "AGENTS-WORKFLOW.md"}
    other_content = (tmp_path / "governance" / "OTHER.md").read_text(encoding="utf-8")
    assert not has_triad_rule(other_content)


def test_inject_into_tree_across_multiple_phase_dirs(tmp_path: Path) -> None:
    _write(tmp_path / "phase_00_bootstrap" / "AGENTS.md", "# Fase 00\n")
    _write(tmp_path / "phase_01_requirements" / "AGENTS.md", "# Fase 01\n")

    result = inject_into_tree(tmp_path)

    assert len(result.injected) == 2
    for phase in ("phase_00_bootstrap", "phase_01_requirements"):
        content = (tmp_path / phase / "AGENTS.md").read_text(encoding="utf-8")
        assert has_triad_rule(content)


def test_inject_into_tree_reports_already_present_on_rerun(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# AGENTS.md\n")

    inject_into_tree(tmp_path)
    second_result = inject_into_tree(tmp_path)

    assert second_result.injected == []
    assert len(second_result.already_present) == 1


def test_inject_into_tree_real_governance_and_phase_templates(tmp_path: Path) -> None:
    real_templates_root = Path(__file__).resolve().parents[2] / "aidd_forge" / "templates"
    templates_copy = tmp_path / "templates"
    shutil.copytree(real_templates_root, templates_copy)

    result = inject_into_tree(templates_copy)

    touched = result.injected + result.already_present
    touched_names = {p.name for p in touched}
    assert "AGENTS.md" in touched_names
    for path in touched:
        assert has_triad_rule(path.read_text(encoding="utf-8"))
