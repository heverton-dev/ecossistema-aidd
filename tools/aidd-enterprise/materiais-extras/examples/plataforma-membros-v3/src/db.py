import sqlite3

class Database:
    def __init__(self, db_path="banco_membros.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    senha_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'aluno',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

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
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY(curso_id) REFERENCES cursos(id),
                    UNIQUE(usuario_id, curso_id)
                );

                CREATE TABLE IF NOT EXISTS progresso (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    aula_id INTEGER NOT NULL,
                    concluida INTEGER DEFAULT 1,
                    data_conclusao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY(aula_id) REFERENCES aulas(id),
                    UNIQUE(usuario_id, aula_id)
                );

                CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
                CREATE INDEX IF NOT EXISTS idx_aulas_curso ON aulas(curso_id, ordem);
            """)
            conn.commit()
