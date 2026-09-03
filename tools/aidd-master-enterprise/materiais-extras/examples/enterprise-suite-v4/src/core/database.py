import sqlite3, os
from contextlib import contextmanager

class Database:
    def __init__(self, uri: str):
        self.uri = uri
        self.is_sqlite = uri.startswith("sqlite:///")
        self.db_path = uri.replace("sqlite:///", "") if self.is_sqlite else ""
        if self.is_sqlite:
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            with sqlite3.connect(self.db_path) as c:
                c.execute("PRAGMA journal_mode=WAL;")
                c.execute("PRAGMA synchronous=NORMAL;")

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
