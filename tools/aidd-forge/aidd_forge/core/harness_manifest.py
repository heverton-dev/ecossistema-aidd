"""Fonte unica de pastas de comando/skill por harness.

Le `gates/manifesto_harnesses.json` (fonte unica de harnesses do ecossistema,
ja usada por `scripts/gestor_componentes.py` e `gates/G_HARNESS_COMPAT.py`) em
vez de cada consumidor manter sua propria lista hardcoded. Achado real
(2026-09-15): antes desta extracao, `slash_router.py` e `harness_sync.py`
tinham cada um sua propria copia, e ambas ja tinham ficado desatualizadas em
relacao ao manifesto (comandos: Cursor errado, faltavam 4 harnesses; skills:
faltavam Antigravity/OpenCode/CodeBuddy e so espelhava em harness que ja
existisse) — centralizar aqui evita que isso se repita.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Fallbacks minimos, usados so quando nao ha manifesto por perto (aidd-forge
# rodando standalone, fora do monorepo ecossistema-aidd).
FALLBACK_COMMAND_DIRS: tuple[str, ...] = (".cursor/commands", ".claude/commands")
FALLBACK_SKILL_DIRS: tuple[str, ...] = (".cursor/skills", ".claude/skills")
FALLBACK_HARNESS_PREFIXES: tuple[str, ...] = (".claude", ".cursor")


def default_manifesto_path() -> Path | None:
    """Acha `gates/manifesto_harnesses.json` na raiz do monorepo, se existir.

    Deste arquivo (`aidd_forge/core/harness_manifest.py`), a raiz do monorepo
    fica 4 niveis acima: core/ -> aidd_forge/ -> aidd-forge/ -> tools/ -> ecossistema-aidd/.
    """
    candidato = Path(__file__).resolve().parents[4] / "gates" / "manifesto_harnesses.json"
    return candidato if candidato.is_file() else None


def _carregar_manifesto(manifesto_path: Path | None) -> dict[str, Any] | None:
    if manifesto_path is None:
        manifesto_path = default_manifesto_path()
    if manifesto_path is None:
        return None
    try:
        return json.loads(manifesto_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _harnesses_sem_override(tipo_entry: dict[str, Any]) -> tuple[str, ...]:
    """Harnesses aplicaveis a um tipo, excluindo os que tem override especial de destino."""
    overrides = tipo_entry.get("dest_harness_template_overrides", {})
    return tuple(h for h in tipo_entry["harnesses_aplicaveis"] if h not in overrides)


def carregar_command_dirs_canonicos(manifesto_path: Path | None = None) -> tuple[str, ...]:
    """Deriva as pastas de comando reais (`{prefixo_pasta}/commands`) do manifesto.

    Le `tipos_componente.command` (harnesses aplicaveis aquele tipo — hoje
    exclui gemini-cli de proposito, que usa `.toml` em vez de `.md`) e monta
    a pasta de cada harness suportado. Sem manifesto legivel, cai no
    fallback minimo (Claude Code + Cursor).
    """
    manifesto = _carregar_manifesto(manifesto_path)
    if manifesto is None:
        return FALLBACK_COMMAND_DIRS
    try:
        tipo_command = manifesto["tipos_componente"]["command"]
        template = tipo_command["dest_harness_template"]
        pasta_template = template.rsplit("/{nome}", 1)[0]
        harnesses = manifesto["harnesses_suportados"]
        return tuple(
            pasta_template.replace("{prefixo_pasta}", harnesses[harness_id]["prefixo_pasta"])
            for harness_id in tipo_command["harnesses_aplicaveis"]
        )
    except (KeyError, TypeError):
        return FALLBACK_COMMAND_DIRS


def carregar_todos_prefixos_harness(manifesto_path: Path | None = None) -> tuple[str, ...]:
    """Todos os prefixos de pasta de harness confirmados (`.claude`, `.agents`, ...),
    independente de tipo de componente. Usado por checks genericos de higiene (ex:
    G14, que procura duplicatas entre `componentes/` e QUALQUER pasta de harness),
    diferente de `carregar_command_dirs_canonicos`/`carregar_skill_dirs_canonicos`
    (que sao especificos de um tipo e ja incluem o sufixo `/commands` ou `/skills`).
    """
    manifesto = _carregar_manifesto(manifesto_path)
    if manifesto is None:
        return FALLBACK_HARNESS_PREFIXES
    try:
        harnesses = manifesto["harnesses_suportados"]
        return tuple(cfg["prefixo_pasta"] for cfg in harnesses.values())
    except (KeyError, TypeError):
        return FALLBACK_HARNESS_PREFIXES


def carregar_skill_dirs_canonicos(manifesto_path: Path | None = None) -> tuple[str, ...]:
    """Deriva as pastas `{prefixo_pasta}/skills` dos harnesses SEM override especial.

    Hoje todos exceto gemini-cli, que exige o formato de extensions — ver
    `carregar_skill_overrides_canonicos`. Sem manifesto legivel, cai no
    fallback minimo (Claude Code + Cursor).
    """
    manifesto = _carregar_manifesto(manifesto_path)
    if manifesto is None:
        return FALLBACK_SKILL_DIRS
    try:
        tipo_skill = manifesto["tipos_componente"]["skill"]
        template = tipo_skill["dest_harness_template"]
        pasta_template = template.rsplit("/{nome}", 1)[0]
        harnesses = manifesto["harnesses_suportados"]
        return tuple(
            pasta_template.replace("{prefixo_pasta}", harnesses[harness_id]["prefixo_pasta"])
            for harness_id in _harnesses_sem_override(tipo_skill)
        )
    except (KeyError, TypeError):
        return FALLBACK_SKILL_DIRS


@dataclass(frozen=True)
class SkillHarnessOverride:
    """Destino especial de um harness cuja skill nao segue o template padrao.

    Hoje so o gemini-cli: pasta aninhada em `extensions/<nome>/skills/<nome>`
    em vez de `skills/<nome>` direto, mais um manifesto extra
    (`gemini-extension.json`) sem fonte 1:1 em `componentes/`.
    """

    dest_dir_template: str
    manifesto_extra_path_template: str | None = None
    manifesto_extra_conteudo_template: dict[str, Any] | None = None


def carregar_skill_overrides_canonicos(
    manifesto_path: Path | None = None,
) -> dict[str, SkillHarnessOverride]:
    """Deriva os overrides de destino de skill por harness (hoje so gemini-cli)."""
    manifesto = _carregar_manifesto(manifesto_path)
    if manifesto is None:
        return {}
    try:
        tipo_skill = manifesto["tipos_componente"]["skill"]
        overrides = tipo_skill.get("dest_harness_template_overrides", {})
        extras = tipo_skill.get("manifestos_extra_por_harness", {})
        harnesses = manifesto["harnesses_suportados"]

        resultado: dict[str, SkillHarnessOverride] = {}
        for harness_id, template in overrides.items():
            prefixo = harnesses[harness_id]["prefixo_pasta"]
            extra_cfg = extras.get(harness_id)
            extra_path_template = None
            extra_conteudo_template = None
            if extra_cfg:
                extra_path_template = extra_cfg["caminho_template"].replace(
                    "{prefixo_pasta}", prefixo
                )
                extra_conteudo_template = extra_cfg["conteudo_template"]
            resultado[harness_id] = SkillHarnessOverride(
                dest_dir_template=template.replace("{prefixo_pasta}", prefixo),
                manifesto_extra_path_template=extra_path_template,
                manifesto_extra_conteudo_template=extra_conteudo_template,
            )
        return resultado
    except (KeyError, TypeError):
        return {}
