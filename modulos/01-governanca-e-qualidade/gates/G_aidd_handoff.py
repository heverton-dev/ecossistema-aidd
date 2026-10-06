# -*- coding: utf-8 -*-
"""
Quality Gate determinístico para validação de artefato de handoff de sessão (D13 / Lei #9).
Regras:
- Arquivo alvo deve existir.
- Deve conter as 5 seções canônicas de handoff.
- Não deve conter código-fonte cru colado (def, class, import).
Retorna exit 0 para conformidade estrita e exit 1 para falha.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SECOES_CANONICAS = [
    "Initial Goal",
    "Completed Work",
    "Quality Gate State",
    "Next Actions",
    "Discovered Invariants & Gotchas",
]

PADRAO_CODIGO = re.compile(r"^\s*(def\s+\w+|class\s+\w+|import\s+\w+|from\s+\w+\s+import)", re.MULTILINE)


def validar_arquivo(caminho_arquivo: str | Path) -> int:
    p = Path(caminho_arquivo).resolve()
    if not p.exists():
        print(f"[G_aidd_handoff] EXIT 1: Arquivo '{p}' não encontrado.", file=sys.stderr)
        return 1

    try:
        texto = p.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[G_aidd_handoff] EXIT 1: Falha ao ler arquivo: {e}", file=sys.stderr)
        return 1

    faltando = []
    for secao in SECOES_CANONICAS:
        if not re.search(rf"^##\s+{re.escape(secao)}", texto, re.MULTILINE):
            faltando.append(secao)

    if faltando:
        print(f"[G_aidd_handoff] EXIT 1: Faltam seções obrigatórias: {faltando}", file=sys.stderr)
        return 1

    if PADRAO_CODIGO.search(texto):
        print("[G_aidd_handoff] EXIT 1: Código-fonte cru detectado no handoff.", file=sys.stderr)
        return 1

    print(f"[G_aidd_handoff] EXIT 0: Artefato de handoff 100% conforme: {p}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python G_aidd_handoff.py <caminho_do_arquivo.md>", file=sys.stderr)
        sys.exit(1)

    sys.exit(validar_arquivo(sys.argv[1]))
