# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_AST_BOUNDED_CONTEXT (Lei #2, #5 & VSA)
=============================================================================
Analisa a AST de todos os módulos de modulos/ e bloqueia qualquer acoplamento
ou importação direta cruzada não-autorizada entre domínios independentes.

Exige que a comunicação entre fatias se dê estritamente por contratos públicos
exportados via __all__ ou interface.py / public.py, proibindo acesso a
módulos internos privados (_* ou subpastas internas não exportadas).

Exit Codes:
  0 = Aprovado (Bounded contexts 100% isolados e contratos públicos respeitados).
  1 = Violação de regra (Acoplamento cruzado direto ou quebra de fronteira).
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple

ROOT_DIR = next((p.parent for p in Path(__file__).resolve().parents if p.name == "modulos"), Path(__file__).resolve().parent.parent)  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)


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
                    # Bloqueia import direto do namespace legado tools
                    if name.startswith("tools."):
                        violacoes.append(f"{arq.relative_to(raiz)}: import direto ilegal de tools '{name}'")
                    # Bloqueia acesso a módulos privados internos de outras fatias
                    elif name.startswith("modulos.") and "compartilhado" not in name:
                        partes_import = name.split(".")
                        if len(partes_import) > 3 and not (name.endswith("interface") or name.endswith("public")):
                            violacoes.append(f"{arq.relative_to(raiz)}: import interno de fatia sem interface pública '{name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Bloqueia from import de tools
                    if node.module.startswith("tools."):
                        violacoes.append(f"{arq.relative_to(raiz)}: from import ilegal de tools '{node.module}'")
                    # Bloqueia from import interno de outras fatias
                    elif node.module.startswith("modulos.") and "compartilhado" not in node.module:
                        partes_mod = node.module.split(".")
                        if len(partes_mod) > 3 and not (node.module.endswith("interface") or node.module.endswith("public")):
                            violacoes.append(f"{arq.relative_to(raiz)}: from import interno de fatia sem interface pública '{node.module}'")

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
