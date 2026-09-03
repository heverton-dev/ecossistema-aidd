import sqlite3

def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS planos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            preco_mensal REAL NOT NULL,
            beneficios_json TEXT NOT NULL,
            destaque INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS assinaturas_ativas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            plano_id INTEGER NOT NULL,
            status TEXT DEFAULT 'ativo',
            iniciada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY(plano_id) REFERENCES planos(id)
        );
    """)
    conn.commit()
