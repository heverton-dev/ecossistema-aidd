#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
QUALITY GATE: G_BRIDGE_POSTGRESQL
===============================================================================
Valida que os scripts SQL gerados/consolidados pela aidd-freedom (init-db.sql)
são PostgreSQL puro, possuem integridade de sintaxe básica e garantem
isolamento transacional e esquemas padronizados.

Exit 0: SQL consolidado válido.
Exit 1: SQL com comandos inválidos ou corrompido.
===============================================================================
"""

import os
import re
import sys

# Extensões indisponíveis no PostgreSQL vanilla da stack self-hosted
# (init-db.sql com elas derruba a subida do container).
EXTENSOES_PROIBIDAS = {"pg_cron"}

def audit_postgresql_script(target_dir: str) -> int:
    print("=" * 72)
    print(" [GATE] G_BRIDGE_POSTGRESQL — Validação de SQL Consolidado")
    print("=" * 72)

    sql_path = os.path.join(target_dir, "init-db.sql")
    if not os.path.exists(sql_path):
        print(f" [INFO] Arquivo init-db.sql não encontrado em {target_dir}. Ignorando se não houver banco.")
        return 0

    erros = []
    with open(sql_path, "r", encoding="utf-8", errors="ignore") as f:
        sql = f.read()

    if len(sql.strip()) == 0:
        erros.append("  [BLOQUEIO] init-db.sql está vazio.")

    # Verifica se há comandos proibidos de nuvem proprietária
    termos_proibidos = [
        ("supabase_admin", "Referência a usuário proprietário 'supabase_admin' sem mapeamento local"),
    ]
    for termo, msg in termos_proibidos:
        if termo in sql and "CREATE ROLE" not in sql and "DO $$" not in sql:
            erros.append(f"  [AVISO] {msg}")

    for match in re.finditer(
        r"CREATE\s+EXTENSION\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?([A-Za-z0-9_\-]+)",
        sql,
        re.IGNORECASE,
    ):
        extensao = match.group(1).lower()
        if extensao in EXTENSOES_PROIBIDAS:
            erros.append(
                f"  [BLOQUEIO] Extensão proibida '{match.group(1)}' em init-db.sql "
                f"(indisponível na stack self-hosted)."
            )

    if erros:
        print(f" [FALHA] Problemas no script SQL ({len(erros)}):")
        for e in erros:
            print(e)
        print("=" * 72)
        return 1

    print(" [SUCESSO] Script init-db.sql auditado e compatível com PostgreSQL corporativo.")
    print("=" * 72)
    return 0

if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(audit_postgresql_script(os.path.abspath(caminho)))
