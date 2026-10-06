#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G_USER_FACING_PTBR.py — Quality Gate Determinístico (ISSUE-USA-0004 / Lei #1 + #13).

Bloqueia jargão não explicado em superfícies lidas pelo usuário leigo
(README.md, --help da CLI raiz, card de entrega / perfis de linguagem).

Exit 0: superfícies conformes (ou jargão sempre acompanhado de tradução).
Exit 1: jargão cru em superfície de usuário.
"""

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent

# Jargão proibido sem tradução imediata na mesma linha/parágrafo curto.
JARGAO = [
    "harness",
    "quality gate",
    "drift",
    "handoff",
    "worktree",
    "VSA",
    "fatia vertical",
    "pipeline",
    "orquestrador",
    "preflight",
    "E2E",
    "BDD",
    "SDD",
    "Quarteto Sine Qua Non",
]

# Linhas que já explicam o termo (glossário / tradução na primeira ocorrência).
EXPLICACAO = re.compile(
    r"(—|–|-|:|\(|=|\bou\b|\btambém chamado\b|\bex\.?:|\bpor exemplo\b|\bsigla de\b)",
    re.IGNORECASE,
)

ALVOS = [
    ROOT_DIR / "README.md",
    ROOT_DIR / "GEMINI.md",
]


def _linha_explicada(linha: str, termo: str) -> bool:
    if termo.lower() not in linha.lower():
        return True
    # aceita se a linha ensina o termo (glossário / definição)
    return bool(EXPLICACAO.search(linha))


def verificar_arquivo(path: Path) -> list[str]:
    erros = []
    if not path.is_file():
        return erros
    texto = path.read_text(encoding="utf-8", errors="ignore")
    # ignora blocos de código (comandos Na Casa)
    prosa = re.sub(r"```.*?```", "", texto, flags=re.DOTALL)
    for num, linha in enumerate(prosa.splitlines(), 1):
        for termo in JARGAO:
            if termo.lower() in linha.lower() and not _linha_explicada(linha, termo):
                erros.append(f"{path.name}:{num}: jargão cru '{termo}': {linha.strip()[:100]}")
    return erros


def verificar_perfil() -> list[str]:
    erros = []
    pf = ROOT_DIR / "scripts" / "preflight_host.py"
    if not pf.is_file():
        return ["scripts/preflight_host.py ausente"]
    t = pf.read_text(encoding="utf-8", errors="ignore")
    if "--perfil" not in t or "leigo" not in t:
        erros.append("scripts/preflight_host.py: flag --perfil leigo|tecnico ausente")
    return erros


def main() -> int:
    erros = []
    for alvo in ALVOS:
        erros.extend(verificar_arquivo(alvo))
    erros.extend(verificar_perfil())
    if erros:
        print("=" * 70)
        print("VIOLACAO [G_USER_FACING_PTBR]: jargão não explicado em superfície de usuário!")
        print("Regra (Rule 10 / perfil leigo): sigla traduzida na 1ª ocorrência; sem jargão cru.")
        print("=" * 70)
        for e in erros:
            print(f"- {e}")
        print(f"TOTAL VIOLATIONS: {len(erros)}")
        return 1
    print("[OK] G_USER_FACING_PTBR: superfícies de usuário em PT-BR simples com jargão explicado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
