import os, sqlite3

class Database:
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///app.db")
        self.is_postgres = self.db_url.startswith("postgres://") or self.db_url.startswith("postgresql://")
        
    def get_connection(self):
        if self.is_postgres:
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
                return conn
            except ImportError:
                raise RuntimeError("psycopg2 não instalado. Para PostgreSQL, instale: pip install psycopg2-binary")
        else:
            db_path = self.db_url.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.row_factory = sqlite3.Row
            return conn
