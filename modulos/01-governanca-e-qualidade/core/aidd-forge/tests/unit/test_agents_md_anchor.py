from pathlib import Path

from aidd_forge.core.agents_md_anchor import MARKER, ensure_component_table, render_component_table


def test_render_creates_section_when_marker_absent():
    original = "# AGENTS.md\n\nRegras basicas.\n"

    updated = render_component_table(
        original, tipo="skill", nome="demo", descricao="Demo", caminho=".agent/skills/demo/SKILL.md"
    )

    assert MARKER in updated
    assert "| skill | demo | Demo | .agent/skills/demo/SKILL.md |" in updated
    assert "Regras basicas." in updated


def test_render_upserts_existing_row_for_same_key():
    original = render_component_table(
        "# AGENTS.md\n", tipo="skill", nome="demo", descricao="Original", caminho="a.md"
    )

    updated = render_component_table(original, tipo="skill", nome="demo", descricao="Nova", caminho="b.md")

    assert updated.count("| skill | demo |") == 1
    assert "| skill | demo | Nova | b.md |" in updated
    assert "Original" not in updated


def test_render_appends_new_row_without_touching_existing():
    original = render_component_table(
        "# AGENTS.md\n", tipo="skill", nome="alpha", descricao="A", caminho="a.md"
    )

    updated = render_component_table(original, tipo="mcp", nome="beta", descricao="B", caminho="b.py")

    assert "| skill | alpha | A | a.md |" in updated
    assert "| mcp | beta | B | b.py |" in updated


def test_ensure_component_table_writes_file_and_reports_change(tmp_path: Path):
    changed = ensure_component_table(
        tmp_path, tipo="rule", nome="demo", descricao="Demo", caminho="docs/rules/demo.md"
    )

    agents_path = tmp_path / "AGENTS.md"
    assert changed is True
    assert agents_path.exists()
    assert "docs/rules/demo.md" in agents_path.read_text(encoding="utf-8")


def test_ensure_component_table_is_noop_when_unchanged(tmp_path: Path):
    ensure_component_table(tmp_path, tipo="rule", nome="demo", descricao="Demo", caminho="docs/rules/demo.md")

    changed = ensure_component_table(
        tmp_path, tipo="rule", nome="demo", descricao="Demo", caminho="docs/rules/demo.md"
    )

    assert changed is False
