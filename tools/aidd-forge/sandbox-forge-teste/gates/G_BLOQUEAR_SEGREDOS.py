#!/usr/bin/env python3
"""Quality Gate: bloqueia commits contendo segredos expostos.

Varre os arquivos staged (`git diff --cached`) — ou, se nao houver staging
(execucao manual/CI), a arvore inteira do repositorio — em busca de chaves
de API, tokens e senhas em texto plano. Script autonomo (zero dependencias
externas) para poder ser copiado para qualquer projeto alvo.

Uso: `python gates/G_BLOQUEAR_SEGREDOS.py [repo_root]`
Saida: exit 0 (nenhum segredo encontrado) ou exit 1 (bloqueia o commit).
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", "gates",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".woff", ".woff2",
    ".ttf", ".eot", ".so", ".dll", ".exe", ".pyc",
}

# (nome do padrao, regex) — padroes de alta confianca para segredos reais.
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Slack Token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("GitHub Token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("Private Key Block", re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA|PGP) PRIVATE KEY-----")),
    (
        "Credencial Hardcoded",
        re.compile(
            r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token)\b\s*[:=]\s*"
            r"['\"]([^'\"\s]{8,})['\"]"
        ),
    ),
)

PLACEHOLDER_VALUES = {
    "changeme", "xxxxxxxx", "your-api-key", "your_api_key", "placeholder",
    "example", "insert-here", "todo", "<secret>", "${secret}",
}


@dataclass
class GateResult:
    passed: bool
    messages: list[str] = field(default_factory=list)


def _staged_files(repo_root: Path) -> list[Path] | None:
    """Retorna arquivos staged via git, ou None se indisponivel/vazio."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=repo_root, capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if proc.returncode != 0:
        return None

    names = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not names:
        return None
    return [repo_root / name for name in names]


def _walk_tree(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(repo_root).parts):
            continue
        files.append(path)
    return files


def _candidate_files(repo_root: Path) -> list[Path]:
    staged = _staged_files(repo_root)
    if staged is not None:
        return [f for f in staged if f.is_file()]
    return _walk_tree(repo_root)


def _is_placeholder(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDER_VALUES


def scan(repo_root: Path) -> GateResult:
    repo_root = Path(repo_root)
    findings: list[str] = []

    for path in _candidate_files(repo_root):
        if path.suffix.lower() in BINARY_EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = path.relative_to(repo_root)
        for line_no, line in enumerate(content.splitlines(), start=1):
            for name, pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                if match.groups() and _is_placeholder(match.group(match.lastindex or 0)):
                    continue
                findings.append(f"{rel}:{line_no}: possivel segredo exposto ({name})")

    if findings:
        return GateResult(passed=False, messages=findings)
    return GateResult(passed=True, messages=["nenhum segredo exposto encontrado"])


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    repo_root = Path(argv[0]) if argv else Path.cwd()

    result = scan(repo_root)
    for message in result.messages:
        print(f"[G_BLOQUEAR_SEGREDOS] {message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
