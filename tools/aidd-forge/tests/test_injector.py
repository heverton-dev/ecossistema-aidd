from pathlib import Path

from aidd_forge.core.harness_manifest import (
    carregar_skill_dirs_canonicos,
    carregar_skill_overrides_canonicos,
)
from aidd_forge.core.injector import Injector


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_run_creates_files_and_dirs(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write(templates / "governance" / "AGENTS.md", "regra")

    target = tmp_path / "project"
    result = Injector(templates, target).run()

    assert (target / "governance" / "AGENTS.md").read_text(encoding="utf-8") == "regra"
    assert len(result.created) == 1
    assert not result.skipped


def test_run_never_overwrites_without_force(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write(templates / "AGENTS.md", "novo")

    target = tmp_path / "project"
    _write(target / "AGENTS.md", "existente do usuario")

    result = Injector(templates, target).run()

    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "existente do usuario"
    assert len(result.skipped) == 1
    assert not result.created


def test_run_overwrites_with_force(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write(templates / "AGENTS.md", "novo")

    target = tmp_path / "project"
    _write(target / "AGENTS.md", "antigo")

    result = Injector(templates, target, force=True).run()

    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "novo"
    assert len(result.overwritten) == 1


def test_link_ide_rules_creates_alias(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write(templates / "governance" / "AGENTS.md", "regra")

    target = tmp_path / "project"
    injector = Injector(templates, target)
    injector.run()
    result = injector.link_ide_rules({"CLAUDE.md": "governance/AGENTS.md"})

    alias = target / "CLAUDE.md"
    assert alias.exists()
    assert alias.read_text(encoding="utf-8") == "regra"
    assert len(result.created) == 1


def test_mirror_skills_all_harnesses_cobre_todos_harnesses_do_manifesto(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _write(target / "skills" / "demo-skill" / "SKILL.md", "# Demo\n")

    result = Injector(tmp_path / "templates", target).mirror_skills_all_harnesses()

    for harness_dir in carregar_skill_dirs_canonicos():
        mirror = target / harness_dir / "demo-skill"
        assert (mirror / "SKILL.md").exists()
        assert mirror in result.created

    gemini_override = carregar_skill_overrides_canonicos()["gemini-cli"]
    gemini_skill = target / gemini_override.dest_dir_template.replace("{nome}", "demo-skill")
    assert (gemini_skill / "SKILL.md").exists()

    gemini_manifesto = target / gemini_override.manifesto_extra_path_template.replace(
        "{nome}", "demo-skill"
    )
    assert gemini_manifesto.exists()
    assert '"demo-skill"' in gemini_manifesto.read_text(encoding="utf-8")


def test_mirror_skills_all_harnesses_e_idempotente_sem_force(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _write(target / "skills" / "demo-skill" / "SKILL.md", "# Demo\n")
    injector = Injector(tmp_path / "templates", target)

    injector.mirror_skills_all_harnesses()
    result = injector.mirror_skills_all_harnesses()

    assert not result.created
    assert result.skipped


def test_mirror_skills_all_harnesses_noop_sem_pasta_skills(tmp_path: Path) -> None:
    target = tmp_path / "project"

    result = Injector(tmp_path / "templates", target).mirror_skills_all_harnesses()

    assert not result.created
    assert not result.skipped
