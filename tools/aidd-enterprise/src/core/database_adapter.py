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
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Optional

from sqlalchemy.orm import sessionmaker

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
        _create_sqlite_engine,
        EngineFacadeConnection,
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
        _create_sqlite_engine,
        EngineFacadeConnection,
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
    RLS_TABLE_REGISTRY is populated.  Drop-in for the pre-v5.0 behaviour.

    Since the NIH #8 engine swap, pooling and WAL are managed by SQLAlchemy
    (``_create_sqlite_engine``): connections come from the Engine pool and the
    PRAGMAs (journal_mode=WAL, synchronous, busy_timeout, foreign_keys) are
    applied by the engine connect-listener.  ``connect()``/``get_connection()``
    return the legacy facade (``RLSConnection`` over ``EngineFacadeConnection``)
    so callers keep the sqlite3-compatible surface (sqlite3.Row rows,
    ``lastrowid``, ``executescript``...)."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._engine = _create_sqlite_engine(db_path)
        self._session_factory = sessionmaker(self._engine)
        self._async_engine = None

    @property
    def engine(self):
        """Engine SQLAlchemy síncrono (pysqlite) — WAL via event listener."""
        return self._engine

    @property
    def session_factory(self):
        """sessionmaker (ORM SQLAlchemy) ligado ao Engine desta adapter."""
        return self._session_factory

    @property
    def async_engine(self):
        """AsyncEngine SQLAlchemy sobre aiosqlite para o mesmo arquivo.

        Criado sob demanda; WAL já está persistido no arquivo pelo Engine
        síncrono. Use ``await adapter.init_async()`` uma vez para reafirmar os
        PRAGMAs no fluxo assíncrono."""
        if self._async_engine is None:
            from sqlalchemy.ext.asyncio import create_async_engine
            self._async_engine = create_async_engine(
                f"sqlite+aiosqlite:///{self.db_path}",
                connect_args={"timeout": 10.0},
            )
        return self._async_engine

    async def init_async(self):
        """Aplica WAL/PRAGMAs no AsyncEngine (aiosqlite). Idempotente.

        journal_mode=WAL é persistente no arquivo; os demais PRAGMAs são
        reafirmados na conexão de bootstrap deste engine assíncrono."""
        async with self.async_engine.connect() as conn:
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            await conn.exec_driver_sql("PRAGMA busy_timeout=5000;")
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")

    def connect(self) -> RLSConnection:
        return self.get_connection()

    def get_connection(self) -> RLSConnection:
        return RLSConnection(EngineFacadeConnection(self._engine.connect()))

    def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a single query with auto-commit.

        For SELECT-like queries, returns a ``_SQLiteResult`` with fetched rows
        (so the connection can be closed immediately).  For DML/DDL, returns a
        lightweight result with ``lastrowid`` and ``rowcount``.

        Use ``get_connection()`` / ``connection()`` for multi-statement
        transactions where you need the connection to stay open."""
        with self._engine.connect() as sqlalchemy_conn:
            facade = EngineFacadeConnection(sqlalchemy_conn)
            rls_conn = RLSConnection(facade)
            cur = rls_conn.execute(query, params)
            rls_conn.commit()
            clean = query.strip().upper()
            is_select = clean.startswith("SELECT") or clean.startswith("PRAGMA")
            if is_select:
                rows = cur.fetchall()
                return _SQLiteResult(rows, lastrowid=None, rowcount=len(rows))
            return _SQLiteResult([], lastrowid=cur.lastrowid, rowcount=cur.rowcount)

    def close(self) -> None:
        """Dispose the engine pools (sync + async) and release all file handles."""
        if self._engine is not None:
            self._engine.dispose()
        if self._async_engine is not None:
            self._async_engine.sync_engine.dispose()
            self._async_engine = None


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
