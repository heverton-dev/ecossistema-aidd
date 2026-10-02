#!/usr/bin/env python3
"""Quality Gate: varredura estatica de vulnerabilidades OWASP Top 10.

Regex-scan sobre todo `.py` do repositorio em busca de padroes de alto
risco (execucao dinamica, injecao de comando/SQL, deserializacao insegura,
TLS desabilitado). Padroes ALTA severidade bloqueiam o commit; padroes
MEDIA severidade (ex.: hashing fraco) sao reportados como aviso sem
bloquear, para evitar falsos-positivos excessivos. Script autonomo (zero
dependencias externas) para poder ser copiado para qualquer projeto alvo.

Uso: `python gates/G_CYBERSECURITY_OWASP.py [repo_root]`
Saida: exit 0 (sem achados de alta severidade) ou exit 1 (bloqueia).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache",
    # "gates": os proprios scripts de gate contem os padroes de regex como
    # literais de string, o que dispara falso-positivo contra si mesmo.
    "gates",
}

# (nome, regex, severidade) — severidade "alta" bloqueia; "media" so avisa.
PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("eval() dinamico", re.compile(r"\beval\s*\("), "alta"),
    ("exec() dinamico", re.compile(r"\bexec\s*\("), "alta"),
    ("os.system (injecao de comando)", re.compile(r"\bos\.system\s*\("), "alta"),
    ("subprocess com shell=True", re.compile(r"shell\s*=\s*True"), "alta"),
    ("pickle.load(s) inseguro", re.compile(r"\bpickle\.loads?\s*\("), "alta"),
    (
        "yaml.load sem SafeLoader",
        re.compile(r"\byaml\.load\s*\((?!.*SafeLoader)"),
        "alta",
    ),
    ("verificacao TLS desabilitada", re.compile(r"verify\s*=\s*False"), "alta"),
    (
        "SQL possivelmente concatenado/interpolado",
        re.compile(
            r"(?i)(SELECT|INSERT|UPDATE|DELETE)\b[^\"'\n]{0,200}['\"]\s*(\+|%|f['\"])"
        ),
        "alta",
    ),
    ("hashlib.md5 (hash fraco)", re.compile(r"\bhashlib\.md5\s*\("), "media"),
    ("hashlib.sha1 (hash fraco)", re.compile(r"\bhashlib\.sha1\s*\("), "media"),
)


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
    high: list[str] = []
    medium: list[str] = []

    for path in _iter_python_files(repo_root):
        rel = path.relative_to(repo_root)
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        for line_no, line in enumerate(lines, start=1):
            for name, pattern, severity in PATTERNS:
                if pattern.search(line):
                    entry = f"{rel}:{line_no}: {name}"
                    (high if severity == "alta" else medium).append(entry)

    messages = [f"[ALTA] {m}" for m in high] + [f"[MEDIA] {m}" for m in medium]
    if high:
        return GateResult(passed=False, messages=messages)

    if medium:
        messages.append("nenhum achado de alta severidade (avisos de media severidade acima)")
    else:
        messages.append("nenhuma vulnerabilidade estatica encontrada")
    return GateResult(passed=True, messages=messages)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    repo_root = Path(argv[0]) if argv else Path.cwd()

    result = scan(repo_root)
    for message in result.messages:
        print(f"[G_CYBERSECURITY_OWASP] {message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
