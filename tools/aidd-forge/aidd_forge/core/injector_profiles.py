"""Matriz de perfis (Profiles) do Injetor Universal para o projeto `aidd-forge`.

Mapeia cada `tipo` de componente injetavel para seu destino fisico dentro do
projeto alvo, seguindo a convencao ja estabelecida no codigo real deste
repositorio (`.agent/skills/`, singular — nao a grafia `.agents/` do rascunho
do plano mestre) em vez de inventar uma nova.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

TIPOS_SUPORTADOS: tuple[str, ...] = ("skill", "mcp", "rule", "spec", "roteiro")


@dataclass(frozen=True)
class ComponentProfile:
    """Perfil de materializacao de um tipo de componente."""

    dest_template: str
    anchor: str | None = None
    registry: str | None = None


FORGE_PROFILE: dict[str, ComponentProfile] = {
    "skill": ComponentProfile(dest_template=".agent/skills/{nome}/SKILL.md"),
    "mcp": ComponentProfile(
        dest_template="aidd_forge/mcps/{nome}.py",
        registry="aidd_forge/mcps/registry.json",
    ),
    "rule": ComponentProfile(dest_template="docs/rules/{nome}.md", anchor="AGENTS.md"),
    "spec": ComponentProfile(dest_template="docs/specs/{nome}.md"),
    "roteiro": ComponentProfile(dest_template="tutoriais/{nome}.md"),
}


class TipoDesconhecidoError(ValueError):
    """Levantado quando `tipo` nao existe no `FORGE_PROFILE`."""


def resolve_profile(tipo: str) -> ComponentProfile:
    """Resolve o `ComponentProfile` de `tipo`; levanta se desconhecido."""
    try:
        return FORGE_PROFILE[tipo]
    except KeyError as exc:
        raise TipoDesconhecidoError(
            f"tipo '{tipo}' desconhecido; tipos suportados: {', '.join(TIPOS_SUPORTADOS)}"
        ) from exc


def resolve_destination(tipo: str, nome: str, target_root: Path) -> Path:
    """Resolve o caminho fisico absoluto do artefato `tipo`/`nome` no alvo."""
    profile = resolve_profile(tipo)
    return Path(target_root) / profile.dest_template.format(nome=nome)
