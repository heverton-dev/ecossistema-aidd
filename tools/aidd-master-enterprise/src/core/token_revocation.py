# -*- coding: utf-8 -*-
"""
AIDD v5.1 — Token Revocation List (TRL Híbrida em Memória + SQLite)
"""
import time
import threading
from typing import Dict

class TokenRevocationList:
    """TRL híbrida (em memória + SQLite-backed). Revogação instantânea de JWTs pelo jti."""
    _store: Dict[str, float] = {}
    _lock = threading.Lock()
    _db = None

    @classmethod
    def configure(cls, db):
        """Habilita persistência SQLite para revogação durável de tokens."""
        cls._db = db
        try:
            with db.get_connection() as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS _revoked_tokens (
                        jti TEXT PRIMARY KEY,
                        exp REAL NOT NULL,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_revoked_exp ON _revoked_tokens(exp);
                """)
                conn.commit()
        except Exception:
            pass

    @classmethod
    def revoke(cls, jti: str, exp: float):
        with cls._lock:
            cls._store[jti] = exp
        if cls._db:
            try:
                with cls._db.get_connection() as conn:
                    conn.execute("INSERT OR REPLACE INTO _revoked_tokens (jti, exp) VALUES (?, ?)", (jti, exp))
                    conn.commit()
            except Exception:
                pass

    @classmethod
    def is_revoked(cls, jti: str) -> bool:
        cls._purge()
        with cls._lock:
            if jti in cls._store:
                return True
        if cls._db:
            try:
                with cls._db.get_connection() as conn:
                    row = conn.execute("SELECT jti FROM _revoked_tokens WHERE jti = ? AND exp > ?", (jti, time.time())).fetchone()
                    if row:
                        return True
            except Exception:
                pass
        return False

    @classmethod
    def _purge(cls):
        now = time.time()
        with cls._lock:
            expired = [k for k, v in cls._store.items() if v < now]
            for k in expired:
                del cls._store[k]
        if cls._db:
            try:
                with cls._db.get_connection() as conn:
                    conn.execute("DELETE FROM _revoked_tokens WHERE exp <= ?", (now,))
                    conn.commit()
            except Exception:
                pass
