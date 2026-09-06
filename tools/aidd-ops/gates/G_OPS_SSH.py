# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops — QUALITY GATE DETERMINÍSTICO SSH (G_OPS_SSH)
=============================================================================
Validação estrita via AST de tools/aidd-ops/src/core/ssh_runner.py:
1. Zero injeção de comandos shell (nenhuma chamada a subprocess/os.system/os.popen
   ou exec_command com concatenação/f-string dinâmica baseada em argumentos externos).
2. Verificação de lista estrita e fechada de operações (OPERACOES_PERMITIDAS).
3. Zero stubs / zero funções vazias.
"""

import ast
import os
import sys

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSH_RUNNER_PATH = os.path.join(TOOL_ROOT, "src", "core", "ssh_runner.py")


class OpsSshGate:
    def __init__(self):
        self.errors = []
        self.checks_passed = 0

    def check(self, condition: bool, description: str, error_msg: str):
        if condition:
            print(f"  [PASS] {description}")
            self.checks_passed += 1
        else:
            print(f"  [FAIL] {description} -> {error_msg}")
            self.errors.append(f"{description}: {error_msg}")

    def auditar(self, caminho_arquivo: str = SSH_RUNNER_PATH) -> int:
        print("=" * 70)
        print(" [GATE G_OPS_SSH] Auditoria Estrita do SSH Runner (Anti-Injeção AST)")
        print(f" Arquivo: {caminho_arquivo}")
        print("=" * 70)

        if not os.path.isfile(caminho_arquivo):
            self.check(False, "Existencia do arquivo ssh_runner.py", f"Nao encontrado: {caminho_arquivo}")
            return 1

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            fonte = f.read()

        try:
            tree = ast.parse(fonte, filename=caminho_arquivo)
        except SyntaxError as e:
            self.check(False, "Analise sintatica (AST Parse)", str(e))
            return 1

        self.check(True, "Analise sintatica (AST Parse)", "")

        # 1. Verificar presenca da constante fechada OPERACOES_PERMITIDAS
        tem_operacoes = False
        operacoes_chaves = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "OPERACOES_PERMITIDAS":
                        if isinstance(node.value, ast.Dict):
                            tem_operacoes = True
                            for k in node.value.keys:
                                if isinstance(k, ast.Constant):
                                    operacoes_chaves.append(k.value)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == "OPERACOES_PERMITIDAS":
                    if isinstance(node.value, ast.Dict):
                        tem_operacoes = True
                        for k in node.value.keys:
                            if isinstance(k, ast.Constant):
                                operacoes_chaves.append(k.value)

        self.check(
            tem_operacoes and len(operacoes_chaves) >= 5,
            "Lista fechada de operacoes (constante OPERACOES_PERMITIDAS no modulo)",
            "OPERACOES_PERMITIDAS ausente ou incompleta",
        )

        # 2. Varredura anti-injecao AST:
        chamadas_inseguras = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ("system", "popen", "exec_command", "run", "Popen", "check_output"):
                    for arg in node.args:
                        if isinstance(arg, ast.JoinedStr):
                            chamadas_inseguras.append(f"f-string em chamada a {func_name} (linha {node.lineno})")
                        elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                            chamadas_inseguras.append(f"concatenacao de string (+) em chamada a {func_name} (linha {node.lineno})")

        self.check(
            len(chamadas_inseguras) == 0,
            "Anti-Injecao AST: zero concatenacao de comandos shell",
            f"Chamadas inseguras detectadas: {chamadas_inseguras}",
        )

        # 3. Varredura anti-stubs
        stubs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    stubs.append(node.name)
                elif (
                    len(node.body) == 1
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and node.body[0].value.value is Ellipsis
                ):
                    stubs.append(node.name)

        self.check(
            len(stubs) == 0,
            "Zero Stubs (AST) em ssh_runner.py",
            f"Funcoes vazias detectadas: {stubs}",
        )

        # Resultado final
        print("-" * 70)
        if self.errors:
            print(f" [FALHA] Quality Gate G_OPS_SSH REPROVADO com {len(self.errors)} erro(s).")
            return 1

        print(f" [SUCESSO] Quality Gate G_OPS_SSH APROVADO ({self.checks_passed} checks OK)!")
        print("=" * 70)
        return 0


def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else SSH_RUNNER_PATH
    gate = OpsSshGate()
    sys.exit(gate.auditar(caminho))


if __name__ == "__main__":
    main()
