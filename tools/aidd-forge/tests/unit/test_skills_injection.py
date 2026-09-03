from pathlib import Path

from aidd_forge.core.injector import Injector

REAL_TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "aidd_forge" / "templates"

EXPECTED_SKILLS = (
    "caveman-ultra",
    "orca-orchestration",
    "impeccable-ui",
    "open-code-review",
    "post-mortem",
    "cybersecurity-audit",
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_skill(templates_root: Path, name: str, body: str = "conteudo") -> None:
    _write(
        templates_root / "skills" / name / "SKILL.md",
        f"---\nname: {name}\ndescription: teste\n---\n\n{body}\n",
    )


# --- Templates reais: as 6 skills fisicas exigidas pela SPRINT 06 ---------


def test_all_six_skills_exist_with_valid_frontmatter() -> None:
    skills_root = REAL_TEMPLATES_ROOT / "skills"

    for name in EXPECTED_SKILLS:
        skill_md = skills_root / name / "SKILL.md"
        assert skill_md.exists(), f"faltando {skill_md}"

        content = skill_md.read_text(encoding="utf-8")
        assert content.startswith("---\n"), f"{name}: SKILL.md sem frontmatter"
        assert f"name: {name}" in content
        assert "description:" in content


def test_no_extra_or_missing_skill_directories() -> None:
    skills_root = REAL_TEMPLATES_ROOT / "skills"
    found = sorted(p.name for p in skills_root.iterdir() if p.is_dir())

    assert found == sorted(EXPECTED_SKILLS)


# --- link_skills: vinculador para a pasta canonica .agent/skills/ --------


def test_link_skills_creates_canonical_symlinks(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write_skill(templates, "caveman-ultra")
    _write_skill(templates, "post-mortem")

    target = tmp_path / "project"
    injector = Injector(templates, target)
    injector.run()
    result = injector.link_skills()

    canonical = target / ".agent" / "skills"
    for name in ("caveman-ultra", "post-mortem"):
        link = canonical / name
        assert link.exists()
        assert (link / "SKILL.md").read_text(encoding="utf-8").endswith("conteudo\n")
    assert len(result.created) == 2


def test_link_skills_ignores_directories_without_skill_md(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write_skill(templates, "caveman-ultra")
    _write(templates / "skills" / "nao-e-skill" / "README.md", "sem SKILL.md")

    target = tmp_path / "project"
    injector = Injector(templates, target)
    injector.run()
    result = injector.link_skills()

    canonical = target / ".agent" / "skills"
    assert (canonical / "caveman-ultra").exists()
    assert not (canonical / "nao-e-skill").exists()
    assert len(result.created) == 1


def test_link_skills_is_idempotent_without_force(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write_skill(templates, "caveman-ultra")

    target = tmp_path / "project"
    injector = Injector(templates, target)
    injector.run()
    injector.link_skills()

    result = injector.link_skills()

    assert not result.created
    assert result.skipped


def test_link_skills_overwrites_with_force(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write_skill(templates, "caveman-ultra", body="v2")

    target = tmp_path / "project"
    injector = Injector(templates, target, force=True)
    injector.run()
    injector.link_skills()

    _write_skill(templates, "caveman-ultra", body="v3")
    injector.run()
    result = injector.link_skills()

    link = target / ".agent" / "skills" / "caveman-ultra" / "SKILL.md"
    assert link.read_text(encoding="utf-8").endswith("v3\n")
    assert result.overwritten


def test_link_skills_returns_empty_result_when_skills_dir_missing(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write(templates / "governance" / "AGENTS.md", "regra")

    target = tmp_path / "project"
    injector = Injector(templates, target)
    injector.run()
    result = injector.link_skills()

    assert not result.created
    assert not result.skipped
    assert not (target / ".agent").exists()


def test_link_skills_on_real_templates_links_all_six(tmp_path: Path) -> None:
    target = tmp_path / "project"
    injector = Injector(REAL_TEMPLATES_ROOT, target)
    injector.run()
    result = injector.link_skills()

    canonical = target / ".agent" / "skills"
    linked = sorted(p.name for p in canonical.iterdir() if p.is_dir())

    assert linked == sorted(EXPECTED_SKILLS)
    assert len(result.created) == len(EXPECTED_SKILLS)
