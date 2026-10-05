# -*- coding: utf-8 -*-
"""
Motor Analítico Determinístico de Acoplamento (VSA).
Dimensão D8: O que o Estágio Processa.
"""

import ast
from typing import Any, Dict, List


def extrair_imports_ast(codigo: str) -> List[str]:
    arvore = ast.parse(codigo)
    imports: List[str] = []
    for node in ast.walk(arvore):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return sorted(imports)


def analisar_codigo_fonte(codigo: str, modulo_origem: str) -> Dict[str, Any]:
    if not modulo_origem or not isinstance(modulo_origem, str):
        raise ValueError("Envelope estrito: módulo de origem obrigatório e deve ser string.")

    todos_imports = extrair_imports_ast(codigo)
    externos = [imp for imp in todos_imports if imp.startswith("tools.") or imp.startswith("components.")]

    envelope = {
        "status": "sucesso",
        "modulo_origem": modulo_origem,
        "total_imports": len(todos_imports),
        "todos_imports": todos_imports,
        "imports_externos": externos,
        "acoplamento_detectado": len(externos) > 0,
    }

    return envelope
