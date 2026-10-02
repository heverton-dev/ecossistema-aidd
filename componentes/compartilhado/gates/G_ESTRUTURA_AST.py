#!/usr/bin/env python3
"""Quality Gate: valida a sintaxe de todo arquivo `.py` do repositorio.

Percorre a arvore e executa `ast.parse` em cada arquivo Python — deteccao
puramente mecanica de erros de sintaxe (SyntaxError/IndentationError), sem
executar nenhum codigo do repositorio. Script autonomo (zero dependencias
externas) para poder ser copiado para qualquer projeto alvo.

Uso: `python gates/G_ESTRUTURA_AST.py [repo_root]`
Saida: exit 0 (toda a arvore .py e valida) ou exit 1 (algum arquivo invalido).
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache",
}


@dataclass
class GateResult:
    passed: bool
    messages: list[str] = field(default_factory=list)


def _iter_python_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(repo_root.rglob("*.py")):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(repo_root).parts):
            continue
        files.append(path)
    return files


def scan(repo_root: Path) -> GateResult:
    repo_root = Path(repo_root)
    errors: list[str] = []
    checked = 0

    for path in _iter_python_files(repo_root):
        checked += 1
        rel = path.relative_to(repo_root)
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{rel}: nao foi possivel ler o arquivo ({exc})")
            continue

        try:
            ast.parse(source, filename=str(rel))
        except SyntaxError as exc:
            errors.append(f"{rel}:{exc.lineno}: {exc.msg}")

    if errors:
        return GateResult(passed=False, messages=errors)
    return GateResult(passed=True, messages=[f"{checked} arquivo(s) .py com sintaxe valida"])


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    repo_root = Path(argv[0]) if argv else Path.cwd()

    result = scan(repo_root)
    for message in result.messages:
        print(f"[G_ESTRUTURA_AST] {message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
