import sqlite3

def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS progresso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            aula_id INTEGER NOT NULL,
            concluida INTEGER DEFAULT 1,
            data_conclusao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(usuario_id, aula_id)
        );
    """)
    conn.commit()
