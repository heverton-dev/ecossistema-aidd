import sqlite3
def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor REAL NOT NULL,
            data_vencimento DATE NOT NULL,
            data_pagamento DATE,
            status TEXT DEFAULT 'pendente',
            entidade_nome TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_lanc_tipo ON lancamentos(tipo, status);
    """)
    conn.commit()
