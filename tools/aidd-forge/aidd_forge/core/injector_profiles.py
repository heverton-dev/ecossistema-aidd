"""Matriz de perfis (Profiles) do Injetor Universal para o projeto `aidd-forge`.

Mapeia cada `tipo` de componente injetavel para seu destino fisico dentro do
projeto alvo, seguindo a convencao ja estabelecida no codigo real deste
repositorio (`.agent/skills/`, singular — nao a grafia `.agents/` do rascunho
do plano mestre) em vez de inventar uma nova.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import os
import subprocess
import sys

TIPOS_SUPORTADOS: tuple[str, ...] = (
    "skill",
    "mcp",
    "rule",
    "spec",
    "roteiro",
    "config",
    "command",
    "hook",
    "sub-agent",
    "script",
)

TIPOS_ECOSSISTEMA: frozenset[str] = frozenset({
    "skill",
    "mcp",
    "spec",
    "config",
    "command",
    "hook",
    "sub-agent",
    "script",
})


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
    "config": ComponentProfile(dest_template="config/{nome}.json"),
    "command": ComponentProfile(dest_template=".agent/commands/{nome}.md"),
    "hook": ComponentProfile(dest_template=".agent/hooks/{nome}/hook.sh"),
    "sub-agent": ComponentProfile(dest_template=".agent/agents/{nome}.md"),
    "script": ComponentProfile(dest_template="scripts/{nome}.py"),
}

CANONICAL_TEMPLATES: dict[str, str] = {
    "skill": "componentes/aidd-forge/skills/{nome}/SKILL.md",
    "mcp": "componentes/aidd-forge/mcps/{nome}/server.py",
    "rule": "docs/rules/{nome}.md",
    "spec": "componentes/aidd-forge/specs/{nome}.md",
    "roteiro": "tutoriais/{nome}.md",
    "config": "componentes/aidd-forge/config/{nome}.json",
    "command": "componentes/aidd-forge/comandos/{nome}.md",
    "hook": "componentes/aidd-forge/hooks/{nome}/hook.sh",
    "sub-agent": "componentes/aidd-forge/subagentes/{nome}.md",
    "script": "componentes/aidd-forge/scripts/{nome}.py",
}


def _default_ecossistema_root() -> Path:
    """Raiz real do monorepo ecossistema-aidd.

    Isolada numa funcao propria (em vez de inline em cada chamador) para que
    testes possam monkeypatchar este ponto unico e evitar gravar na arvore
    real do repositorio durante `pytest` (ver `conftest.py`).
    """
    return Path(__file__).resolve().parents[4]


def resolve_canonical_destination(tipo: str, nome: str, ecossistema_root: Path | None = None) -> Path | None:
    """Resolve o caminho do componente dentro de `componentes/aidd-forge/...`."""
    if tipo not in CANONICAL_TEMPLATES:
        return None
    if ecossistema_root is None:
        ecossistema_root = _default_ecossistema_root()
    return Path(ecossistema_root) / CANONICAL_TEMPLATES[tipo].format(nome=nome)


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


def sincronizar_componente(
    tipo: str,
    ferramenta: str = "aidd-forge",
    ecossistema_root: Path | None = None,
) -> int:
    """Executa a sincronizacao multi-harness via gestor unico de componentes.

    Dispara:
      python ecossistema.py components sync --tipo <tipo> --ferramenta <ferramenta>
    com fallback direto para importacao do modulo `gestor_componentes`.
    """
    if tipo not in TIPOS_ECOSSISTEMA:
        return 0

    if ecossistema_root is None:
        ecossistema_root = _default_ecossistema_root()

    script_ecossistema = ecossistema_root / "ecossistema.py"
    if script_ecossistema.exists():
        cmd = [
            sys.executable,
            str(script_ecossistema),
            "components",
            "sync",
            "--tipo",
            tipo,
            "--ferramenta",
            ferramenta,
        ]
        try:
            res = subprocess.run(cmd, cwd=str(ecossistema_root), capture_output=True, text=True)
            return res.returncode
        except Exception:
            pass

    # Fallback: import direto de scripts/gestor_componentes.py
    try:
        scripts_dir = str(ecossistema_root / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import gestor_componentes
        gestor_componentes.sync(tipo=tipo, ferramenta=ferramenta)
        return 0
    except Exception:
        return 1

