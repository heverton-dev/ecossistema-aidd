#!/usr/bin/env python3
"""Quality Gate: valida os componentes gravados pelo Injetor Universal.

Confere que todo componente registrado em `aidd_forge/mcps/registry.json`
e/ou na tabela "Componentes Injetados" do `AGENTS.md` do alvo aponta para um
arquivo que de fato existe em disco e que nao e um stub vazio/placeholder.
Se nenhum dos dois artefatos existir, o gate aprova silenciosamente: ainda
nao houve nenhuma injecao neste projeto, o que nao e uma falha. Script
autonomo (zero dependencias externas) para poder ser copiado para qualquer
projeto alvo.

Uso: `python gates/G_INJECT.py [repo_root]`
Saida: exit 0 (nada injetado, ou tudo injetado consistente) ou exit 1.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REGISTRY_RELATIVE = Path("aidd_forge") / "mcps" / "registry.json"
ANCHOR_RELATIVE = Path("AGENTS.md")
MARKER = "## Componentes Injetados"
STUB_CONTEUDOS: frozenset[str] = frozenset({"", "pass", "todo", "..."})


@dataclass
class GateResult:
    passed: bool
    messages: list[str] = field(default_factory=list)


def _check_registry(repo_root: Path) -> list[str]:
    registry_path = repo_root / REGISTRY_RELATIVE
    if not registry_path.exists():
        return []

    try:
        entries = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{REGISTRY_RELATIVE}: JSON invalido ({exc})"]

    problems: list[str] = []
    for entry in entries:
        nome = entry.get("nome", "?")
        rel_path = entry.get("path")
        if not rel_path:
            problems.append(f"registry: entrada '{nome}' sem campo 'path'")
            continue

        artefato = repo_root / rel_path
        if not artefato.exists():
            problems.append(f"registry: '{nome}' aponta para arquivo inexistente: {rel_path}")
            continue

        conteudo = artefato.read_text(encoding="utf-8").strip().lower()
        if conteudo in STUB_CONTEUDOS:
            problems.append(f"registry: '{nome}' e um stub vazio/placeholder: {rel_path}")

    return problems


def _table_rows(anchor_path: Path) -> list[str]:
    text = anchor_path.read_text(encoding="utf-8")
    if MARKER not in text:
        return []

    _, _, tail = text.partition(MARKER)
    lines = tail.split("\n")

    idx = 0
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx < len(lines) and lines[idx].strip().startswith("|"):
        idx += 1  # cabecalho
    if idx < len(lines) and lines[idx].strip().startswith("|"):
        idx += 1  # separador

    rows: list[str] = []
    while idx < len(lines) and lines[idx].strip().startswith("|"):
        rows.append(lines[idx].strip())
        idx += 1
    return rows


def _check_anchor_table(repo_root: Path) -> list[str]:
    anchor_path = repo_root / ANCHOR_RELATIVE
    if not anchor_path.exists():
        return []

    problems: list[str] = []
    for row in _table_rows(anchor_path):
        cols = [c.strip() for c in row.strip("|").split("|")]
        if len(cols) < 4:
            problems.append(f"AGENTS.md: linha de componente mal formada: {row}")
            continue

        tipo, nome, _descricao, caminho = cols[0], cols[1], cols[2], cols[3]
        if not (repo_root / caminho).exists():
            problems.append(
                f"AGENTS.md: componente '{nome}' ({tipo}) aponta para caminho inexistente: {caminho}"
            )

    return problems


def scan(repo_root: Path) -> GateResult:
    repo_root = Path(repo_root)
    problems = _check_registry(repo_root) + _check_anchor_table(repo_root)

    if problems:
        return GateResult(passed=False, messages=problems)

    return GateResult(passed=True, messages=["nenhuma inconsistencia em componentes injetados"])


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    repo_root = Path(argv[0]) if argv else Path.cwd()

    result = scan(repo_root)
    for message in result.messages:
        print(f"[G_INJECT] {message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
