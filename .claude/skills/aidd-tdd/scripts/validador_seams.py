# -*- coding: utf-8 -*-
"""
Validador estático AST de Costuras Públicas e Anti-Stubs para aidd-tdd (D4 / D1 / DoD 3).
Inspeciona arquivos de teste para garantir conformidade com a Lei #5:
- Zero Stubs vazios (pass, NotImplementedError).
- Zero asserções triviais (assert True, assert 1 == 1).
- Proibição de acoplamento a membros privados (começados por _).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Tuple, List


class SeamVisitor(ast.NodeVisitor):
    def __init__(self):
        self.problemas: List[str] = []
        self.tem_assert_real = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Checar corpo da funcao de teste
        if node.name.startswith("test_") or node.name.endswith("_test"):
            # 1. Checa stubs vazios (apenas pass ou docstring + pass)
            pass_statements = [n for n in node.body if isinstance(n, ast.Pass)]
            if pass_statements and len(node.body) <= 2:
                self.problemas.append(
                    f"Linha {node.lineno}: Função de teste '{node.name}' contém stub vazio (pass)."
                )

            # 2. Checa NotImplementedError
            for stmt in node.body:
                if isinstance(stmt, ast.Raise):
                    if isinstance(stmt.exc, ast.Call) and getattr(stmt.exc.func, "id", None) == "NotImplementedError":
                        self.problemas.append(
                            f"Linha {node.lineno}: Função de teste '{node.name}' lança NotImplementedError."
                        )

        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert):
        # Checar assert True ou constantes booleanas
        if isinstance(node.test, ast.Constant):
            if node.test.value is True:
                self.problemas.append(
                    f"Linha {node.lineno}: Asserção trivial detectada (assert True)."
                )
                return

        # Checa assert 1 == 1 ou literais idênticos
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Constant) and len(node.test.comparators) == 1:
                if isinstance(node.test.comparators[0], ast.Constant):
                    if node.test.left.value == node.test.comparators[0].value:
                        self.problemas.append(
                            f"Linha {node.lineno}: Asserção trivial detectada (comparação estática de constantes idênticas)."
                        )
                        return

        self.tem_assert_real = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Checa chamada direta a membros privados
        if isinstance(node.func, ast.Attribute):
            if node.func.attr.startswith("_") and not node.func.attr.startswith("__"):
                self.problemas.append(
                    f"Linha {node.lineno}: Acoplamento indevido a membro privado '{node.func.attr}'."
                )
        self.generic_visit(node)


def validar_arquivo_teste(caminho: str | Path) -> Tuple[bool, List[str]]:
    p = Path(caminho)
    if not p.exists():
        return False, [f"Arquivo '{caminho}' não existe."]

    try:
        conteudo = p.read_text(encoding="utf-8")
        arvore = ast.parse(conteudo, filename=str(p))
    except Exception as e:
        return False, [f"Erro ao parsear arquivo AST: {e}"]

    visitor = SeamVisitor()
    visitor.visit(arvore)

    if not visitor.tem_assert_real and not visitor.problemas:
        # Se for um arquivo de teste sem nenhuma asserção real
        if "test" in p.name.lower():
            visitor.problemas.append("Arquivo de teste não contém nenhuma asserção funcional observável.")

    return len(visitor.problemas) == 0, visitor.problemas
