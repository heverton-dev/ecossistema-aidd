from pathlib import Path

from aidd_forge.commands.slash_router import (
    IDE_COMMAND_DIRS,
    INTENT_ROUTER_MARKER,
    SLASH_COMMANDS,
    SlashRouter,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_run_writes_forge_and_aidd_init_in_every_ide_dir(tmp_path: Path) -> None:
    result = SlashRouter(tmp_path).run()

    for ide_dir in IDE_COMMAND_DIRS:
        for command in SLASH_COMMANDS:
            command_path = tmp_path / ide_dir / f"{command}.md"
            assert command_path.exists()
            assert "/forge" in command_path.read_text(encoding="utf-8") or "/aidd-init" in (
                command_path.read_text(encoding="utf-8")
            )

    assert len(result.created) == len(IDE_COMMAND_DIRS) * len(SLASH_COMMANDS)


def test_known_ide_dirs_include_cursor_claude_and_generic_agent() -> None:
    assert IDE_COMMAND_DIRS == (".cursor/rules", ".claude/commands", ".agent/commands")


def test_forge_command_content_mentions_cli_entrypoint(tmp_path: Path) -> None:
    SlashRouter(tmp_path).run()

    content = (tmp_path / ".claude" / "commands" / "forge.md").read_text(encoding="utf-8")
    assert "python -m aidd_forge.cli init" in content


def test_aidd_init_command_is_alias_of_forge(tmp_path: Path) -> None:
    SlashRouter(tmp_path).run()

    content = (tmp_path / ".cursor" / "rules" / "aidd-init.md").read_text(encoding="utf-8")
    assert "/forge" in content


def test_run_is_idempotent_without_force(tmp_path: Path) -> None:
    router = SlashRouter(tmp_path)
    router.run()

    result = router.run()

    assert not result.created
    assert result.skipped


def test_run_overwrites_with_force(tmp_path: Path) -> None:
    command_path = tmp_path / ".claude" / "commands" / "forge.md"
    _write(command_path, "conteudo antigo")

    result = SlashRouter(tmp_path, force=True).run()

    assert "conteudo antigo" not in command_path.read_text(encoding="utf-8")
    assert command_path in result.overwritten


def test_ensure_intent_router_injects_when_missing(tmp_path: Path) -> None:
    agents_path = tmp_path / "governance" / "AGENTS.md"
    _write(agents_path, "# AGENTS.md\n\nRegras basicas.\n")

    result = SlashRouter(tmp_path).run()

    updated = agents_path.read_text(encoding="utf-8")
    assert result.intent_router_injected is True
    assert INTENT_ROUTER_MARKER in updated
    assert "configurar este projeto com aidd" in updated


def test_ensure_intent_router_is_noop_when_already_present(tmp_path: Path) -> None:
    agents_path = tmp_path / "governance" / "AGENTS.md"
    _write(agents_path, f"# AGENTS.md\n\n{INTENT_ROUTER_MARKER}\n\nja existe.\n")
    original = agents_path.read_text(encoding="utf-8")

    result = SlashRouter(tmp_path).run()

    assert result.intent_router_injected is False
    assert agents_path.read_text(encoding="utf-8") == original


def test_ensure_intent_router_noop_when_agents_md_absent(tmp_path: Path) -> None:
    result = SlashRouter(tmp_path).run()

    assert result.intent_router_injected is False
    assert not (tmp_path / "governance" / "AGENTS.md").exists()
