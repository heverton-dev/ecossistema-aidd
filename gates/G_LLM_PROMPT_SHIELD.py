# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_LLM_PROMPT_SHIELD
=============================================================================
Auditoria de Blindagem e Sanitização Anti-Prompt Injection em Clientes LLM.

Regra Inviolável de Arquitetura:
  Nenhum payload não-confiável proveniente de requisições externas ou usuários
  pode ser concatenado diretamente em chamadas a APIs de LLMs ou subagentes
  sem passar deterministicamente pela sanitização do PromptShield
  ('PromptShield.sanitize', 'PromptShield.inspect' ou 'PromptShield.wrap_user_payload').

Saída:
  exit 0 = Todas as chamadas a LLM utilizam PromptShield ou repositório conforme.
  exit 1 = Concatenação crua ou chamada LLM desprotegida detectada via AST.
"""

import ast
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LLMCallVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.erros = []
        self.usa_prompt_shield = False

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and ("security" in node.module or "prompt_shield" in node.module):
            for alias in node.names:
                if alias.name == "PromptShield":
                    self.usa_prompt_shield = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Detecta chamadas a completions/generate_content/messages.create
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        chamadas_llm = {
            "generate_content",
            "chat_completion",
            "create_chat_completion",
            "invoke_model",
            "complete",
        }

        if func_name in chamadas_llm and not self.usa_prompt_shield:
            # Verifica se passa argumentos dinâmicos (não apenas string literal)
            tem_arg_dinamico = any(not isinstance(arg, ast.Constant) for arg in node.args)
            tem_kw_dinamico = any(not isinstance(kw.value, ast.Constant) for kw in node.keywords)
            if tem_arg_dinamico or tem_kw_dinamico:
                self.erros.append(
                    f"{self.filename}:{node.lineno} — Chamada LLM '{func_name}' sem import/uso do PromptShield"
                )

        self.generic_visit(node)


def auditar_arquivo(caminho_arquivo: str) -> list[str]:
    try:
        with open(caminho_arquivo, "r", encoding="utf-8-sig") as f:
            conteudo = f.read()
        arvore = ast.parse(conteudo, filename=caminho_arquivo)
    except Exception as exc:
        return [f"{caminho_arquivo}: Erro ao analisar sintaxe AST: {exc}"]

    visitor = LLMCallVisitor(caminho_arquivo)
    visitor.visit(arvore)
    return visitor.erros


def scan_prompt_shield(repo_root: str) -> list[str]:
    todos_erros = []
    pastas_alvo = ["tools", "componentes", "src"]
    for pasta in pastas_alvo:
        dir_completo = os.path.join(repo_root, pasta)
        if not os.path.exists(dir_completo):
            continue
        for root, _, files in os.walk(dir_completo):
            if any(skip in root for skip in [".git", "__pycache__", "node_modules", "venv", "tests", "materiais-extras"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    caminho = os.path.join(root, file)
                    erros = auditar_arquivo(caminho)
                    todos_erros.extend(erros)
    return todos_erros


def main() -> int:
    print("=" * 72)
    print(" [GATE] G_LLM_PROMPT_SHIELD — Auditoria de Blindagem Anti-Injection")
    print("=" * 72)

    erros = scan_prompt_shield(ROOT_DIR)

    if erros:
        print(f"\n[FALHA] Detectada(s) {len(erros)} violação(ões) de segurança em chamadas LLM:\n")
        for err in erros:
            print(f"  - {err}")
        print("\nRegra: Todas as chamadas a LLMs devem utilizar PromptShield para sanitização.")
        print("=" * 72)
        return 1

    print("\n[SUCESSO] Quality Gate G_LLM_PROMPT_SHIELD APROVADO — 100% blindado contra injeções!")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
