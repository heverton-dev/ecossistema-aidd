"""Testes unitarios dos 7 Quality Gates mecanicos (`templates/gates/`).

Cada gate e um script autonomo (sem `__init__.py`, nao faz parte do
pacote `aidd_forge`), entao os modulos sao carregados dinamicamente via
`importlib` a partir do caminho real do template.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

GATES_ROOT = Path(__file__).resolve().parents[2] / "aidd_forge" / "templates" / "gates"


def _load_gate(name: str) -> ModuleType:
    path = GATES_ROOT / name
    module_name = name.replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- G_ESTRUTURA_AST ---------------------------------------------------------


def test_ast_gate_passes_on_valid_python(tmp_path: Path) -> None:
    gate = _load_gate("G_ESTRUTURA_AST.py")
    _write(tmp_path / "ok.py", "def f():\n    return 1\n")

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_ast_gate_fails_on_syntax_error(tmp_path: Path) -> None:
    gate = _load_gate("G_ESTRUTURA_AST.py")
    _write(tmp_path / "broken.py", "def f(:\n    return 1\n")

    result = gate.scan(tmp_path)

    assert result.passed is False
    assert any("broken.py" in m for m in result.messages)


def test_ast_gate_ignores_excluded_dirs(tmp_path: Path) -> None:
    gate = _load_gate("G_ESTRUTURA_AST.py")
    _write(tmp_path / ".venv" / "lib" / "broken.py", "def f(:\n")

    result = gate.scan(tmp_path)

    assert result.passed is True


# --- G_BLOQUEAR_SEGREDOS -----------------------------------------------------


def test_secrets_gate_passes_on_clean_tree(tmp_path: Path) -> None:
    gate = _load_gate("G_BLOQUEAR_SEGREDOS.py")
    _write(tmp_path / "app.py", "def handler():\n    return 'ok'\n")

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_secrets_gate_blocks_aws_key(tmp_path: Path) -> None:
    gate = _load_gate("G_BLOQUEAR_SEGREDOS.py")
    _write(tmp_path / "config.py", 'AWS_KEY = "AKIAABCDEFGHIJKLMNOP"\n')

    result = gate.scan(tmp_path)

    assert result.passed is False
    assert any("config.py" in m for m in result.messages)


def test_secrets_gate_blocks_hardcoded_password(tmp_path: Path) -> None:
    gate = _load_gate("G_BLOQUEAR_SEGREDOS.py")
    _write(tmp_path / "settings.py", 'password = "hunter22222"\n')

    result = gate.scan(tmp_path)

    assert result.passed is False


def test_secrets_gate_ignores_placeholder_values(tmp_path: Path) -> None:
    gate = _load_gate("G_BLOQUEAR_SEGREDOS.py")
    _write(tmp_path / "settings.py", 'password = "changeme"\n')

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_secrets_gate_prefers_staged_files_over_full_tree(tmp_path: Path) -> None:
    gate = _load_gate("G_BLOQUEAR_SEGREDOS.py")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)

    _write(tmp_path / "clean.py", "x = 1\n")
    subprocess.run(["git", "add", "clean.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    _write(tmp_path / "clean.py", "x = 2\n")
    subprocess.run(["git", "add", "clean.py"], cwd=tmp_path, check=True)
    _write(tmp_path / "leaky_unstaged.py", 'password = "hunter22222"\n')

    result = gate.scan(tmp_path)

    assert result.passed is True


# --- G_HARNESS_COMPAT ---------------------------------------------------------


def test_harness_gate_fails_when_dirs_missing(tmp_path: Path) -> None:
    gate = _load_gate("G_HARNESS_COMPAT.py")

    result = gate.scan(tmp_path)

    assert result.passed is False


def test_harness_gate_passes_when_all_dirs_present(tmp_path: Path) -> None:
    gate = _load_gate("G_HARNESS_COMPAT.py")
    for name in (".agent", ".claude", ".cursor"):
        (tmp_path / name).mkdir()

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_harness_gate_fails_on_broken_symlink(tmp_path: Path) -> None:
    gate = _load_gate("G_HARNESS_COMPAT.py")
    for name in (".agent", ".claude", ".cursor"):
        (tmp_path / name).mkdir()

    link = tmp_path / ".agent" / "skills"
    try:
        link.symlink_to(tmp_path / "nao-existe", target_is_directory=True)
    except OSError:
        pytest.skip("symlinks nao suportados neste ambiente (Windows sem privilegio)")

    result = gate.scan(tmp_path)

    assert result.passed is False
    assert any("quebrado" in m for m in result.messages)


# --- G_CONTRACTS ---------------------------------------------------------------


def test_contracts_gate_passes_when_no_schemas(tmp_path: Path) -> None:
    gate = _load_gate("G_CONTRACTS.py")
    _write(tmp_path / "data.json", '{"foo": "bar"}\n')

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_contracts_gate_passes_on_valid_draft_2020_12_schema(tmp_path: Path) -> None:
    gate = _load_gate("G_CONTRACTS.py")
    _write(
        tmp_path / "schema.json",
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", '
        '"type": "object", "properties": {"a": {"type": "string"}}}\n',
    )

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_contracts_gate_fails_on_wrong_draft(tmp_path: Path) -> None:
    gate = _load_gate("G_CONTRACTS.py")
    _write(
        tmp_path / "schema.json",
        '{"$schema": "http://json-schema.org/draft-07/schema#", "type": "object"}\n',
    )

    result = gate.scan(tmp_path)

    assert result.passed is False


def test_contracts_gate_fails_on_invalid_json(tmp_path: Path) -> None:
    gate = _load_gate("G_CONTRACTS.py")
    _write(tmp_path / "broken.json", "{not valid json,,,}")

    result = gate.scan(tmp_path)

    assert result.passed is False


def test_contracts_gate_fails_on_duplicate_id(tmp_path: Path) -> None:
    gate = _load_gate("G_CONTRACTS.py")
    body = (
        '{{"$schema": "https://json-schema.org/draft/2020-12/schema", '
        '"$id": "https://example.com/dup", "type": "object"}}\n'
    )
    _write(tmp_path / "a.json", body.format())
    _write(tmp_path / "b.json", body.format())

    result = gate.scan(tmp_path)

    assert result.passed is False
    assert any("duplicado" in m for m in result.messages)


# --- G_CYBERSECURITY_OWASP -----------------------------------------------------


def test_owasp_gate_passes_on_clean_code(tmp_path: Path) -> None:
    gate = _load_gate("G_CYBERSECURITY_OWASP.py")
    _write(tmp_path / "app.py", "def add(a, b):\n    return a + b\n")

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_owasp_gate_blocks_eval(tmp_path: Path) -> None:
    gate = _load_gate("G_CYBERSECURITY_OWASP.py")
    _write(tmp_path / "app.py", "def run(cmd):\n    return eval(cmd)\n")

    result = gate.scan(tmp_path)

    assert result.passed is False


def test_owasp_gate_blocks_shell_true(tmp_path: Path) -> None:
    gate = _load_gate("G_CYBERSECURITY_OWASP.py")
    _write(
        tmp_path / "app.py",
        "import subprocess\nsubprocess.run(cmd, shell=True)\n",
    )

    result = gate.scan(tmp_path)

    assert result.passed is False


def test_owasp_gate_warns_but_passes_on_medium_severity(tmp_path: Path) -> None:
    gate = _load_gate("G_CYBERSECURITY_OWASP.py")
    _write(tmp_path / "app.py", "import hashlib\nhashlib.md5(b'x')\n")

    result = gate.scan(tmp_path)

    assert result.passed is True
    assert any("MEDIA" in m for m in result.messages)


def test_owasp_gate_does_not_flag_itself(tmp_path: Path) -> None:
    gate = _load_gate("G_CYBERSECURITY_OWASP.py")

    result = gate.scan(GATES_ROOT.parent.parent)

    assert result.passed is True


# --- G_TESTES_REAIS --------------------------------------------------------------


def test_testes_reais_gate_passes_when_no_tests(tmp_path: Path) -> None:
    gate = _load_gate("G_TESTES_REAIS.py")
    _write(tmp_path / "app.py", "x = 1\n")

    result = gate.scan(tmp_path)

    assert result.passed is True
    assert "nenhum arquivo de teste" in result.messages[0]


def test_testes_reais_gate_passes_when_suite_is_green(tmp_path: Path) -> None:
    gate = _load_gate("G_TESTES_REAIS.py")
    _write(tmp_path / "test_ok.py", "def test_ok():\n    assert 1 == 1\n")

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_testes_reais_gate_fails_when_suite_has_failures(tmp_path: Path) -> None:
    gate = _load_gate("G_TESTES_REAIS.py")
    _write(tmp_path / "test_bad.py", "def test_bad():\n    assert 1 == 2\n")

    result = gate.scan(tmp_path)

    assert result.passed is False


# --- G_PERFORMANCE ----------------------------------------------------------------


def test_performance_gate_passes_when_no_budget_configured(tmp_path: Path) -> None:
    gate = _load_gate("G_PERFORMANCE.py")

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_performance_gate_passes_within_budget(tmp_path: Path) -> None:
    gate = _load_gate("G_PERFORMANCE.py")
    budget = {
        "budgets": [
            {"name": "fast", "command": [sys.executable, "-c", "pass"], "max_ms": 60000}
        ]
    }
    import json

    _write(tmp_path / ".aidd" / "gates" / "performance_budget.json", json.dumps(budget))

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_performance_gate_fails_when_budget_exceeded(tmp_path: Path) -> None:
    gate = _load_gate("G_PERFORMANCE.py")
    budget = {
        "budgets": [
            {
                "name": "slow",
                "command": [sys.executable, "-c", "import time; time.sleep(0.2)"],
                "max_ms": 1,
            }
        ]
    }
    import json

    _write(tmp_path / ".aidd" / "gates" / "performance_budget.json", json.dumps(budget))

    result = gate.scan(tmp_path)

    assert result.passed is False


def test_performance_gate_fails_when_command_errors(tmp_path: Path) -> None:
    gate = _load_gate("G_PERFORMANCE.py")
    budget = {
        "budgets": [
            {"name": "broken", "command": [sys.executable, "-c", "import sys; sys.exit(1)"], "max_ms": 60000}
        ]
    }
    import json

    _write(tmp_path / ".aidd" / "gates" / "performance_budget.json", json.dumps(budget))

    result = gate.scan(tmp_path)

    assert result.passed is False


# --- G_INJECT -----------------------------------------------------------------


def test_inject_gate_passes_when_nothing_was_injected(tmp_path: Path) -> None:
    gate = _load_gate("G_INJECT.py")

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_inject_gate_passes_with_consistent_registry(tmp_path: Path) -> None:
    gate = _load_gate("G_INJECT.py")
    _write(tmp_path / "aidd_forge" / "mcps" / "demo.py", "def demo():\n    return 1\n")
    _write(
        tmp_path / "aidd_forge" / "mcps" / "registry.json",
        '[{"nome": "demo", "descricao": "x", "path": "aidd_forge/mcps/demo.py"}]\n',
    )

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_inject_gate_fails_when_registry_points_to_missing_file(tmp_path: Path) -> None:
    gate = _load_gate("G_INJECT.py")
    _write(
        tmp_path / "aidd_forge" / "mcps" / "registry.json",
        '[{"nome": "fantasma", "descricao": "x", "path": "aidd_forge/mcps/fantasma.py"}]\n',
    )

    result = gate.scan(tmp_path)

    assert result.passed is False
    assert any("fantasma" in msg for msg in result.messages)


def test_inject_gate_fails_when_registry_points_to_stub(tmp_path: Path) -> None:
    gate = _load_gate("G_INJECT.py")
    _write(tmp_path / "aidd_forge" / "mcps" / "demo.py", "pass")
    _write(
        tmp_path / "aidd_forge" / "mcps" / "registry.json",
        '[{"nome": "demo", "descricao": "x", "path": "aidd_forge/mcps/demo.py"}]\n',
    )

    result = gate.scan(tmp_path)

    assert result.passed is False


def test_inject_gate_passes_with_consistent_agents_md_table(tmp_path: Path) -> None:
    gate = _load_gate("G_INJECT.py")
    _write(tmp_path / "docs" / "rules" / "demo.md", "Regra real.\n")
    _write(
        tmp_path / "AGENTS.md",
        "# AGENTS.md\n\n"
        "## Componentes Injetados\n\n"
        "| Tipo | Nome | Descricao | Caminho |\n"
        "| --- | --- | --- | --- |\n"
        "| rule | demo | Demo | docs/rules/demo.md |\n",
    )

    result = gate.scan(tmp_path)

    assert result.passed is True


def test_inject_gate_fails_when_agents_md_table_points_to_missing_path(tmp_path: Path) -> None:
    gate = _load_gate("G_INJECT.py")
    _write(
        tmp_path / "AGENTS.md",
        "# AGENTS.md\n\n"
        "## Componentes Injetados\n\n"
        "| Tipo | Nome | Descricao | Caminho |\n"
        "| --- | --- | --- | --- |\n"
        "| rule | demo | Demo | docs/rules/demo.md |\n",
    )

    result = gate.scan(tmp_path)

    assert result.passed is False
