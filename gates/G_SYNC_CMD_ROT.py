#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G_SYNC_CMD_ROT.py - Quality Gate Deterministico (ISSUE-USA-0001 / Lei #1 + #13).

Bloqueia a forma incompleta de sincronizacao de componentes em docs vivos
e exige que o parser continue mapeando os aliases publicos.

Detecta:
1. `components sync` / `componentes sync` sem `--tipo` (ou token `todos`) na mesma linha.
2. Alias publicos ausentes do parser: top-level `sync` e flag `--tipos`.

Exit 0: conformidade total.
Exit 1: uma ou mais violacoes (arquivo:linha impressos).
"""

import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent

# Docs vivos que ensinam comandos ao usuario/agente.
ALVOS = [
    ROOT_DIR / "MEMORY.md",
    ROOT_DIR / "README.md",
    ROOT_DIR / "docs" / "protocolos",
    ROOT_DIR / "docs" / "livros",
    ROOT_DIR / "docs" / "explicacoes",
    ROOT_DIR / "docs" / "melhorias",
]

# Relatorios de diagnostico citam a forma errada como evidencia (Lei #8).
EXCLUIR_NOMES = (
    "RELATORIO-ACHADOS",
    "especificacao-tecnica-usabilidade",
)

RE_SYNC = re.compile(r"(components|componentes)\s+sync")
RE_ECOSSISTEMA = Path("ecossistema.py")
GESTOR = ROOT_DIR / "scripts" / "gestor_componentes.py"


def _iter_arquivos():
    for alvo in ALVOS:
        if alvo.is_file() and alvo.suffix == ".md":
            yield alvo
        elif alvo.is_dir():
            for arq in sorted(alvo.rglob("*.md")):
                if any(x in arq.name for x in EXCLUIR_NOMES):
                    continue
                if any(p in {".git", "__pycache__", "node_modules"} for p in arq.parts):
                    continue
                yield arq


def verificar_docs() -> list[str]:
    erros = []
    for arq in _iter_arquivos():
        try:
            linhas = arq.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for num, linha in enumerate(linhas, 1):
            if not RE_SYNC.search(linha):
                continue
            # Exige a flag --tipo na mesma linha (token 'todos' solto nao conta:
            # "todos os harnesses" e falso-positivo).
            if "--tipo" in linha:
                continue
            rel = arq.relative_to(ROOT_DIR) if arq.is_relative_to(ROOT_DIR) else arq
            erros.append(f"{rel}:{num}: forma incompleta de components sync: {linha.strip()[:120]}")
    return erros


def verificar_aliases() -> list[str]:
    erros = []
    eco = RE_ECOSSISTEMA if False else ROOT_DIR / "ecossistema.py"
    if not eco.is_file():
        return [f"arquivo ausente: {eco}"]
    texto = eco.read_text(encoding="utf-8", errors="ignore")
    if not re.search(r'"sync"\s*:\s*cmd_sync', texto):
        erros.append("ecossistema.py: alias top-level 'sync' -> cmd_sync nao mapeado")
    if "--tipos" not in texto:
        erros.append("ecossistema.py: flag --tipos (sinonimo de --tipo) ausente")
    if not GESTOR.is_file():
        erros.append(f"arquivo ausente: {GESTOR}")
    else:
        gtexto = GESTOR.read_text(encoding="utf-8", errors="ignore")
        if "--tipos" not in gtexto:
            erros.append("scripts/gestor_componentes.py: flag --tipos ausente")
    return erros


def main() -> int:
    erros = verificar_docs() + verificar_aliases()
    if erros:
        print("=" * 70)
        print("VIOLACAO [G_SYNC_CMD_ROT]: forma de sync incompleta ou alias desmapeado!")
        print("Forma canonica: python ecossistema.py components sync --tipo todos")
        print("=" * 70)
        for e in erros:
            print(f"- {e}")
        print(f"TOTAL VIOLATIONS: {len(erros)}")
        return 1
    print("[OK] G_SYNC_CMD_ROT: docs canonicos e aliases de sync conformes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
