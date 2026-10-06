# -*- coding: utf-8 -*-
"""
Quality Gate Determinístico de Fronteira VSA.
Dimensão D13: Quality Gates (Portões).
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


def extrair_imports_arquivo(caminho: Path) -> List[str]:
    conteudo = caminho.read_text(encoding="utf-8-sig", errors="replace")
    arvore = ast.parse(conteudo)
    imports: List[str] = []
    for node in ast.walk(arvore):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def verificar_fronteiras_vsa(diretorio: Path) -> Tuple[bool, List[str]]:
    diretorio = Path(diretorio).resolve()
    violacoes: List[str] = []

    # Alvo principal da checagem: modulos/ (se existir) ou o diretório especificado
    alvo = diretorio / "modulos" if (diretorio / "modulos").is_dir() else diretorio

    for arq in alvo.rglob("*.py"):
        # Ignora pastas de cache, worktrees, venv ou testes de mock
        if any(ign in arq.parts for ign in (".git", ".pytest_cache", "__pycache__", "worktrees_", ".worktrees")):
            continue
        try:
            imports = extrair_imports_arquivo(arq)
            for imp in imports:
                if imp.startswith("tools.") or imp.startswith("components."):
                    violacoes.append(f"{arq.name}: import não autorizado de fronteira '{imp}'")
        except Exception as e:
            violacoes.append(f"{arq.name}: falha ao analisar AST ({e})")

    return len(violacoes) == 0, violacoes



def main(args: List[str] = None) -> int:
    if args is None:
        args = sys.argv[1:]

    caminho = Path(args[0]) if args else Path(".")
    aprovado, violacoes = verificar_fronteiras_vsa(caminho)

    if aprovado:
        print("[G_modularizacao_vsa] APROVADO: Nenhuma violação de fronteira VSA detectada.")
        return 0
    else:
        print(f"[G_modularizacao_vsa] REPROVADO: {len(violacoes)} violações de fronteira encontradas:")
        for v in violacoes:
            print(f"  - {v}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
