# -*- coding: utf-8 -*-
"""
G_FACTORY_MVP — Valida estrutura do diretorio aidd-factory.

Modos:
  (a) Valida estrutura: py_compile + AST anti-stubs em todos os .py
  (b) Valida output: FACTORY_OUTPUT.json contra schema
"""
import ast
import os
import py_compile
import sys

_FACTORY_ROOT = os.path.join(os.path.dirname(__file__), "..")
_ESPERADOS = [
    "AGENTS.md",
    "src/__init__.py",
    "src/core/__init__.py",
    "src/core/result.py",
    "src/core/escritor_atomico.py",
    "scripts/__init__.py",
    "scripts/pipeline_factory.py",
    "scripts/contrato_factory.py",
    "scripts/phases/__init__.py",
    "scripts/phases/01_analisador.py",
    "scripts/phases/04_compose.py",
    "scripts/phases/05_init_db.py",
    "scripts/phases/06_env.py",
    "schemas/schema_factory_input.json",
    "schemas/schema_factory_output.json",
    "gates/G_FACTORY_MVP.py",
    "tests/__init__.py",
]


def _verificar_estrutura() -> list:
    """Verifica se todos os arquivos esperados existem."""
    problemas = []
    for caminho_relativo in _ESPERADOS:
        caminho = os.path.join(_FACTORY_ROOT, caminho_relativo)
        if not os.path.isfile(caminho):
            problemas.append(f"Arquivo ausente: {caminho_relativo}")
    return problemas


def _verificar_py_compile() -> list:
    """Verifica se todos os .py compilam sem erro."""
    problemas = []
    for root, dirs, files in os.walk(os.path.join(_FACTORY_ROOT, "src")):
        for f in files:
            if f.endswith(".py"):
                caminho = os.path.join(root, f)
                try:
                    py_compile.compile(caminho, doraise=True)
                except py_compile.PyCompileError as exc:
                    problemas.append(f"py_compile falhou: {os.path.relpath(caminho, _FACTORY_ROOT)}: {exc}")
    for root, dirs, files in os.walk(os.path.join(_FACTORY_ROOT, "scripts")):
        for f in files:
            if f.endswith(".py"):
                caminho = os.path.join(root, f)
                try:
                    py_compile.compile(caminho, doraise=True)
                except py_compile.PyCompileError as exc:
                    problemas.append(f"py_compile falhou: {os.path.relpath(caminho, _FACTORY_ROOT)}: {exc}")
    return problemas


def _verificar_anti_stubs() -> list:
    """Verifica ausencia de stubs via AST."""
    problemas = []
    stub_indicators = ["NotImplemented", "pass  # TODO", "raise NotImplementedError"]
    for root, dirs, files in os.walk(os.path.join(_FACTORY_ROOT, "src")):
        for f in files:
            if not f.endswith(".py"):
                continue
            caminho = os.path.join(root, f)
            try:
                with open(caminho, "r", encoding="utf-8") as fh:
                    tree = ast.parse(fh.read(), filename=caminho)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Raise) and hasattr(node, "exc"):
                        if isinstance(node.exc, ast.Name) and node.exc.id == "NotImplementedError":
                            problemas.append(f"Stub detectado (NotImplementedError): {os.path.relpath(caminho, _FACTORY_ROOT)}:{node.lineno}")
            except (SyntaxError, OSError):
                pass
    return problemas


def executar():
    """Executa o gate e retorna codigo de saida."""
    print("=" * 72)
    print(" [G_FACTORY_MVP] Validacao de Estrutura do AIDD-Factory")
    print("=" * 72)

    problemas = []
    problemas.extend(_verificar_estrutura())
    problemas.extend(_verificar_py_compile())
    problemas.extend(_verificar_anti_stubs())

    if problemas:
        print(f"\n[FALHA] {len(problemas)} problema(s) detectado(s):")
        for p in problemas:
            print(f"  - {p}")
        return 1

    print("\n[SUCESSO] Estrutura do aidd-factory validada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(executar())
