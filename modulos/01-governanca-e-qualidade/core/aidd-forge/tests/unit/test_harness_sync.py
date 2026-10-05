from pathlib import Path

from aidd_forge.core.harness_manifest import (
    carregar_command_dirs_canonicos,
    carregar_skill_dirs_canonicos,
    carregar_skill_overrides_canonicos,
)
from aidd_forge.core.harness_sync import sincronizar_command, sincronizar_skill


def _create_skill(target_root: Path, nome: str) -> None:
    skill_dir = target_root / ".agent" / "skills" / nome
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Demo\n", encoding="utf-8")


def test_sincronizar_skill_espelha_em_todos_harnesses_mesmo_sem_existir(tmp_path: Path):
    _create_skill(tmp_path, "demo-skill")
    # Nenhuma pasta de harness pre-existe no alvo — sincronizar_skill cria as
    # que faltarem, mesmo contrato do SlashRouter/sincronizar_command.

    resultado = sincronizar_skill("demo-skill", tmp_path)

    for harness_dir in carregar_skill_dirs_canonicos():
        mirror = tmp_path / harness_dir / "demo-skill"
        assert mirror in resultado.mirrored
        assert (mirror / "SKILL.md").exists()


def test_sincronizar_skill_gemini_cli_usa_formato_de_extensions(tmp_path: Path):
    _create_skill(tmp_path, "demo-skill")

    resultado = sincronizar_skill("demo-skill", tmp_path)

    overrides = carregar_skill_overrides_canonicos()
    assert "gemini-cli" in overrides
    override = overrides["gemini-cli"]

    mirror = tmp_path / override.dest_dir_template.replace("{nome}", "demo-skill")
    assert mirror in resultado.mirrored
    assert (mirror / "SKILL.md").exists()

    extra_path = tmp_path / override.manifesto_extra_path_template.replace("{nome}", "demo-skill")
    assert extra_path in resultado.mirrored
    assert extra_path.exists()
    conteudo = extra_path.read_text(encoding="utf-8")
    assert '"demo-skill"' in conteudo
    assert '"version"' in conteudo


def test_sincronizar_skill_noop_quando_skill_nao_existe(tmp_path: Path):
    resultado = sincronizar_skill("inexistente", tmp_path)

    assert resultado.mirrored == []
    assert not (tmp_path / ".claude" / "skills").exists()


def test_sincronizar_skill_e_idempotente_sem_force(tmp_path: Path):
    _create_skill(tmp_path, "demo-skill")

    sincronizar_skill("demo-skill", tmp_path)
    resultado = sincronizar_skill("demo-skill", tmp_path)

    assert resultado.mirrored == []


def _create_command(target_root: Path, nome: str) -> None:
    commands_dir = target_root / ".agent" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / f"{nome}.md").write_text(f"# /{nome}\n\nComando de demo.\n", encoding="utf-8")


def test_sincronizar_command_espelha_em_todos_harnesses_do_manifesto_mesmo_sem_existir(
    tmp_path: Path,
):
    _create_command(tmp_path, "demo-command")
    # Nenhuma pasta de harness pre-existe no alvo — diferente de sincronizar_skill,
    # sincronizar_command cria as que faltarem (mesmo contrato do SlashRouter).

    resultado = sincronizar_command("demo-command", tmp_path)

    dirs_canonicos = carregar_command_dirs_canonicos()
    assert dirs_canonicos, "manifesto de harnesses deveria estar acessivel no monorepo de teste"
    for harness_dir in dirs_canonicos:
        mirror = tmp_path / harness_dir / "demo-command.md"
        assert mirror in resultado.mirrored
        assert mirror.exists()
        assert "demo-command" in mirror.read_text(encoding="utf-8")


def test_sincronizar_command_noop_quando_command_nao_existe(tmp_path: Path):
    resultado = sincronizar_command("inexistente", tmp_path)

    assert resultado.mirrored == []


def test_sincronizar_command_e_idempotente_sem_force(tmp_path: Path):
    _create_command(tmp_path, "demo-command")

    sincronizar_command("demo-command", tmp_path)
    resultado = sincronizar_command("demo-command", tmp_path)

    assert resultado.mirrored == []


def test_sincronizar_command_sobrescreve_com_force(tmp_path: Path):
    _create_command(tmp_path, "demo-command")
    sincronizar_command("demo-command", tmp_path)

    canonical = tmp_path / ".agent" / "commands" / "demo-command.md"
    canonical.write_text("# /demo-command\n\nConteudo atualizado.\n", encoding="utf-8")

    resultado = sincronizar_command("demo-command", tmp_path, force=True)

    dirs_canonicos = carregar_command_dirs_canonicos()
    algum_atualizado = any(
        "atualizado" in (tmp_path / harness_dir / "demo-command.md").read_text(encoding="utf-8")
        for harness_dir in dirs_canonicos
    )
    assert algum_atualizado
    assert resultado.mirrored
