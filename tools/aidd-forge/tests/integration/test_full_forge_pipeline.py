"""Teste de integracao: pipeline completo do AIDD Forge, ponta a ponta.

Executa `forge init` de verdade sobre um repositorio git real (subprocess
`git`, sem mocks), confirma que toda a arvore de governanca/fases/skills/
gates/hook e provisionada, e confirma que o hook `pre-commit` instalado
de fato bloqueia um commit real contendo um segredo e libera um commit
limpo — validando o ciclo completo descrito no plano de arquitetura
(SPRINT 01 a SPRINT 07).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from aidd_forge.cli import main

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git nao disponivel no PATH")

EXPECTED_SKILLS = (
    "caveman-ultra", "orca-orchestration", "impeccable-ui",
    "open-code-review", "post-mortem", "cybersecurity-audit",
)
EXPECTED_PHASES = (
    "phase_00_bootstrap", "phase_01_requirements", "phase_02_architecture",
    "phase_03_implementation", "phase_04_audit_security",
)
EXPECTED_GATES = (
    "G_BLOQUEAR_SEGREDOS.py", "G_CONTRACTS.py", "G_CYBERSECURITY_OWASP.py",
    "G_ESTRUTURA_AST.py", "G_HARNESS_COMPAT.py", "G_INJECT.py", "G_PERFORMANCE.py",
    "G_TESTES_REAIS.py",
)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _init_repo(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    _git(["init", "-q"], cwd=target)
    _git(["config", "user.email", "forge@test.local"], cwd=target)
    _git(["config", "user.name", "forge-test"], cwd=target)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- Bootstrap completo (SPRINT 01-06) --------------------------------------


def test_forge_init_provisions_the_entire_governance_tree(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_repo(target)

    exit_code = main(["init", str(target)])

    assert exit_code == 0
    assert (target / "governance" / "AGENTS.md").exists()
    assert (target / "CLAUDE.md").exists()
    assert (target / "orca" / "01_orca_inventory.json").exists()
    assert (target / "orca" / "02_routing_rules.json").exists()

    for phase in EXPECTED_PHASES:
        phase_dir = target / ".aidd" / "pipeline" / phase
        assert (phase_dir / "AGENTS.md").exists()
        assert (phase_dir / "mcp_config.json").exists()

    for skill in EXPECTED_SKILLS:
        assert (target / ".agent" / "skills" / skill / "SKILL.md").exists()

    for ide_dir in (".cursor/rules", ".claude/commands", ".agent/commands"):
        assert (target / ide_dir / "forge.md").exists()
        assert (target / ide_dir / "aidd-init.md").exists()


# --- Quality Gates + Git Hooks (SPRINT 07) ----------------------------------


def test_forge_init_installs_all_seven_gates_and_pre_commit_hook(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_repo(target)

    main(["init", str(target)])

    for gate_name in EXPECTED_GATES:
        gate_path = target / "gates" / gate_name
        assert gate_path.exists(), f"gate ausente: {gate_name}"

    hook_path = target / ".git" / "hooks" / "pre-commit"
    assert hook_path.exists()
    assert "Quality Gates" in hook_path.read_text(encoding="utf-8")


def test_freshly_bootstrapped_project_passes_every_gate(tmp_path: Path) -> None:
    """Um projeto recem-inicializado deve nascer 100% em conformidade consigo mesmo."""
    target = tmp_path / "project"
    _init_repo(target)
    main(["init", str(target)])

    hook_path = target / ".git" / "hooks" / "pre-commit"
    proc = subprocess.run(
        ["sh", str(hook_path)], cwd=target, capture_output=True, text=True,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Todos os Quality Gates aprovados" in proc.stdout


def test_pre_commit_hook_blocks_a_real_commit_with_a_secret(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_repo(target)
    main(["init", str(target)])

    _write(target / "leaky.py", 'api_key = "sk-live-1234567890abcdef"\n')
    _git(["add", "-A"], cwd=target)

    proc = subprocess.run(
        ["git", "commit", "-m", "leak"], cwd=target, capture_output=True, text=True,
    )

    assert proc.returncode != 0
    assert "G_BLOQUEAR_SEGREDOS" in (proc.stdout + proc.stderr)

    log = subprocess.run(["git", "log", "--oneline"], cwd=target, capture_output=True, text=True)
    assert log.stdout.strip() == ""


def test_pre_commit_hook_allows_a_clean_commit(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_repo(target)
    main(["init", str(target)])

    _write(target / "app.py", "def add(a, b):\n    return a + b\n")
    _git(["add", "-A"], cwd=target)

    proc = subprocess.run(
        ["git", "commit", "-m", "clean"], cwd=target, capture_output=True, text=True,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr

    log = subprocess.run(["git", "log", "--oneline"], cwd=target, capture_output=True, text=True)
    assert "clean" in log.stdout


def test_pre_commit_hook_blocks_commit_with_syntax_error(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_repo(target)
    main(["init", str(target)])

    _write(target / "broken.py", "def f(:\n    pass\n")
    _git(["add", "-A"], cwd=target)

    proc = subprocess.run(
        ["git", "commit", "-m", "broken"], cwd=target, capture_output=True, text=True,
    )

    assert proc.returncode != 0
    assert "G_ESTRUTURA_AST" in (proc.stdout + proc.stderr)


# --- Idempotencia e --force ---------------------------------------------------


def test_forge_init_is_idempotent_and_preserves_existing_hook(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_repo(target)
    main(["init", str(target)])
    hook_path = target / ".git" / "hooks" / "pre-commit"
    original_hook = hook_path.read_text(encoding="utf-8")

    exit_code = main(["init", str(target)])

    assert exit_code == 0
    assert hook_path.read_text(encoding="utf-8") == original_hook


def test_forge_init_force_reinstalls_gates_and_hook(tmp_path: Path) -> None:
    target = tmp_path / "project"
    _init_repo(target)
    main(["init", str(target)])

    hook_path = target / ".git" / "hooks" / "pre-commit"
    _write(hook_path, "#!/bin/sh\necho old custom hook\nexit 1\n")

    exit_code = main(["init", str(target), "--force"])

    assert exit_code == 0
    assert "old custom hook" not in hook_path.read_text(encoding="utf-8")
    assert "Quality Gates" in hook_path.read_text(encoding="utf-8")


# --- Injetor Universal (Fase 6: prova de fogo) -------------------------------


def test_forge_inject_creates_a_cybersecurity_skill_and_an_mcp_end_to_end(tmp_path: Path) -> None:
    """Injeta uma skill de ciberseguranca e um MCP num projeto real, e confere
    que o hook `pre-commit` real (com `G_INJECT.py` incluso) continua aprovando."""
    target = tmp_path / "project"
    _init_repo(target)
    main(["init", str(target)])

    skill_exit = main(
        [
            "inject",
            "skill",
            "seguranca-ciber",
            "--descricao",
            "Skill de auditoria de ciberseguranca",
            "--conteudo",
            "---\nname: seguranca-ciber\ndescription: Auditoria OWASP.\n---\n\n# Seguranca Ciber\n",
            "--path",
            str(target),
        ]
    )
    mcp_exit = main(
        [
            "inject",
            "mcp",
            "meu-mcp",
            "--descricao",
            "MCP de exemplo",
            "--conteudo",
            "def handler():\n    return {\"ok\": True}\n",
            "--path",
            str(target),
        ]
    )

    assert skill_exit == 0
    assert mcp_exit == 0
    assert (target / ".agent" / "skills" / "seguranca-ciber" / "SKILL.md").exists()
    assert (target / "aidd_forge" / "mcps" / "meu-mcp.py").exists()

    registry = json.loads((target / "aidd_forge" / "mcps" / "registry.json").read_text(encoding="utf-8"))
    assert registry == [{"nome": "meu-mcp", "descricao": "MCP de exemplo", "path": "aidd_forge/mcps/meu-mcp.py"}]

    _write(target / "app.py", "def add(a, b):\n    return a + b\n")
    _git(["add", "-A"], cwd=target)
    hook_path = target / ".git" / "hooks" / "pre-commit"
    proc = subprocess.run(["sh", str(hook_path)], cwd=target, capture_output=True, text=True)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Todos os Quality Gates aprovados" in proc.stdout
