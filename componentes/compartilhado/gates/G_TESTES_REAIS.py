#!/usr/bin/env python3
"""Quality Gate: executa a suite pytest e exige 100% de aprovacao (Zero Fail).

Roda `python -m pytest -q` no repositorio alvo. Se nenhum arquivo de teste
existir ainda, o gate passa com um aviso (nao ha o que ainda ser exigido
logo apos `forge init`); a partir do momento em que testes existem, a
suite inteira precisa passar — qualquer falha bloqueia o commit. Script
autonomo (usa apenas a stdlib para descoberta; delega a execucao ao
`pytest` do ambiente alvo via subprocess).

Uso: `python gates/G_TESTES_REAIS.py [repo_root]`
Saida: exit 0 (suite 100% verde ou sem testes) ou exit 1 (alguma falha).
"""

from __future__ import annotations

import subprocess
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


def _has_test_files(repo_root: Path) -> bool:
    for pattern in ("test_*.py", "*_test.py"):
        for path in repo_root.rglob(pattern):
            if not any(part in EXCLUDED_DIRS for part in path.relative_to(repo_root).parts):
                return True
    return False


def scan(repo_root: Path) -> GateResult:
    repo_root = Path(repo_root)

    if not _has_test_files(repo_root):
        return GateResult(passed=True, messages=["nenhum arquivo de teste encontrado, gate passa"])

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=repo_root, capture_output=True, text=True, timeout=600, check=False,
        )
    except FileNotFoundError:
        return GateResult(passed=False, messages=["pytest nao encontrado no ambiente alvo"])
    except subprocess.TimeoutExpired:
        return GateResult(passed=False, messages=["suite pytest excedeu o timeout de 600s"])

    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode == 0:
        return GateResult(passed=True, messages=["suite pytest 100% aprovada", output])

    return GateResult(passed=False, messages=[f"suite pytest falhou (exit {proc.returncode})", output])


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    repo_root = Path(argv[0]) if argv else Path.cwd()

    result = scan(repo_root)
    for message in result.messages:
        print(f"[G_TESTES_REAIS] {message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
