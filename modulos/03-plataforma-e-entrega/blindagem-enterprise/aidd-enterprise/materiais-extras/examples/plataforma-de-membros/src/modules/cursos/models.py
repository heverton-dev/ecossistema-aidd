import sqlite3

def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            preco REAL NOT NULL,
            thumbnail TEXT NOT NULL,
            categoria TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS aulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curso_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            duracao TEXT NOT NULL,
            video_url TEXT NOT NULL,
            ordem INTEGER NOT NULL,
            FOREIGN KEY(curso_id) REFERENCES cursos(id)
        );
        CREATE TABLE IF NOT EXISTS matriculas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            curso_id INTEGER NOT NULL,
            data_matricula TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(usuario_id, curso_id)
        );
    """)
    conn.commit()
