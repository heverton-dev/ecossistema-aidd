import sqlite3

class Database:
    def __init__(self, db_path="loja.db"):
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
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    senha_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'admin'
                );

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

                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_nome TEXT,
                    itens_json TEXT NOT NULL,
                    valor_total REAL NOT NULL,
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'enviado_whatsapp'
                );

                CREATE INDEX IF NOT EXISTS idx_produtos_cat ON produtos(categoria, ativo);
            """)
            conn.commit()
