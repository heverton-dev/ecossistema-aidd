from pathlib import Path

import pytest

from aidd_forge.core.injector_profiles import (
    FORGE_PROFILE,
    TIPOS_SUPORTADOS,
    TipoDesconhecidoError,
    resolve_canonical_destination,
    resolve_destination,
    resolve_profile,
)


def test_todos_os_tipos_suportados_tem_perfil():
    for tipo in TIPOS_SUPORTADOS:
        assert tipo in FORGE_PROFILE


@pytest.mark.parametrize(
    "tipo,esperado",
    [
        ("skill", ".agent/skills/demo/SKILL.md"),
        ("mcp", "aidd_forge/mcps/demo.py"),
        ("rule", "docs/rules/demo.md"),
        ("spec", "docs/specs/demo.md"),
        ("roteiro", "tutoriais/demo.md"),
        ("config", "config/demo.json"),
        ("command", ".agent/commands/demo.md"),
        ("hook", ".agent/hooks/demo/hook.sh"),
        ("sub-agent", ".agent/agents/demo.md"),
        ("script", "scripts/demo.py"),
    ],
)
def test_resolve_destination_por_tipo(tmp_path: Path, tipo, esperado):
    dest = resolve_destination(tipo, "demo", tmp_path)

    assert dest == tmp_path / esperado


@pytest.mark.raiz_real
def test_resolve_canonical_destination():
    dest = resolve_canonical_destination("skill", "demo")
    assert dest is not None
    # Raiz real do monorepo possui gates/manifesto_harnesses.json
    monorepo_root = dest.parents[4]
    assert (monorepo_root / "gates" / "manifesto_harnesses.json").exists(), (
        f"Destino canonico resolveu para raiz invalida: {monorepo_root} (gates/manifesto_harnesses.json nao existe)"
    )
    assert dest == monorepo_root / "componentes" / "aidd-forge" / "skills" / "demo" / "SKILL.md"
    assert "tools/componentes" not in dest.as_posix()


def test_apenas_mcp_tem_registry():
    for tipo, profile in FORGE_PROFILE.items():
        if tipo == "mcp":
            assert profile.registry == "aidd_forge/mcps/registry.json"
        else:
            assert profile.registry is None


def test_apenas_rule_tem_anchor():
    for tipo, profile in FORGE_PROFILE.items():
        if tipo == "rule":
            assert profile.anchor == "AGENTS.md"
        else:
            assert profile.anchor is None


def test_tipo_desconhecido_levanta_erro(tmp_path: Path):
    with pytest.raises(TipoDesconhecidoError):
        resolve_profile("tipo_inexistente")

    with pytest.raises(TipoDesconhecidoError):
        resolve_destination("tipo_inexistente", "demo", tmp_path)

