# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — DYNAMIC CONTEXT SLICER (AST & Knowledge Graph)
=============================================================================
Fatia deterministicamente o subgrafo de simbolos e dependencias necessarios
para uma tarefa, montando um payload JSON estruturado (<150 tokens) e
eliminando a necessidade de buscas Grep exploratorias e leitura de arquivos inteiros.
"""

import ast
import os
from typing import Any, Dict, List, Set


class DynamicContextSlicer:
    """Extrai contratos, assinaturas e dependencias de forma token-eficiente."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def slice_file_symbols(self, relative_path: str) -> Dict[str, Any]:
        """Extrai apenas classes e funcoes de um arquivo sem o corpo de implementacao."""
        full_path = os.path.join(self.root_dir, relative_path)
        if not os.path.isfile(full_path) or not full_path.endswith(".py"):
            return {"file": relative_path, "symbols": []}

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
            tree = ast.parse(source, filename=relative_path)
        except Exception as e:
            return {"file": relative_path, "error": str(e)}

        symbols = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                args = [a.arg for a in node.args.args]
                symbols.append({
                    "type": "function",
                    "name": node.name,
                    "args": args,
                    "lineno": node.lineno
                })
            elif isinstance(node, ast.ClassDef):
                methods = [
                    n.name for n in node.body 
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                symbols.append({
                    "type": "class",
                    "name": node.name,
                    "methods": methods,
                    "lineno": node.lineno
                })

        return {"file": relative_path, "symbols": symbols}

    def get_minimal_context(self, file_paths: List[str]) -> Dict[str, Any]:
        """Monta um payload ultra-compacto com assinaturas de multiplos arquivos."""
        slices = [self.slice_file_symbols(p) for p in file_paths]
        return {
            "version": "1.0",
            "files_sliced": len(slices),
            "contracts": slices
        }
