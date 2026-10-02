#!/usr/bin/env python3
"""Quality Gate: garante compatibilidade ativa entre os harnesses de IDE.

Confere que `.agent/`, `.claude/` e `.cursor/` (as tres pastas de harness
injetadas pelo `aidd-forge`) existem e que nenhum symlink sob elas esta
quebrado (dangling) — o que indicaria drift entre a arvore de templates e
os artefatos vinculados. Script autonomo (zero dependencias externas) para
poder ser copiado para qualquer projeto alvo.

Uso: `python gates/G_HARNESS_COMPAT.py [repo_root]`
Saida: exit 0 (harnesses provisionados e symlinks ativos) ou exit 1.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

HARNESS_DIRS: tuple[str, ...] = (".agent", ".claude", ".cursor")


@dataclass
class GateResult:
    passed: bool
    messages: list[str] = field(default_factory=list)


def _broken_symlinks(root: Path, repo_root: Path) -> list[str]:
    broken: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() and not path.exists():
            broken.append(f"{path.relative_to(repo_root)}: symlink quebrado (alvo ausente)")
    return broken


def scan(repo_root: Path, harness_dirs: tuple[str, ...] = HARNESS_DIRS) -> GateResult:
    repo_root = Path(repo_root)
    missing: list[str] = []
    broken: list[str] = []
    present: list[str] = []

    for name in harness_dirs:
        harness_root = repo_root / name
        if not harness_root.exists():
            missing.append(f"{name}/ nao provisionado (rode 'forge init')")
            continue
        present.append(name)
        broken.extend(_broken_symlinks(harness_root, repo_root))

    if missing or broken:
        return GateResult(passed=False, messages=[*missing, *broken])

    return GateResult(
        passed=True,
        messages=[f"harnesses ativos e sem symlinks quebrados: {', '.join(present)}"],
    )


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    repo_root = Path(argv[0]) if argv else Path.cwd()

    result = scan(repo_root)
    for message in result.messages:
        print(f"[G_HARNESS_COMPAT] {message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
