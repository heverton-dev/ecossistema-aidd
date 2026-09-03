import sqlite3
def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            empresa TEXT,
            score INTEGER DEFAULT 50,
            status TEXT DEFAULT 'novo',
            origem TEXT DEFAULT 'Inbound Website',
            valor_estimado REAL DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
    """)
    conn.commit()
