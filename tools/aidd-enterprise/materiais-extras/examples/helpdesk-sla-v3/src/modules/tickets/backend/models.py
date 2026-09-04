import sqlite3
def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocolo TEXT UNIQUE NOT NULL,
            assunto TEXT NOT NULL,
            descricao TEXT NOT NULL,
            cliente_nome TEXT NOT NULL,
            cliente_email TEXT NOT NULL,
            prioridade TEXT DEFAULT 'P3',
            status TEXT DEFAULT 'aberto',
            sla_limite_horas INTEGER DEFAULT 24,
            agente_responsavel TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_tickets_prio ON tickets(prioridade, status);
    """)
    conn.commit()
