# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.0 — Polyglot Database Adapter Layer
=============================================================================
Unified adapter interface for SQLite, PostgreSQL, and Supabase.
Builds on the existing RLSConnection / PostgresConnectionProxy infrastructure
in database.py, adding connection pooling, a factory, and Supabase support.

Usage::

    from database_adapter import DatabaseFactory

    adapter = DatabaseFactory.create("sqlite:///app.db")
    with adapter.get_connection() as conn:
        conn.execute("INSERT INTO t (x) VALUES (?)", (1,))

    adapter = DatabaseFactory.create("postgresql://user:pass@host:5432/db")
    # ... same API

    adapter = DatabaseFactory.create("supabase://db.xxxx.supabase.co:5432/postgres")
    # ... same API, SSL enforced, RLS ready
"""

from __future__ import annotations

import os
import re
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Import existing infrastructure from database.py
# ---------------------------------------------------------------------------
try:
    from core.database import (
        RLSConnection,
        RLS_TABLE_REGISTRY,
        PostgresConnectionProxy,
        PostgresCursorProxy,
        append_audit_log,
        enable_rls_tenant,
        set_tenant,
        _translate_ddl_for_postgres,
    )
except ImportError:
    from database import (
        RLSConnection,
        RLS_TABLE_REGISTRY,
        PostgresConnectionProxy,
        PostgresCursorProxy,
        append_audit_log,
        enable_rls_tenant,
        set_tenant,
        _translate_ddl_for_postgres,
    )


# =========================================================================
# Abstract Base
# =========================================================================

class DatabaseAdapter(ABC):
    """Contrato poliglota: qualquer motor de persistência implementa isto."""

    @abstractmethod
    def connect(self) -> Any:
        """Open and return a raw connection (or proxy) to the database."""

    @abstractmethod
    def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a single query and return the cursor/result."""

    @abstractmethod
    def close(self) -> None:
        """Release all resources (connections, pools)."""

    @abstractmethod
    def get_connection(self):
        """Return a connection (context-manager capable) for scoped usage."""

    # -- convenience -------------------------------------------------------

    @contextmanager
    def connection(self):
        """Context manager that yields a connection, commits on success,
        rolls back on error, and closes on exit."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# =========================================================================
# Lightweight result wrapper for execute()
# =========================================================================

class _SQLiteResult:
    """Returned by ``SQLiteAdapter.execute()``.  Wraps fetched rows and
    exposes ``lastrowid`` / ``rowcount`` so callers can use the same
    interface as a raw cursor."""

    def __init__(self, rows: list, lastrowid: int | None = None, rowcount: int = 0):
        self._rows = rows
        self._idx = 0
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    def fetchone(self):
        if self._idx < len(self._rows):
            row = self._rows[self._idx]
            self._idx += 1
            return row
        return None

    def fetchall(self):
        return self._rows[self._idx:]

    def __iter__(self):
        return iter(self._rows)


# =========================================================================
# SQLite Adapter — wraps existing WAL + RLSConnection
# =========================================================================

class SQLiteAdapter(DatabaseAdapter):
    """Local embedded engine.  WAL mode, foreign keys, RLSConnection when
    RLS_TABLE_REGISTRY is populated.  Drop-in for the pre-v5.0 behaviour."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self) -> RLSConnection:
        return self.get_connection()

    def get_connection(self) -> RLSConnection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.row_factory = sqlite3.Row
        return RLSConnection(conn)

    def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a single query with auto-commit.

        For SELECT-like queries, returns a ``_SQLiteResult`` with fetched rows
        (so the connection can be closed immediately).  For DML/DDL, returns a
        lightweight result with ``lastrowid`` and ``rowcount``.

        Use ``get_connection()`` / ``connection()`` for multi-statement
        transactions where you need the connection to stay open."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.row_factory = sqlite3.Row
            rls_conn = RLSConnection(conn)
            cur = rls_conn.execute(query, params)
            clean = query.strip().upper()
            is_select = clean.startswith("SELECT") or clean.startswith("PRAGMA")
            if is_select:
                rows = cur.fetchall()
                conn.commit()
                return _SQLiteResult(rows, lastrowid=None, rowcount=len(rows))
            else:
                conn.commit()
                return _SQLiteResult([], lastrowid=cur.lastrowid, rowcount=cur.rowcount)
        finally:
            conn.close()

    def close(self) -> None:
        """SQLite is file-based; nothing persistent to tear down."""


# =========================================================================
# PostgreSQL Adapter — with simple connection pooling
# =========================================================================

class _ConnectionPool:
    """Minimal thread-safe connection pool for psycopg2 connections."""

    def __init__(self, dsn: str, min_conn: int = 1, max_conn: int = 5):
        self._dsn = dsn
        self._min = min_conn
        self._max = max_conn
        self._pool: list = []
        self._lock = threading.Lock()
        self._in_use = 0
        self._closed = False
        # Pool is lazy: connections are created on first acquire(), not at init.
        # This avoids requiring a live server just to instantiate the adapter.

    def _make_raw(self):
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            raise RuntimeError(
                "psycopg2 não instalado. "
                "Para PostgreSQL, instale: pip install psycopg2-binary"
            )
        return psycopg2.connect(self._dsn, cursor_factory=RealDictCursor)

    def _warm(self):
        """Pre-fill pool up to min_conn."""
        for _ in range(self._min):
            self._pool.append(self._make_raw())

    def acquire(self):
        with self._lock:
            if self._closed:
                raise RuntimeError("Pool is closed")
            if self._pool:
                self._in_use += 1
                return self._pool.pop()
            if self._in_use < self._max:
                self._in_use += 1
                return self._make_raw()
        # Pool exhausted — block until one is returned
        while True:
            with self._lock:
                if self._pool:
                    self._in_use += 1
                    return self._pool.pop()
            time.sleep(0.01)

    def release(self, conn):
        with self._lock:
            self._in_use -= 1
            if not self._closed:
                self._pool.append(conn)
            else:
                conn.close()

    def close_all(self):
        with self._lock:
            self._closed = True
            while self._pool:
                self._pool.pop().close()


class PostgreSQLAdapter(DatabaseAdapter):
    """Remote production engine with connection pooling.
    Activated when URL starts with ``postgresql://``."""

    def __init__(self, dsn: str, min_conn: int = 1, max_conn: int = 5):
        self.dsn = dsn
        self._pool = _ConnectionPool(dsn, min_conn, max_conn)

    def connect(self) -> PostgresConnectionProxy:
        raw = self._pool.acquire()
        return PostgresConnectionProxy(raw)

    def get_connection(self) -> PostgresConnectionProxy:
        return self.connect()

    def execute(self, query: str, params: tuple = ()) -> Any:
        with self.connection() as conn:
            return conn.execute(query, params)

    def close(self) -> None:
        self._pool.close_all()

    @contextmanager
    def connection(self):
        """Acquire from pool, commit on success, rollback on error,
        always return to pool."""
        proxy = self.connect()
        try:
            yield proxy
            proxy.commit()
        except Exception:
            proxy.rollback()
            raise
        finally:
            self._pool.release(proxy._conn)


# =========================================================================
# Supabase Adapter — PostgreSQL + SSL + RLS
# =========================================================================

class SupabaseAdapter(DatabaseAdapter):
    """Wraps PostgreSQLAdapter with Supabase-specific configuration:
    SSL required, Row Level Security integration, service role key support."""

    def __init__(
        self,
        host: str,
        port: int = 5432,
        dbname: str = "postgres",
        user: str = "postgres",
        password: str = "",
        sslmode: str = "require",
        service_role_key: Optional[str] = None,
    ):
        self.service_role_key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        dsn = (
            f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
            f"?sslmode={sslmode}"
        )
        self._pg = PostgreSQLAdapter(dsn)

    def connect(self) -> PostgresConnectionProxy:
        return self._pg.connect()

    def get_connection(self) -> PostgresConnectionProxy:
        return self._pg.get_connection()

    def execute(self, query: str, params: tuple = ()) -> Any:
        return self._pg.execute(query, params)

    def close(self) -> None:
        self._pg.close()

    @contextmanager
    def connection(self):
        with self._pg.connection() as conn:
            yield conn


# =========================================================================
# Factory — auto-detect adapter from connection string
# =========================================================================

_SUPABASE_HOST_RE = re.compile(r"\.supabase\.", re.IGNORECASE)


class DatabaseFactory:
    """Create the right adapter from a DATABASE_URL."""

    @staticmethod
    def create(url: str) -> DatabaseAdapter:
        if url.startswith("sqlite:///"):
            path = url.replace("sqlite:///", "")
            return SQLiteAdapter(path)

        if url.startswith("postgresql://") or url.startswith("postgres://"):
            # Detect Supabase by host pattern
            host_part = url.split("@")[-1].split("/")[0] if "@" in url else ""
            if _SUPABASE_HOST_RE.search(host_part):
                return DatabaseFactory._parse_supabase(url)
            return PostgreSQLAdapter(url)

        raise ValueError(f"Unsupported DATABASE_URL scheme: {url!r}")

    @staticmethod
    def _parse_supabase(url: str) -> SupabaseAdapter:
        # postgresql://user:pass@host:port/dbname?sslmode=require
        clean = url.replace("postgres://", "postgresql://")
        without_scheme = clean[len("postgresql://"):]
        user_pass, host_db = without_scheme.split("@", 1)
        user, password = user_pass.split(":", 1) if ":" in user_pass else (user_pass, "")
        host_port, dbname = host_db.split("/", 1)
        dbname = dbname.split("?")[0]  # strip query params
        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            port = int(port)
        else:
            host, port = host_port, 5432
        return SupabaseAdapter(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
