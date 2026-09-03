#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GATE DETERMINÍSTICO DE QUALIDADE & IMPECCABLE UI (G_QUALIDADE)
=============================================================================
Valida compilação estática (py_compile), varredura AST anti-stubs vazios,
e Linter de Acessibilidade & Impeccable UI (WCAG 2.1, zero alerts, modais customizados).
"""

import os
import sys
import subprocess
import ast
import re
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def verificar(target_dir: str = "."):
    print("[GATE G_QUALIDADE v5.1] Validando sintaxe estática, AST anti-stubs e Linter Impeccable UI...")
    target_dir = os.path.abspath(target_dir)
    erros = []

    # 1. Compilação de Sintaxe (py_compile)
    for root, dirs, files in os.walk(target_dir):
        if any(ignore in root for ignore in ['.git', 'node_modules', '.venv', '__pycache__', '.pytest_cache']):
            continue
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                res = subprocess.run([sys.executable, '-m', 'py_compile', path], capture_output=True, text=True)
                if res.returncode != 0:
                    erros.append(f"Erro de compilação sintática em: {os.path.relpath(path, target_dir)}")

    # 2. Varredura AST Anti-Stubs em Services e Routes
    src_dir = os.path.join(target_dir, "src")
    if os.path.isdir(src_dir):
        for root, _, files in os.walk(src_dir):
            for f in files:
                if f.endswith('.py') and f in ['services.py', 'routes.py', 'models.py']:
                    f_path = os.path.join(root, f)
                    try:
                        with open(f_path, 'r', encoding='utf-8', errors='ignore') as pf:
                            content = pf.read()
                            tree = ast.parse(content, filename=f_path)
                            for node in ast.walk(tree):
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                                        erros.append(f"Stub vazio 'pass' detectado em {os.path.relpath(f_path, target_dir)} -> {node.name}()")
                                    elif len(node.body) == 1 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and node.body[0].value.value is Ellipsis:
                                        erros.append(f"Stub vazio '...' detectado em {os.path.relpath(f_path, target_dir)} -> {node.name}()")
                    except Exception as e:
                        erros.append(f"Falha ao inspecionar AST em {f_path}: {e}")

    # 3. Linter de Impeccable UI & Acessibilidade WCAG 2.1
    comp_dir = os.path.join(src_dir, "static", "components")
    if os.path.isdir(comp_dir):
        for f in os.listdir(comp_dir):
            if f.endswith('.html'):
                f_path = os.path.join(comp_dir, f)
                with open(f_path, 'r', encoding='utf-8', errors='ignore') as hf:
                    html = hf.read()
                    if 'alert(' in html or 'confirm(' in html or 'prompt(' in html:
                        erros.append(f"Diálogo nativo de SO detectado em {f} (Use Toasts e Modais Impeccable).")
                    if '<button' in html and 'type=' not in html:
                        erros.append(f"Tag <button> sem atributo 'type' em {f} (WCAG 2.1).")

    if erros:
        print("\n[FAIL] ❌ BLOQUEIO DE QUALIDADE: Falhas de qualidade detectadas:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)

    print("[OK] SUCESSO: Sintaxe, AST anti-stubs e Linter Impeccable UI validados com 100% de êxito (exit 0)!")
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Diretório alvo do projeto")
    args, _ = parser.parse_known_args()
    verificar(args.dir)
