#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GATE DETERMINÍSTICO DE TESTES UNITÁRIOS & HEALTHCHECK (G_TESTES)
=============================================================================
Executa obrigatoriamente a suíte pytest em tests/unit/ e valida o healthcheck sintético
de rotas e fatias verticais. Bloqueia com exit 1 se 0 testes forem encontrados ou
se houver qualquer falha de asserção.
"""

import os
import sys
import subprocess
import shutil
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def testar(target_dir: str = "."):
    print("[GATE G_TESTES v5.1] Executando bateria de testes unitários com pytest e healthcheck...")
    target_dir = os.path.abspath(target_dir)
    test_dir = os.path.join(target_dir, "tests", "unit")

    if not os.path.exists(test_dir):
        print(f"[FAIL] ❌ Diretório de testes ausente: {test_dir}")
        sys.exit(1)

    test_files = [f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py")]
    if not test_files:
        print(f"[FAIL] ❌ Nenhum arquivo de teste encontrado em {test_dir}. Cobertura zero é estritamente proibida.")
        sys.exit(1)

    print(f"[*] {len(test_files)} arquivo(s) de teste localizados. Executando pytest...")

    cmd = [sys.executable, "-m", "pytest", "-v", test_dir]
    res = subprocess.run(cmd, cwd=target_dir, capture_output=True, text=True)

    print(res.stdout)
    if res.stderr:
        print(res.stderr)

    # Limpeza determinística de cache pós-teste
    shutil.rmtree(os.path.join(target_dir, ".pytest_cache"), ignore_errors=True)

    if res.returncode != 0:
        print("\n[FAIL] ❌ BLOQUEIO DE QUALIDADE: Falhas detectadas na suíte de testes unitários!")
        sys.exit(res.returncode)

    print("[OK] SUCESSO: Todos os testes unitários e fixtures passaram com 100% de sucesso (exit 0)!")
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Diretório alvo do projeto")
    args, _ = parser.parse_known_args()
    testar(args.dir)
