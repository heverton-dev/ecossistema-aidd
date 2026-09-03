from pathlib import Path

from aidd_forge.core.harness_sync import sincronizar_skill


def _create_skill(target_root: Path, nome: str) -> None:
    skill_dir = target_root / ".agent" / "skills" / nome
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Demo\n", encoding="utf-8")


def test_sincronizar_skill_espelha_apenas_harnesses_existentes(tmp_path: Path):
    _create_skill(tmp_path, "demo-skill")
    (tmp_path / ".claude").mkdir()

    resultado = sincronizar_skill("demo-skill", tmp_path)

    mirror = tmp_path / ".claude" / "skills" / "demo-skill"
    assert mirror in resultado.mirrored
    assert (mirror / "SKILL.md").exists()
    assert ".gemini" in resultado.skipped_harnesses
    assert ".mimocode" in resultado.skipped_harnesses
    assert not (tmp_path / ".gemini").exists()


def test_sincronizar_skill_noop_quando_skill_nao_existe(tmp_path: Path):
    (tmp_path / ".claude").mkdir()

    resultado = sincronizar_skill("inexistente", tmp_path)

    assert resultado.mirrored == []
    assert not (tmp_path / ".claude" / "skills").exists()


def test_sincronizar_skill_e_idempotente_sem_force(tmp_path: Path):
    _create_skill(tmp_path, "demo-skill")
    (tmp_path / ".claude").mkdir()

    sincronizar_skill("demo-skill", tmp_path)
    resultado = sincronizar_skill("demo-skill", tmp_path)

    assert resultado.mirrored == []
