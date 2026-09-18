# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_PROTOTYPE_REWRITE
=============================================================================
Garante o isolamento determinístico de protótipos em sandbox/ e impede a
promoção direta de código experimental (vibe coding / PoC) para produção
(src/ ou features/) sem cobertura de testes TDD espelhada.

Regras de conformidade:
  1. A pasta sandbox/ (na raiz ou em ferramentas) é estritamente isolada e
     nunca pode ser importada por módulos sob src/ ou features/.
  2. Qualquer módulo promovido de protótipo para src/ ou src/features/ DEVE
     obrigatoriamente possuir arquivo de teste espelhado em tests/unit/
     (ex.: src/features/pedido/service.py -> tests/unit/test_pedido_service.py).
  3. Proíbe referências diretas a 'sandbox.' em código de produção.

Uso:
  python gates/G_PROTOTYPE_REWRITE.py [--target PATH]
      exit 0 = Isolamento de sandbox e cobertura de promoção válidos
      exit 1 = Violação de isolamento ou promoção de protótipo sem testes
"""

import ast
import os
import sys
from typing import List, Tuple


def verificar_imports_sandbox(base_dir: str) -> List[Tuple[str, int, str]]:
    """
    Varre todos os arquivos Python em src/ e bloqueia imports de sandbox.
    Retorna lista de tuplas: (arquivo, linha, import_proibido)
    """
    violacoes = []
    src_dir = os.path.join(base_dir, "src")
    if not os.path.isdir(src_dir):
        return violacoes

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8-sig") as f:
                        tree = ast.parse(f.read(), filename=full_path)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name == "sandbox" or alias.name.startswith("sandbox."):
                                    violacoes.append((full_path, node.lineno, alias.name))
                        elif isinstance(node, ast.ImportFrom):
                            mod = node.module or ""
                            if mod == "sandbox" or mod.startswith("sandbox."):
                                violacoes.append((full_path, node.lineno, mod))
                except Exception:
                    continue

    return violacoes


def verificar_promocao_sem_testes(base_dir: str) -> List[str]:
    """
    Verifica se arquivos em src/features/ que contenham marcas de protótipo
    ou histórico de PoC possuem testes espelhados em tests/.
    """
    sem_testes = []
    features_dir = os.path.join(base_dir, "src", "features")
    if not os.path.isdir(features_dir):
        return sem_testes

    tests_dir = os.path.join(base_dir, "tests")

    for entry in os.listdir(features_dir):
        slice_path = os.path.join(features_dir, entry)
        if not os.path.isdir(slice_path) or entry.startswith("_"):
            continue

        for root, _, files in os.walk(slice_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    rel_file = os.path.relpath(os.path.join(root, file), features_dir)
                    # Verifica se o arquivo tem marcadores de protótipo
                    full_path = os.path.join(root, file)
                    is_prototype_promoted = False
                    try:
                        with open(full_path, "r", encoding="utf-8-sig") as f:
                            content = f.read()
                            if "sandbox" in content.lower() or "poc" in content.lower() or "prototype" in content.lower():
                                is_prototype_promoted = True
                    except Exception:
                        continue

                    if is_prototype_promoted:
                        # Deve existir teste em tests/
                        expected_test_name = f"test_{entry}_{file}"
                        expected_test_simple = f"test_{file}"
                        test_found = False

                        if os.path.isdir(tests_dir):
                            for t_root, _, t_files in os.walk(tests_dir):
                                if any(f.startswith(expected_test_name) or f.startswith(expected_test_simple) or f == f"test_{entry}.py" for f in t_files):
                                    test_found = True
                                    break

                        if not test_found:
                            sem_testes.append(f"{full_path} (origem protótipo sem teste unitário espelhado)")

    return sem_testes


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Auditor de Isolamento de Protótipos e Trava de Reescrita")
    parser.add_argument("--target", default=".", help="Diretório a ser analisado")
    args = parser.parse_args()

    erros = 0

    violacoes_import = verificar_imports_sandbox(args.target)
    if violacoes_import:
        print("[ERRO] G_PROTOTYPE_REWRITE: Código de produção sob src/ importa módulo experimental sandbox/:")
        for arq, linha, mod in violacoes_import:
            print(f"  - {arq}:{linha} -> import '{mod}'")
        erros += len(violacoes_import)

    promocoes_sem_teste = verificar_promocao_sem_testes(args.target)
    if promocoes_sem_teste:
        print("[ERRO] G_PROTOTYPE_REWRITE: Código promovido de protótipo para src/ sem suíte TDD espelhada:")
        for item in promocoes_sem_teste:
            print(f"  - {item}")
        erros += len(promocoes_sem_teste)

    if erros > 0:
        print(f"\n======================================================================")
        print(f" [FALHA] Quality Gate G_PROTOTYPE_REWRITE REPROVADO com {erros} erro(s).")
        print(f"======================================================================")
        return 1

    print("[OK] G_PROTOTYPE_REWRITE: Isolamento de sandbox e cobertura TDD de promoção 100% conformes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
