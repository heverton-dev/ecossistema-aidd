"""Sincronizador Multi-Harness: espelha uma skill injetada nos harnesses ativos.

Reaproveita o mesmo contrato de `Injector.link_skills` (symlink de diretorio
com fallback para `copytree` quando o SO nao permite), mas para uma unica
skill recem-materializada em vez de uma arvore inteira de templates.
Autolimitado (self-healing): so espelha em harnesses que ja existem no alvo
(`.claude/`, `.gemini/`, `.mimocode/`) — nunca cria um harness que o usuario
nao provisionou via `forge init`.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

CANONICAL_SKILLS_DIR = ".agent/skills"
MIRROR_HARNESS_DIRS: tuple[str, ...] = (".claude", ".gemini", ".mimocode")


@dataclass
class HarnessSyncResult:
    """Resumo do espelhamento de uma skill nos harnesses ativos do alvo."""

    mirrored: list[Path] = field(default_factory=list)
    skipped_harnesses: list[str] = field(default_factory=list)


def sincronizar_skill(nome: str, target_root: Path, force: bool = False) -> HarnessSyncResult:
    """Espelha `target_root/.agent/skills/<nome>` nos harnesses ativos do alvo."""
    target_root = Path(target_root)
    canonical_dir = target_root / CANONICAL_SKILLS_DIR / nome
    result = HarnessSyncResult()

    if not canonical_dir.exists():
        return result

    for harness in MIRROR_HARNESS_DIRS:
        harness_root = target_root / harness
        if not harness_root.exists():
            result.skipped_harnesses.append(harness)
            continue

        mirror_path = harness_root / "skills" / nome
        if mirror_path.exists() or mirror_path.is_symlink():
            if not force:
                continue
            if mirror_path.is_symlink() or mirror_path.is_file():
                mirror_path.unlink()
            else:
                shutil.rmtree(mirror_path)

        mirror_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            mirror_path.symlink_to(canonical_dir, target_is_directory=True)
        except OSError:
            shutil.copytree(canonical_dir, mirror_path)

        result.mirrored.append(mirror_path)

    return result
