"""Sincronizador Multi-Harness: espelha uma skill ou command injetado nos harnesses ativos.

Ambos reaproveitam o mesmo contrato de `Injector.link_skills` (symlink com
fallback para copia quando o SO nao permite), mas para um unico componente
recem-materializado em vez de uma arvore inteira de templates.

Espelham INCONDICIONALMENTE em TODOS os harnesses confirmados no manifesto
canonico (`aidd_forge.core.harness_manifest`), igual ao que `SlashRouter` ja
faz para `/forge`/`/aidd-init` — um componente injetado deve ficar tao
descobrivel quanto os comandos de bootstrap, independente de qual harness o
usuario abrir depois (cria a pasta do harness se ela ainda nao existir).

Achados reais (2026-09-15): sem isso, `forge inject command` so gravava um
unico arquivo em `.agent/commands/` (invisivel pra qualquer harness real), e
`sincronizar_skill` tinha uma lista propria de so 3 harnesses (faltavam
Antigravity/OpenCode/CodeBuddy) e so espelhava em pastas que ja existiam.
Gemini CLI e tratado a parte pra skills: nao le `SKILL.md` solto, exige o
formato de extensions (`extensions/<nome>/skills/<nome>` + um
`gemini-extension.json` proprio) — ver `carregar_skill_overrides_canonicos`.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from aidd_forge.core.harness_manifest import (
    carregar_command_dirs_canonicos,
    carregar_skill_dirs_canonicos,
    carregar_skill_overrides_canonicos,
)

CANONICAL_SKILLS_DIR = ".agent/skills"
CANONICAL_COMMANDS_DIR = ".agent/commands"


@dataclass
class HarnessSyncResult:
    """Resumo do espelhamento de um componente nos harnesses do alvo."""

    mirrored: list[Path] = field(default_factory=list)
    skipped_harnesses: list[str] = field(default_factory=list)


def _mirror_dir(canonical_dir: Path, mirror_path: Path, force: bool) -> Path | None:
    """Espelha um diretorio (symlink com fallback para copytree); None se pulado."""
    if mirror_path.exists() or mirror_path.is_symlink():
        if not force:
            return None
        if mirror_path.is_symlink() or mirror_path.is_file():
            mirror_path.unlink()
        else:
            shutil.rmtree(mirror_path)

    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        mirror_path.symlink_to(canonical_dir, target_is_directory=True)
    except OSError:
        shutil.copytree(canonical_dir, mirror_path)
    return mirror_path


def sincronizar_skill(nome: str, target_root: Path, force: bool = False) -> HarnessSyncResult:
    """Espelha `target_root/.agent/skills/<nome>` em TODOS os harnesses do manifesto.

    Nao pula harness cuja pasta ainda nao existe — cria as que faltarem. Para
    gemini-cli, usa o formato de extensions (pasta aninhada + manifesto
    `gemini-extension.json` proprio) em vez do template padrao.
    """
    target_root = Path(target_root)
    canonical_dir = target_root / CANONICAL_SKILLS_DIR / nome
    result = HarnessSyncResult()

    if not canonical_dir.exists():
        return result

    for harness_dir in carregar_skill_dirs_canonicos():
        mirror_path = target_root / harness_dir / nome
        mirrored = _mirror_dir(canonical_dir, mirror_path, force)
        if mirrored is not None:
            result.mirrored.append(mirrored)

    for override in carregar_skill_overrides_canonicos().values():
        dest_rel = override.dest_dir_template.replace("{nome}", nome)
        mirror_path = target_root / dest_rel
        mirrored = _mirror_dir(canonical_dir, mirror_path, force)
        if mirrored is not None:
            result.mirrored.append(mirrored)

        if override.manifesto_extra_path_template and override.manifesto_extra_conteudo_template:
            extra_path = target_root / override.manifesto_extra_path_template.replace("{nome}", nome)
            if not extra_path.exists() or force:
                conteudo = {
                    chave: (valor.replace("{nome}", nome) if isinstance(valor, str) else valor)
                    for chave, valor in override.manifesto_extra_conteudo_template.items()
                }
                extra_path.parent.mkdir(parents=True, exist_ok=True)
                extra_path.write_text(
                    json.dumps(conteudo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
                result.mirrored.append(extra_path)

    return result


def sincronizar_command(nome: str, target_root: Path, force: bool = False) -> HarnessSyncResult:
    """Espelha `target_root/.agent/commands/<nome>.md` em TODOS os harnesses do manifesto.

    Diferente de `sincronizar_skill`, nao pula harness cuja pasta ainda nao
    existe — cria as que faltarem, igual ao `SlashRouter` ja faz pro `/forge`.
    Um command injetado pelo usuario deve funcionar em qualquer harness que
    ele venha a usar depois, nao so nos que ja estavam presentes no momento
    da injecao.
    """
    target_root = Path(target_root)
    canonical_file = target_root / CANONICAL_COMMANDS_DIR / f"{nome}.md"
    result = HarnessSyncResult()

    if not canonical_file.exists():
        return result

    for harness_dir in carregar_command_dirs_canonicos():
        mirror_path = target_root / harness_dir / f"{nome}.md"
        if mirror_path == canonical_file:
            continue

        if mirror_path.exists() or mirror_path.is_symlink():
            if not force:
                continue
            mirror_path.unlink()

        mirror_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            mirror_path.symlink_to(canonical_file)
        except OSError:
            shutil.copy2(canonical_file, mirror_path)

        result.mirrored.append(mirror_path)

    return result
