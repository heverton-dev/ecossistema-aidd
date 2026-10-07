# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD MASTER — AST IMPORT GUARD (Bounded Context Isolator)
=============================================================================
Analisa a AST de todos os arquivos em src/modules/ e bloqueia qualquer
importacao direta cruzada entre dominios de negocio distintos (ex: modulo crm
importando modulo erp diretamente sem passar pelo EventBus ou core).
"""

import ast
import os
import sys
from typing import List, Tuple


def check_module_isolation(modules_root: str) -> List[Tuple[str, int, str]]:
    """Varre src/modules e identifica violacoes de bounded context via AST."""
    violations = []

    if not os.path.isdir(modules_root):
        return violations

    modules = [
        d for d in os.listdir(modules_root) 
        if os.path.isdir(os.path.join(modules_root, d)) and not d.startswith("__")
    ]

    for current_mod in modules:
        mod_path = os.path.join(modules_root, current_mod)
        for root, _, files in os.walk(mod_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        source = f.read()
                    tree = ast.parse(source, filename=file_path)
                except Exception:
                    continue

                for node in ast.walk(tree):
                    # Checar 'import src.modules.outro' ou 'import modules.outro'
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            name = alias.name
                            for other_mod in modules:
                                if other_mod != current_mod and (f"modules.{other_mod}" in name or f"src.modules.{other_mod}" in name):
                                    rel = os.path.relpath(file_path, modules_root)
                                    violations.append((rel, node.lineno, f"Import direto proibido: '{name}'"))
                    # Checar 'from src.modules.outro import X'
                    elif isinstance(node, ast.ImportFrom):
                        mod_name = node.module or ""
                        for other_mod in modules:
                            if other_mod != current_mod and (f"modules.{other_mod}" in mod_name or f"src.modules.{other_mod}" in mod_name):
                                rel = os.path.relpath(file_path, modules_root)
                                violations.append((rel, node.lineno, f"ImportFrom direto proibido: '{mod_name}'"))

    return violations


def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    modules_dir = os.path.join(root, "src", "modules")
    if not os.path.isdir(modules_dir):
        print(f"Diretorio {modules_dir} nao encontrado. Pulando verificacao AST.")
        return 0

    violations = check_module_isolation(modules_dir)
    if violations:
        print(f"ERRO: Encontradas {len(violations)} violacoes de Bounded Context em aidd-master:")
        for v in violations:
            print(f"  {v[0]}:{v[1]} - {v[2]}")
        return 1

    print("OK: Bounded Context 100% isolado (Zero imports cruzados diretos).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
