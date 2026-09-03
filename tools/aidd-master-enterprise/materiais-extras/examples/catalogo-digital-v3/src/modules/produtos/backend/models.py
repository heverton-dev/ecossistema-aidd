import sqlite3

def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            preco REAL NOT NULL,
            preco_promo REAL,
            categoria TEXT NOT NULL,
            thumbnail TEXT NOT NULL,
            estoque INTEGER DEFAULT 50,
            destaque INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_produtos_cat ON produtos(categoria, ativo);
    """)
    conn.commit()
