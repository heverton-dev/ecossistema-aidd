# -*- coding: utf-8 -*-
"""
Restaura tools/aidd-master/templates/v2/ (R1 do
PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md).

Diagnostico confirmado: o diretorio esta vazio ha muito tempo (nao existe nem
em proj_aidd/aidd-master/templates/v2), enquanto aidd-master-enterprise
(fork historico da mesma linhagem) recebeu e manteve os 25 arquivos
(database.py, cqrs.py, local_first.py, circuit_breaker.py, saga.py, etc.)
que tests/unit/test_database_adapter.py e tests/unit/test_cqrs_local_first.py
esperam importar via sys.path. Copia idempotente: aborta se o destino ja
tiver conteudo, para nao mascarar um estado inesperado.
"""

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "tools", "aidd-master-enterprise", "templates", "v2")
DST = os.path.join(ROOT, "tools", "aidd-master", "templates", "v2")


def main():
    if not os.path.isdir(SRC):
        print(f"ERRO: origem nao encontrada: {SRC}")
        sys.exit(1)

    os.makedirs(DST, exist_ok=True)
    existentes = os.listdir(DST)
    if existentes:
        print(f"ABORTADO: destino ja contem {len(existentes)} arquivo(s): {DST}")
        sys.exit(1)

    copiados = 0
    for nome in os.listdir(SRC):
        if nome == "__pycache__":
            continue
        origem = os.path.join(SRC, nome)
        destino = os.path.join(DST, nome)
        if os.path.isfile(origem):
            shutil.copy2(origem, destino)
            copiados += 1
        elif os.path.isdir(origem):
            shutil.copytree(origem, destino, ignore=shutil.ignore_patterns("__pycache__"))
            copiados += sum(len(f) for _, _, f in os.walk(destino))

    print(f"OK {copiados} arquivo(s) restaurado(s) em {DST}")


if __name__ == "__main__":
    main()
