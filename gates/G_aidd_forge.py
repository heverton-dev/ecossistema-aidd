#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_aidd_forge (D13 / DoD 6)
=============================================================================
Quality Gate Determinístico de bootstrap do aidd-forge (Lei #8 / Lei #13).
Valida estritamente um alvo de bootstrap forge:
  1. Arquivo de governança AGENTS.md presente e não vazio.
  2. Gates do alvo: gates/G_*.py presente, sintaticamente válido e com
     caminho de falha explícito (Lei #13: portão que não morde é fachada).
  3. Hook pre-commit instalado em .git/hooks/pre-commit (alvo é repo git).
  4. Zero stubs: nenhum função/AST com corpo vazio, pass, ellipsis ou
     raise NotImplementedError (Lei #5).
  5. Rótulo honesto: nenhuma alegação ilusória (100% testado, zero bugs,
     certificação) em AGENTS.md/README*.md (Lei #8).

Critérios de Aceite:
  - Exit 0: alvo conforme em 100% dos critérios.
  - Exit 1: qualquer violação (alvo incompleto, stub, fachada, rótulo falso)
            ou entrada inválida (sem --alvo).
=============================================================================
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PADROES_ROTULO_ILUSORIO = [
    re.compile(r"100%\s*(de\s*)?testad", re.IGNORECASE),
    re.compile(r"\bzero\s+bugs?\b", re.IGNORECASE),
    re.compile(r"\bcertifica[çc][ãa]o\b", re.IGNORECASE),
]

PADROES_CAMINHO_DE_FALHA = [
    re.compile(r"\breturn\s+1\b"),
    re.compile(r"\bsys\.exit\(\s*1\s*\)"),
    re.compile(r"\bSystemExit\(\s*1\s*\)"),
]

_DIRS_EXCLUIDAS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def _iterar_arquivos_py(alvo: Path):
    for caminho in sorted(alvo.rglob("*.py")):
        if any(parte in _DIRS_EXCLUIDAS for parte in caminho.parts):
            continue
        yield caminho


def _corpo_apenas_stub(corpo: List[ast.stmt], docstring: bool) -> bool:
    restante = list(corpo)
    if docstring and restante:
        primeiro = restante[0]
        if (
            isinstance(primeiro, ast.Expr)
            and isinstance(primeiro.value, ast.Constant)
            and isinstance(primeiro.value.value, str)
        ):
            restante = restante[1:]
    if not restante:
        return True
    for no in restante:
        if isinstance(no, ast.Pass):
            continue
        if isinstance(no, ast.Expr) and isinstance(no.value, ast.Constant) and no.value.value is ...:
            continue
        if (
            isinstance(no, ast.Raise)
            and isinstance(no.exc, ast.Call)
            and isinstance(no.exc.func, ast.Name)
            and no.exc.func.id == "NotImplementedError"
        ):
            continue
        if (
            isinstance(no, ast.Raise)
            and isinstance(no.exc, ast.Name)
            and no.exc.id == "NotImplementedError"
        ):
            continue
        return False
    return True


def verificar_governanca(alvo: Path) -> List[str]:
    violacoes: List[str] = []
    agents = alvo / "AGENTS.md"
    if not agents.is_file() or not agents.read_text(encoding="utf-8", errors="replace").strip():
        violacoes.append("AGENTS.md ausente ou vazio (governança não injetada)")

    docs_texto = []
    if agents.is_file():
        docs_texto.append(agents.read_text(encoding="utf-8", errors="replace"))
    for readme in sorted(alvo.glob("README*.md")):
        docs_texto.append(readme.read_text(encoding="utf-8", errors="replace"))
    for texto in docs_texto:
        for padrao in PADROES_ROTULO_ILUSORIO:
            if padrao.search(texto):
                violacoes.append(
                    f"rótulo ilusório (Lei #8): padrão '{padrao.pattern}' em documento de governança"
                )
                break
    return violacoes


def verificar_gates_alvo(alvo: Path) -> List[str]:
    violacoes: List[str] = []
    gates_dir = alvo / "gates"
    if not gates_dir.is_dir():
        return ["diretório gates/ ausente no alvo"]

    arquivos_gate = sorted(gates_dir.glob("G_*.py"))
    if not arquivos_gate:
        return ["nenhum quality gate (G_*.py) presente no alvo"]

    for gate in arquivos_gate:
        texto = gate.read_text(encoding="utf-8", errors="replace")
        if not texto.strip():
            violacoes.append(f"gate vazio: {gate.name}")
            continue
        try:
            ast.parse(texto, filename=str(gate))
        except SyntaxError as exc:
            violacoes.append(f"gate com sintaxe inválida: {gate.name} ({exc.msg})")
            continue
        if not any(p.search(texto) for p in PADROES_CAMINHO_DE_FALHA):
            violacoes.append(
                f"gate sem caminho de falha explícito (Lei #13): {gate.name}"
            )
    return violacoes


def verificar_hook(alvo: Path) -> List[str]:
    if not (alvo / ".git").exists():
        hook_alt = alvo / "hooks" / "pre-commit"
        if hook_alt.is_file() and hook_alt.read_text(encoding="utf-8", errors="replace").strip():
            return []
        return ["alvo não é repositório git (hook pre-commit não instalável)"]
    hook = alvo / ".git" / "hooks" / "pre-commit"
    if not hook.is_file() or not hook.read_text(encoding="utf-8", errors="replace").strip():
        return ["hook .git/hooks/pre-commit ausente ou vazio"]
    return []


def verificar_stubs(alvo: Path) -> List[str]:
    violacoes: List[str] = []
    for caminho in _iterar_arquivos_py(alvo):
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        try:
            arvore = ast.parse(texto, filename=str(caminho))
        except SyntaxError as exc:
            violacoes.append(f"sintaxe inválida: {caminho.relative_to(alvo)} ({exc.msg})")
            continue
        for no in ast.walk(arvore):
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if _corpo_apenas_stub(no.body, docstring=True):
                    violacoes.append(
                        f"stub detectado (Lei #5): {caminho.relative_to(alvo)}::{no.name}"
                    )
    return violacoes


def validar_alvo(alvo: Path) -> Tuple[bool, List[str]]:
    """Retorna (aprovado, violacoes) com checagens 100% determinísticas."""
    if not alvo.is_dir():
        return False, [f"diretório alvo inexistente: {alvo}"]

    violacoes: List[str] = []
    violacoes.extend(verificar_governanca(alvo))
    violacoes.extend(verificar_gates_alvo(alvo))
    violacoes.extend(verificar_hook(alvo))
    violacoes.extend(verificar_stubs(alvo))
    return (not violacoes), violacoes


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python gates/G_aidd_forge.py",
        description="Quality Gate determinístico do bootstrap aidd-forge (D13)",
    )
    parser.add_argument("--alvo", required=True, help="Diretório do projeto alvo do forge")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 1

    aprovado, violacoes = validar_alvo(Path(args.alvo).resolve())
    if aprovado:
        print("[SUCESSO] Quality Gate G_aidd_forge APROVADO. EXIT 0")
        return 0
    for violacao in violacoes:
        print(f"[VIOLAÇÃO] {violacao}")
    print("[ERRO] Quality Gate G_aidd_forge REPROVADO. EXIT 1")
    return 1


if __name__ == "__main__":
    sys.exit(main())
