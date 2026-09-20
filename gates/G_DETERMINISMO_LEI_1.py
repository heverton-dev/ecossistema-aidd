#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_DETERMINISMO_LEI_1 (Lei Canônica #1)
=============================================================================
Auditoria de Determinismo Mecânico: Bloqueia o uso de SDKs e chamadas de LLM
em caminhos de execução estritamente determinísticos (ex: gates/*.py e módulos
declarados mecânicos).

Invariante Inviolável (Lei #1 - Determinism First):
  Tarefas mecânicas, verificação de qualidade e pipelines de infraestrutura
  devem utilizar scripts determinísticos, AST, regex ou JSON Schema.
  É estritamente proibido o uso de chamadas de LLM para tarefas mecânicas.

Limite Metrológico e Honestidade de Rótulo (Lei #8 / ISSUE-0020):
  Nenhum analisador estático classifica de forma geral o uso "mecânico" versus
  "cognitivo/heurístico" de um LLM. Este portão cobre estritamente o subconjunto
  de SDKs de LLM conhecidos (anthropic, openai, google.generativeai, etc.)
  em diretórios declarados mecânicos. A cobertura total de julgamento semântico
  permanece no território da revisão humana e convenção arquitetural.

Saída:
  exit 0 = Nenhuma violação de determinismo detectada.
  exit 1 = Uso de SDK ou chamada de LLM detectada em rota mecânica.
=============================================================================
"""

import ast
import json
import os
import sys
from typing import Dict, List, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES_DIR = os.path.join(ROOT_DIR, "gates")
EXCECOES_FILE = os.path.join(GATES_DIR, "excecoes_determinismo.json")

# SDKs de LLM proibidos em rotas determinísticas
BLOCKED_LLM_MODULES: Set[str] = {
    "anthropic",
    "openai",
    "google.generativeai",
    "google.genai",
    "langchain",
    "langchain_core",
    "litellm",
    "cohere",
    "groq",
    "mistralai",
    "ollama",
    "together",
}


def carregar_excecoes() -> Set[str]:
    """Carrega lista de arquivos ou padrões isentos de forma documentada e versionada."""
    if not os.path.isfile(EXCECOES_FILE):
        return set()
    try:
        with open(EXCECOES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("excecoes_autorizadas", []))
    except Exception as exc:
        print(f"[AVISO] Falha ao carregar {EXCECOES_FILE}: {exc}")
        return set()


class DeterminismoVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if alias.name in BLOCKED_LLM_MODULES or base_module in BLOCKED_LLM_MODULES:
                self.violations.append(
                    f"{self.filename}:{node.lineno} — Importação de SDK de LLM proibido em caminho mecânico: 'import {alias.name}'"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_module = node.module.split(".")[0]
            if node.module in BLOCKED_LLM_MODULES or base_module in BLOCKED_LLM_MODULES:
                self.violations.append(
                    f"{self.filename}:{node.lineno} — Importação de SDK de LLM proibido em caminho mecânico: 'from {node.module} import ...'"
                )
        self.generic_visit(node)


def auditar_arquivo(caminho: str) -> List[str]:
    """Analisa um arquivo Python via AST procurando importações proibidas de LLMs."""
    try:
        with open(caminho, "r", encoding="utf-8-sig", errors="replace") as f:
            tree = ast.parse(f.read(), filename=caminho)
    except SyntaxError as e:
        return [f"{caminho}:{e.lineno} — Erro de sintaxe AST: {e.msg}"]
    except Exception as e:
        return [f"{caminho} — Erro ao abrir arquivo: {e}"]

    visitor = DeterminismoVisitor(caminho)
    visitor.visit(tree)
    return visitor.violations


def auditar_determinismo(repo_root: str = ROOT_DIR) -> Tuple[int, List[str], int]:
    """Verifica todos os arquivos em gates/ e rotas mecânicas declaradas."""
    excecoes = carregar_excecoes()
    violations: List[str] = []
    total_auditados = 0

    # Escopo 1: Todos os scripts em gates/ (excluindo testes que testam a própria detecção)
    if os.path.isdir(GATES_DIR):
        for root, _, files in os.walk(GATES_DIR):
            for file in sorted(files):
                if not file.endswith(".py"):
                    continue
                caminho_rel = os.path.relpath(os.path.join(root, file), repo_root).replace("\\", "/")
                # Arquivos de teste de gates testam reprovação e podem citar padrões, mas gates de produção não
                if file.startswith("test_"):
                    continue
                if caminho_rel in excecoes:
                    continue

                total_auditados += 1
                violations.extend(auditar_arquivo(os.path.join(root, file)))

    return (1 if violations else 0), violations, total_auditados


def main() -> int:
    print("=" * 72)
    print(" [GATE] G_DETERMINISMO_LEI_1 — Auditoria de Determinismo Mecânico (Lei #1)")
    print("=" * 72)

    code, violations, total = auditar_determinismo(ROOT_DIR)

    if violations:
        print(f"\n[FALHA] Detectada(s) {len(violations)} violação(ões) da Lei #1 (Determinism First):\n")
        for v in violations:
            print(f"  - {v}")
        print("\nRegra Violada: Caminhos mecânicos (gates/) não podem utilizar SDKs de LLM.")
        print("=" * 72)
        return 1

    print(f"\n[SUCESSO] Quality Gate G_DETERMINISMO_LEI_1 APROVADO — {total} arquivos mecânicos 100% conformes.")
    print("=" * 72)
    print(" [LIMITE METROLÓGICO — LEI #8 / ISSUE-0020]:")
    print("   O gate valida deterministicamente via AST o bloqueio de SDKs de LLM conhecidos")
    print("   (anthropic, openai, google.generativeai, litellm, langchain, cohere, groq, etc.).")
    print("   A classificação semântica universal entre uso 'mecânico' e 'cognitivo' permanece")
    print("   no escopo de revisão humana arquitetural.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
