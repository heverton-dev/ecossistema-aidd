from pathlib import Path

import pytest

from aidd_forge.core.subagent_purger import MAX_PROMPT_CHARS, Result, SubagentPurger


def test_run_saves_valid_artifact_and_purges_session(tmp_path: Path) -> None:
    calls: list[str] = []

    def spawn_fn(prompt: str) -> str:
        calls.append(prompt)
        return "def hello():\n    return 'ola'\n"

    purger = SubagentPurger(spawn_fn)
    output_path = tmp_path / "artifact.py"

    result = purger.run("gere uma funcao hello", output_path)

    assert result.is_ok
    assert result.value == output_path
    assert output_path.read_text(encoding="utf-8") == "def hello():\n    return 'ola'\n"
    assert calls == ["gere uma funcao hello"]
    assert purger.session_active is False


def test_run_fails_on_invalid_ast_and_does_not_write_file(tmp_path: Path) -> None:
    def spawn_fn(prompt: str) -> str:
        return "def hello(:\n    invalid syntax"

    purger = SubagentPurger(spawn_fn)
    output_path = tmp_path / "artifact.py"

    result = purger.run("gere codigo quebrado", output_path)

    assert not result.is_ok
    assert "AST" in result.error
    assert not output_path.exists()
    assert purger.session_active is False


def test_run_fails_when_spawn_fn_raises(tmp_path: Path) -> None:
    def spawn_fn(prompt: str) -> str:
        raise RuntimeError("harness indisponivel")

    purger = SubagentPurger(spawn_fn)
    output_path = tmp_path / "artifact.py"

    result = purger.run("qualquer prompt", output_path)

    assert not result.is_ok
    assert "harness indisponivel" in result.error
    assert not output_path.exists()
    assert purger.session_active is False


def test_run_rejects_oversized_prompt_without_spawning(tmp_path: Path) -> None:
    spawned = False

    def spawn_fn(prompt: str) -> str:
        nonlocal spawned
        spawned = True
        return "x = 1\n"

    purger = SubagentPurger(spawn_fn)
    output_path = tmp_path / "artifact.py"
    oversized_prompt = "a" * (MAX_PROMPT_CHARS + 1)

    result = purger.run(oversized_prompt, output_path)

    assert not result.is_ok
    assert "limite" in result.error
    assert spawned is False
    assert not output_path.exists()


def test_session_active_is_false_before_run() -> None:
    purger = SubagentPurger(lambda prompt: "x = 1\n")
    assert purger.session_active is False


def test_result_ok_and_fail_are_mutually_exclusive() -> None:
    ok = Result.ok("artefato")
    fail = Result.fail("erro")

    assert ok.is_ok is True
    assert ok.value == "artefato"
    assert ok.error is None

    assert fail.is_ok is False
    assert fail.error == "erro"
    assert fail.value is None
