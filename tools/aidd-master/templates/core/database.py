# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.0-Alpha — Camada de Persistência Poliglota (DatabaseAdapter Bridge)
=============================================================================
Database é uma fachada fina que delega para um DatabaseAdapter (SQLite ou
PostgreSQL) escolhido a partir de DATABASE_URL. A API pública usada pelo
código gerado (get_connection, record_migration, enqueue_outbox_event)
permanece idêntica independente do motor escolhido: os módulos gerados por
add_module.py continuam usando `?` como placeholder e `cur.lastrowid` sem
nenhuma alteração, mesmo rodando contra PostgreSQL.
"""

import os
import re
import json
import uuid
import sqlite3
import datetime
import hashlib
from abc import ABC, abstractmethod


def append_audit_log(cursor, action: str, payload: dict):
    cursor.execute("SELECT curr_hash FROM _audit_log ORDER BY timestamp DESC LIMIT 1;")
    row = cursor.fetchone()
    prev_hash = '0' * 64
    if row:
        prev_hash = row["curr_hash"] if isinstance(row, dict) else row[0]
    payload_json = json.dumps(payload, sort_keys=True)
    curr_hash = hashlib.sha256(f"{prev_hash}{action}{payload_json}".encode('utf-8')).hexdigest()
    log_id = uuid.uuid4().hex
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO _audit_log (id, timestamp, action, payload, prev_hash, curr_hash) VALUES (?, ?, ?, ?, ?, ?)",
        (log_id, timestamp, action, payload_json, prev_hash, curr_hash)
    )

def enable_rls_tenant(cursor, table_name: str):
    if hasattr(cursor, '_cursor') or type(cursor).__name__ == 'PostgresCursorProxy':
        cursor.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
        cursor.execute(f"CREATE POLICY tenant_isolation ON {table_name} USING (tenant_id = current_setting('app.current_tenant_id')::uuid);")
    else:
        # RLS enforced at application layer
        pass

def set_tenant(cursor, tenant_id: str):
    if hasattr(cursor, '_cursor') or type(cursor).__name__ == 'PostgresCursorProxy':
        cursor.execute(f"SET app.current_tenant_id = '{tenant_id}';")
    else:
        # RLS enforced at application layer
        pass


_PLACEHOLDER_RE = re.compile(r"\?")
_AUTOINCREMENT_RE = re.compile(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", re.IGNORECASE)


def _translate_ddl_for_postgres(sql: str) -> str:
    """Traduz o dialeto DDL SQLite (gerado por add_module.py/models.py) para PostgreSQL."""
    return _AUTOINCREMENT_RE.sub("SERIAL PRIMARY KEY", sql)


class DatabaseAdapter(ABC):
    """Contrato mínimo que qualquer motor de persistência precisa cumprir."""

    @abstractmethod
    def get_connection(self):
        ...

    @abstractmethod
    def init_system_tables(self):
        ...


class SQLiteAdapter(DatabaseAdapter):
    """Motor local embarcado (Zero Setup). Comportamento idêntico ao pré-v5.0."""

    def __init__(self, db_url: str):
        self.db_path = db_url.replace("sqlite:///", "")

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def init_system_tables(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS _schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module_name TEXT NOT NULL UNIQUE,
                    version INTEGER NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS _outbox_events (
                    id TEXT PRIMARY KEY,
                    event_name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pendente',
                    criado_em TEXT NOT NULL,
                    processado_em TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_outbox_status ON _outbox_events(status);
                CREATE TABLE IF NOT EXISTS _audit_log (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    curr_hash TEXT NOT NULL
                );
            """)
            conn.commit()
        finally:
            conn.close()


class PostgresCursorProxy:
    """Emula a superfície do cursor sqlite3 (fetchone/fetchall/lastrowid) sobre psycopg2."""

    def __init__(self, real_cursor):
        self._cursor = real_cursor
        self._lastrowid = None

    def execute(self, query: str, params=None):
        params = params or ()
        translated = _PLACEHOLDER_RE.sub("%s", query)

        stripped = translated.strip().upper()
        is_insert = stripped.startswith("INSERT")
        already_has_returning = "RETURNING" in stripped
        if is_insert and not already_has_returning:
            translated = translated.rstrip().rstrip(";") + " RETURNING id"

        self._cursor.execute(translated, params)

        if is_insert:
            try:
                row = self._cursor.fetchone()
                self._lastrowid = row["id"] if row else None
            except Exception:
                self._lastrowid = None
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount


class PostgresConnectionProxy:
    """Emula a superfície da conexão sqlite3 (execute/executemany/executescript/context manager)
    sobre uma conexão psycopg2 real, permitindo que código escrito para SQLite rode sem alteração."""

    def __init__(self, real_conn):
        self._conn = real_conn

    def execute(self, query: str, params=None):
        cursor_proxy = PostgresCursorProxy(self._conn.cursor())
        return cursor_proxy.execute(query, params)

    def executemany(self, query: str, seq_of_params):
        translated = _PLACEHOLDER_RE.sub("%s", query)
        cur = self._conn.cursor()
        cur.executemany(translated, seq_of_params)
        return cur

    def executescript(self, sql: str):
        translated = _translate_ddl_for_postgres(sql)
        cur = self._conn.cursor()
        cur.execute(translated)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._conn.rollback()
        else:
            self._conn.commit()
        return False


class PostgresAdapter(DatabaseAdapter):
    """Motor remoto (produção). Ativado quando DATABASE_URL começa com postgres(ql)://."""

    def __init__(self, db_url: str):
        self.db_url = db_url

    def _connect_raw(self):
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            raise RuntimeError("psycopg2 não instalado. Para PostgreSQL, instale: pip install psycopg2-binary")
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    def get_connection(self):
        return PostgresConnectionProxy(self._connect_raw())

    def init_system_tables(self):
        conn = self._connect_raw()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS _schema_migrations (
                    id SERIAL PRIMARY KEY,
                    module_name TEXT NOT NULL UNIQUE,
                    version INTEGER NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS _outbox_events (
                    id TEXT PRIMARY KEY,
                    event_name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pendente',
                    criado_em TEXT NOT NULL,
                    processado_em TEXT
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_outbox_status ON _outbox_events(status);")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS _audit_log (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    curr_hash TEXT NOT NULL
                );
            """)
            conn.commit()
        finally:
            conn.close()


class Database:
    """Fachada de persistência. Escolhe o adapter a partir de DATABASE_URL e mantém
    a mesma API pública (get_connection, record_migration, enqueue_outbox_event)
    independente do motor escolhido — Zero Fricção para o código gerado."""

    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///app.db")
        self.is_postgres = self.db_url.startswith("postgres://") or self.db_url.startswith("postgresql://")
        self._adapter = PostgresAdapter(self.db_url) if self.is_postgres else SQLiteAdapter(self.db_url)
        self._adapter.init_system_tables()

    def get_connection(self):
        return self._adapter.get_connection()

    def record_migration(self, module_name: str, version: int = 1):
        """Registra a aplicação idempotente de schema para um módulo."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO _schema_migrations (module_name, version, applied_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(module_name) DO UPDATE SET version = ?, applied_at = CURRENT_TIMESTAMP;
            """, (module_name, version, version))
            conn.commit()

    def enqueue_outbox_event(self, conn, event_name: str, payload: dict) -> str:
        """Transactional Outbox Pattern: grava o evento na MESMA transação/conexão da
        mutação de negócio, garantindo entrega at-least-once mesmo se o processo cair
        antes do EventBus.emit() em memória ser disparado."""
        event_id = uuid.uuid4().hex
        criado_em = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO _outbox_events (id, event_name, payload, status, criado_em)
            VALUES (?, ?, ?, 'pendente', ?)
            """,
            (event_id, event_name, json.dumps(payload, ensure_ascii=False), criado_em)
        )
        return event_id
