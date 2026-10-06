# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_AST_BOUNDED_CONTEXT (Lei #2 & VSA)
=============================================================================
Analisa a AST de todos os módulos de modulos/ e bloqueia qualquer acoplamento
ou importação direta cruzada não-autorizada entre domínios independentes.

Exit Codes:
  0 = Aprovado (Bounded contexts 100% isolados).
  1 = Violação de regra (Acoplamento cruzado direto detectado).
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent


def verificar_bounded_context_vsa(raiz: Path) -> Tuple[bool, List[str]]:
    violacoes: List[str] = []
    modulos_dir = raiz / "modulos"

    if not modulos_dir.is_dir():
        return True, []

    for arq in modulos_dir.rglob("*.py"):
        partes = arq.parts
        if any(ign in partes for ign in (".git", ".pytest_cache", "__pycache__", "materiais-extras", "examples")):
            continue

        try:
            conteudo = arq.read_text(encoding="utf-8-sig", errors="replace")
            tree = ast.parse(conteudo, filename=str(arq))
        except Exception as e:
            violacoes.append(f"{arq}: falha ao analisar AST ({e})")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name.startswith("tools.") or (name.startswith("modulos.") and "compartilhado" not in name):
                        violacoes.append(f"{arq.relative_to(raiz)}: import direto ilegal '{name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module and (node.module.startswith("tools.") or (node.module.startswith("modulos.") and "compartilhado" not in node.module)):
                    violacoes.append(f"{arq.relative_to(raiz)}: from import ilegal '{node.module}'")

    return len(violacoes) == 0, violacoes


def main(args: List[str] = None) -> int:
    if args is None:
        args = sys.argv[1:]

    caminho = Path(args[0]) if args else ROOT_DIR
    aprovado, violacoes = verificar_bounded_context_vsa(caminho)

    if aprovado:
        print("[G_AST_BOUNDED_CONTEXT] APROVADO: Bounded contexts VSA 100% isolados.")
        return 0

    print("[G_AST_BOUNDED_CONTEXT] REPROVADO: Violações de bounded context detectadas:")
    for v in violacoes:
        print(f"  ✗ {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
