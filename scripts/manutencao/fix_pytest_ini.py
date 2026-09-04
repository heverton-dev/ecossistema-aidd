# -*- coding: utf-8 -*-
"""
Corrige gates/../pytest.ini da raiz do ecossistema-aidd (R2 do
PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md):
1. Remove o BOM UTF-8 que quebrava o parser do pytest
   ("unexpected line: '﻿[pytest]'").
2. Corrige 'testpaths' para referenciar apenas diretórios que existem
   de fato na raiz, em vez do 'tests' inexistente.
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTEST_INI = os.path.join(ROOT, "pytest.ini")


def main():
    with io.open(PYTEST_INI, "r", encoding="utf-8-sig") as f:
        content = f.read()

    candidatos = ["tests", "gates"]
    existentes = [c for c in candidatos if os.path.isdir(os.path.join(ROOT, c))]
    if not existentes:
        print("ERRO: nenhum diretorio candidato de testpaths existe na raiz.")
        sys.exit(1)

    linhas_corrigidas = []
    for linha in content.splitlines():
        if linha.strip().startswith("testpaths"):
            linhas_corrigidas.append("testpaths = " + " ".join(existentes))
        else:
            linhas_corrigidas.append(linha)

    with io.open(PYTEST_INI, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(linhas_corrigidas) + "\n")

    print(f"OK pytest.ini corrigido (BOM removido, testpaths = {' '.join(existentes)})")


if __name__ == "__main__":
    main()
