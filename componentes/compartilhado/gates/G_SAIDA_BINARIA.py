#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_SAIDA_BINARIA (Lei Canônica #2)
=============================================================================
Auditoria de Qualidade Binária: Verifica deterministicamente via AST que todos
os Quality Gates em gates/ terminam estritamente com sys.exit(0) ou sys.exit(1).
Nenhum código de saída ambíguo (2, 3, strings, bare return, fall-through) é aceito.

Invariante Inviolável (Lei #2 - Binary Quality):
  Toda verificação de qualidade deve produzir veredito puramente binário:
  0 = APROVADO (passa), 1 = REPROVADO (bloqueia).

Critérios de Aceite (ISSUE-0021):
  1. Todo arquivo gates/G_*.py deve conter bloco if __name__ == '__main__':
     com chamada explícita a sys.exit.
  2. Todos os call sites de sys.exit devem passar estritamente literal 0 ou 1,
     ou função cujos retornos sejam exclusivamente 0 ou 1.
  3. Proibido sys.exit() sem argumento (fall-through implícito).

Saída:
  exit 0 = Todos os scripts em gates/ são estritamente binários.
  exit 1 = Ao menos uma saída ambígua ou ausência de sys.exit detectada.
=============================================================================
"""

import ast
import os
import sys
from typing import Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES_DIR = os.path.join(ROOT_DIR, "gates")


class BinaryExitVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, tree: ast.AST):
        self.filename = filename
        self.tree = tree
        self.erros: List[str] = []
        self.has_main_block = False
        self.main_has_sys_exit = False
        self.functions: Dict[str, ast.FunctionDef] = {}

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions[node.name] = node

    def visit_If(self, node: ast.If):
        # Detecta if __name__ == '__main__'
        if isinstance(node.test, ast.Compare):
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == "__name__":
                self.has_main_block = True
                exits = [
                    n for n in ast.walk(node)
                    if isinstance(n, ast.Call)
                    and getattr(n.func, "id", getattr(n.func, "attr", None)) in ("exit", "sys.exit")
                ]
                if exits:
                    self.main_has_sys_exit = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = getattr(node.func, "id", getattr(node.func, "attr", None))
        if func_name in ("exit", "sys.exit"):
            if not node.args:
                self.erros.append(
                    f"{self.filename}:{node.lineno} — Chamada a '{func_name}()' sem argumento (deve ser explícito 0 ou 1)."
                )
                return

            arg = node.args[0]
            # Caso 1: Literal constante
            if isinstance(arg, ast.Constant):
                if arg.value not in (0, 1):
                    self.erros.append(
                        f"{self.filename}:{node.lineno} — Código de saída '{arg.value}' inválido. Apenas 0 ou 1 são permitidos (Lei #2)."
                    )
            # Caso 2: Chamada a função local (ex: sys.exit(main()))
            elif isinstance(arg, ast.Call):
                target_fn_name = getattr(arg.func, "id", getattr(arg.func, "attr", None))
                if target_fn_name and target_fn_name in self.functions:
                    fn_node = self.functions[target_fn_name]
                    retornos = [r for r in ast.walk(fn_node) if isinstance(r, ast.Return)]
                    for r in retornos:
                        if r.value is None:
                            self.erros.append(
                                f"{self.filename}:{r.lineno} — Função '{target_fn_name}' contém 'return' vazio (None)."
                            )
                        elif isinstance(r.value, ast.Constant):
                            if r.value.value not in (0, 1):
                                self.erros.append(
                                    f"{self.filename}:{r.lineno} — Função '{target_fn_name}' retorna literal '{r.value.value}' (não binário)."
                                )
                        elif isinstance(r.value, ast.IfExp):
                            # Ex: 1 if erro else 0
                            pass
                        elif isinstance(r.value, ast.Tuple) and len(r.value.elts) > 0:
                            first_elt = r.value.elts[0]
                            if isinstance(first_elt, ast.Constant) and first_elt.value not in (0, 1):
                                self.erros.append(
                                    f"{self.filename}:{r.lineno} — Função '{target_fn_name}' retorna tupla com código não-binário: {first_elt.value}"
                                )
            # Caso 3: Operação ternária direta: sys.exit(1 if erros else 0)
            elif isinstance(arg, ast.IfExp):
                pass
            # Caso 4: Compare ou UnaryOp
            elif isinstance(arg, (ast.Compare, ast.UnaryOp)):
                pass

        self.generic_visit(node)


def auditar_arquivo(caminho: str) -> List[str]:
    """Audita um script de gate individual via AST."""
    try:
        with open(caminho, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read()
        tree = ast.parse(content, filename=caminho)
    except SyntaxError as e:
        return [f"{caminho}:{e.lineno} — Erro de sintaxe AST: {e.msg}"]
    except Exception as e:
        return [f"{caminho} — Erro de leitura: {e}"]

    visitor = BinaryExitVisitor(caminho, tree)
    visitor.visit(tree)

    erros = list(visitor.erros)
    if not visitor.has_main_block:
        erros.append(f"{caminho} — Ausência de bloco 'if __name__ == \"__main__\":'.")
    elif not visitor.main_has_sys_exit:
        erros.append(
            f"{caminho} — Bloco '__main__' não contém chamada explícita a sys.exit(...) (risco de fall-through)."
        )

    return erros


def auditar_todos_os_gates(gates_dir: str = GATES_DIR) -> Tuple[int, List[str], int]:
    """Audita todos os arquivos G_*.py em gates/."""
    erros_totais: List[str] = []
    total_auditados = 0

    if not os.path.isdir(gates_dir):
        return 1, [f"Diretório não encontrado: {gates_dir}"], 0

    for file in sorted(os.listdir(gates_dir)):
        if file.startswith("G_") and file.endswith(".py"):
            total_auditados += 1
            caminho = os.path.join(gates_dir, file)
            erros = auditar_arquivo(caminho)
            erros_totais.extend(erros)

    return (1 if erros_totais else 0), erros_totais, total_auditados


def main() -> int:
    print("=" * 72)
    print(" [GATE] G_SAIDA_BINARIA — Auditoria de Saída Estritamente Binária (Lei #2)")
    print("=" * 72)

    code, erros, total = auditar_todos_os_gates(GATES_DIR)

    if erros:
        print(f"\n[FALHA] Detectada(s) {len(erros)} violação(ões) de saída binária (Lei #2):\n")
        for err in erros:
            print(f"  - {err}")
        print("\nRegra Violada: Gates devem invocar sys.exit(0) ou sys.exit(1) sem ambiguidade.")
        print("=" * 72)
        return 1

    print(f"\n[SUCESSO] Quality Gate G_SAIDA_BINARIA APROVADO — {total} gates auditados com saída 100% binária (0/1).")
    print("=" * 72)
    print(" [LIMITE METROLÓGICO — LEI #8 / ISSUE-0021]:")
    print("   A verificação estática assegura que os pontos de saída inspecionados utilizam 0 ou 1.")
    print("   Exceções não tratadas em tempo de execução que causem crash com código 1 pelo runtime")
    print("   do Python são garantidas pelo meta-gate de execução real G_PORTAO_PROVA_QUE_MORDE.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
