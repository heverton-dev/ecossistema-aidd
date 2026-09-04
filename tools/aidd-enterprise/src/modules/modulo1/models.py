# -*- coding: utf-8 -*-
"""
Schema e inicialização de banco de dados para o módulo 'modulo1'.
"""

import sqlite3
import json


def init_schema(conn: sqlite3.Connection):
    """Cria a tabela, índices e insere seed data do módulo modulo1 se não existirem."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mod_modulo1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            dados_json TEXT,
            status TEXT DEFAULT 'ativo',
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deletado_em TIMESTAMP DEFAULT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_modulo1_ativo ON mod_modulo1(ativo);
        CREATE INDEX IF NOT EXISTS idx_modulo1_status ON mod_modulo1(status);
        CREATE INDEX IF NOT EXISTS idx_modulo1_deletado ON mod_modulo1(deletado_em);
    """)
    conn.commit()

    # Seed Fixtures Determinísticas (se a tabela estiver vazia)
    result = conn.execute("SELECT count(*) FROM mod_modulo1 WHERE deletado_em IS NULL").fetchone()
    if result[0] == 0:
        conn.executemany("""
            INSERT INTO mod_modulo1 (titulo, descricao, dados_json, status, ativo)
            VALUES (?, ?, ?, 'ativo', 1);
        """, [
            (f"Registro Exemplo 01 - MODULO1", f"Primeiro registro semeado para o módulo modulo1", json.dumps({"origem": "seed", "tag": "demo"})),
            (f"Registro Exemplo 02 - MODULO1", f"Segundo registro semeado para validação de KPIs", json.dumps({"origem": "seed", "tag": "producao"}))
        ])
        conn.commit()
