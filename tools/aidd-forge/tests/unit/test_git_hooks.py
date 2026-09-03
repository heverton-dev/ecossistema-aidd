from pathlib import Path

from aidd_forge.core.git_hooks import GATES_SUBDIR, HOOK_NAME, GitHooksInstaller

REAL_TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "aidd_forge" / "templates"

EXPECTED_GATES = (
    "G_BLOQUEAR_SEGREDOS.py",
    "G_CONTRACTS.py",
    "G_CYBERSECURITY_OWASP.py",
    "G_ESTRUTURA_AST.py",
    "G_HARNESS_COMPAT.py",
    "G_INJECT.py",
    "G_PERFORMANCE.py",
    "G_TESTES_REAIS.py",
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_git(target: Path) -> None:
    (target / ".git").mkdir(parents=True)


# --- Templates reais: os Quality Gates exigidos pela SPRINT 07 + Injetor Universal ---


def test_all_seven_gate_scripts_exist() -> None:
    gates_root = REAL_TEMPLATES_ROOT / GATES_SUBDIR
    found = sorted(p.name for p in gates_root.glob("G_*.py"))

    assert found == sorted(EXPECTED_GATES)


# --- GitHooksInstaller.run --------------------------------------------------


def test_run_copies_real_gates_into_target(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_git(target)

    result = GitHooksInstaller(REAL_TEMPLATES_ROOT, target).run()

    for name in EXPECTED_GATES:
        assert (target / GATES_SUBDIR / name).exists()
    assert result.gate_scripts == tuple(sorted(EXPECTED_GATES))


def test_run_installs_pre_commit_hook_when_git_dir_present(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_git(target)

    result = GitHooksInstaller(REAL_TEMPLATES_ROOT, target).run()

    hook_path = target / ".git" / "hooks" / HOOK_NAME
    assert result.hook_installed is True
    assert result.hook_path == hook_path
    assert hook_path.exists()
    assert "Quality Gates" in hook_path.read_text(encoding="utf-8")


def test_run_skips_hook_when_no_git_dir(tmp_path: Path) -> None:
    target = tmp_path / "project"

    result = GitHooksInstaller(REAL_TEMPLATES_ROOT, target).run()

    assert result.hook_installed is False
    assert result.hook_path is None
    assert result.skipped_reason is not None
    assert "git" in result.skipped_reason.lower()


def test_run_still_copies_gates_when_no_git_dir(tmp_path: Path) -> None:
    target = tmp_path / "project"

    result = GitHooksInstaller(REAL_TEMPLATES_ROOT, target).run()

    assert result.gates_injection.created
    assert (target / GATES_SUBDIR / "G_ESTRUTURA_AST.py").exists()


def test_run_is_idempotent_without_force(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_git(target)
    installer = GitHooksInstaller(REAL_TEMPLATES_ROOT, target)
    installer.run()

    result = installer.run()

    assert result.hook_installed is False
    assert "ja existe" in result.skipped_reason
    assert not result.gates_injection.created
    assert result.gates_injection.skipped


def test_run_overwrites_hook_with_force(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_git(target)
    hook_path = target / ".git" / "hooks" / HOOK_NAME
    _write(hook_path, "#!/bin/sh\necho custom hook\n")

    result = GitHooksInstaller(REAL_TEMPLATES_ROOT, target, force=True).run()

    assert result.hook_installed is True
    assert "custom hook" not in hook_path.read_text(encoding="utf-8")


def test_run_resolves_worktree_gitdir_pointer_file(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir(parents=True)
    real_git_dir = tmp_path / "main-repo" / ".git" / "worktrees" / "project"
    real_git_dir.mkdir(parents=True)
    _write(target / ".git", f"gitdir: {real_git_dir}\n")

    result = GitHooksInstaller(REAL_TEMPLATES_ROOT, target).run()

    assert result.hook_installed is True
    assert result.hook_path == real_git_dir / "hooks" / HOOK_NAME
    assert (real_git_dir / "hooks" / HOOK_NAME).exists()


def test_run_raises_when_gates_templates_missing(tmp_path: Path) -> None:
    empty_templates = tmp_path / "templates"
    empty_templates.mkdir()
    target = tmp_path / "project"
    _init_git(target)

    try:
        GitHooksInstaller(empty_templates, target).run()
        assert False, "esperava FileNotFoundError"
    except FileNotFoundError:
        pass
