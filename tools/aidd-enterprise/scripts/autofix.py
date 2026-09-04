#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — AUTO-FIX SCRIPT (autofix.py)
=============================================================================
Script auxiliar que tenta corrigir automaticamente problemas comuns:
  1. Formatação com black (se instalado)
  2. Ordenação de imports com isort (se instalado)
  3. Limpeza de *.pyc e __pycache__

Sempre exit 0 — é um helper, não um gate.
"""

import os
import sys
import shutil
import subprocess
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def run_black(root_dir: str) -> bool:
    """Executa black formatter em todos os .py se disponível."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print("  ⏭️  black não instalado — pulando formatação")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  ⏭️  black não disponível — pulando formatação")
        return False

    print("  🖤 Executando black formatter...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--quiet", "--target-version", "py311", root_dir],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print("  ✅ black: formatação concluída com sucesso")
            return True
        else:
            print(f"  ⚠️  black: saída com avisos (exit {result.returncode})")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[:5]:
                    print(f"      {line}")
            return False
    except subprocess.TimeoutExpired:
        print("  ⚠️  black: timeout após 120s")
        return False


def run_isort(root_dir: str) -> bool:
    """Executa isort para ordenar imports se disponível."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "--version-number"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print("  ⏭️  isort não instalado — pulando ordenação de imports")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  ⏭️  isort não disponível — pulando ordenação de imports")
        return False

    print("  📦 Executando isort...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "--profile", "black", "--quiet", root_dir],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print("  ✅ isort: ordenação de imports concluída")
            return True
        else:
            print(f"  ⚠️  isort: saída com avisos (exit {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print("  ⚠️  isort: timeout após 120s")
        return False


def clean_pycache(root_dir: str) -> tuple:
    """Remove *.pyc e diretórios __pycache__ recursivamente."""
    pyc_removed = 0
    dirs_removed = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Pular .git e venv
        if any(ignored in dirpath for ignored in [".git", ".venv", "node_modules"]):
            continue

        # Remover __pycache__ directories
        if "__pycache__" in dirnames:
            cache_dir = os.path.join(dirpath, "__pycache__")
            try:
                shutil.rmtree(cache_dir)
                dirs_removed += 1
            except OSError:
                pass

        # Remover .pyc files soltos
        for fname in filenames:
            if fname.endswith(".pyc"):
                fpath = os.path.join(dirpath, fname)
                try:
                    os.remove(fpath)
                    pyc_removed += 1
                except OSError:
                    pass

    return pyc_removed, dirs_removed


def main():
    parser = argparse.ArgumentParser(description="autofix.py — Auto-Fix Helper AIDD v5.1")
    parser.add_argument("--dir", default=".", help="Diretório raiz do projeto")
    args = parser.parse_args()

    root_dir = os.path.abspath(args.dir)

    print("=" * 80)
    print("🔧  AIDD v5.1 — AUTO-FIX: Tentando corrigir problemas automaticamente")
    print(f"📁 Diretório Alvo: {root_dir}")
    print("=" * 80)

    fixes_applied = []

    # 1. Limpar *.pyc e __pycache__
    print("\n🧹 [1/3] Limpando cache Python (*.pyc e __pycache__)...")
    pyc_removed, dirs_removed = clean_pycache(root_dir)
    if pyc_removed > 0 or dirs_removed > 0:
        fixes_applied.append(f"Removidos {pyc_removed} arquivos .pyc e {dirs_removed} diretórios __pycache__")
        print(f"  ✅ Limpeza concluída: {pyc_removed} .pyc, {dirs_removed} __pycache__")
    else:
        print("  ✅ Nenhum arquivo de cache para limpar")

    # 2. Executar black
    print("\n🖤 [2/3] Formatação com black...")
    if run_black(root_dir):
        fixes_applied.append("Formatação black aplicada")

    # 3. Executar isort
    print("\n📦 [3/3] Ordenação de imports com isort...")
    if run_isort(root_dir):
        fixes_applied.append("Ordenação isort aplicada")

    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DO AUTO-FIX:")
    if fixes_applied:
        for fix in fixes_applied:
            print(f"   ✅ {fix}")
    else:
        print("   ℹ️  Nenhuma correção necessária ou possível")
    print("=" * 80)

    # Sempre exit 0 — helper, não gate
    sys.exit(0)


if __name__ == "__main__":
    main()
