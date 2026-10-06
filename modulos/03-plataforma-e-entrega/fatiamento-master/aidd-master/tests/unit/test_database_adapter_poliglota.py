# -*- coding: utf-8 -*-
"""
Tests for the Polyglot DatabaseAdapter layer (database_adapter.py).

- SQLiteAdapter: real CRUD via tmp_path
- DatabaseFactory: URL parsing and auto-detection
- Connection context manager: commit/rollback semantics
- PostgreSQLAdapter: tested with fakes (no real server needed)
"""

import os
import sys
import sqlite3
import threading

import pytest

# Ensure src/core is importable
CORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src", "core"))
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

from database_adapter import (  # noqa: E402
    DatabaseAdapter,
    SQLiteAdapter,
    PostgreSQLAdapter,
    SupabaseAdapter,
    DatabaseFactory,
    _ConnectionPool,
)


# =========================================================================
# SQLiteAdapter — real CRUD
# =========================================================================

class TestSQLiteAdapter:
    def _make_adapter(self, tmp_path, name="test.db"):
        db_file = tmp_path / name
        return SQLiteAdapter(str(db_file))

    def test_connect_returns_connection(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        conn = adapter.connect()
        assert conn is not None
        conn.close()

    def test_wal_mode_enabled(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        conn = adapter.connect()
        mode = conn._conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        conn.close()

    def test_foreign_keys_enabled(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        conn = adapter.connect()
        fk = conn._conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
        conn.close()

    def test_crud_create_table(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        adapter.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
        )
        # Verify table exists
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        conn.close()
        assert "items" in tables

    def test_crud_insert_and_select(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        adapter.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
        )
        cur = adapter.execute("INSERT INTO items (name) VALUES (?)", ("Widget",))
        assert cur.lastrowid == 1

        cur = adapter.execute("SELECT * FROM items WHERE id = ?", (1,))
        row = cur.fetchone()
        assert row["name"] == "Widget"

    def test_crud_update(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        adapter.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
        )
        adapter.execute("INSERT INTO items (name) VALUES (?)", ("Widget",))
        adapter.execute("UPDATE items SET name = ? WHERE id = ?", ("Gadget", 1))

        cur = adapter.execute("SELECT name FROM items WHERE id = ?", (1,))
        assert cur.fetchone()["name"] == "Gadget"

    def test_crud_delete(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        adapter.execute(
            "CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
        )
        adapter.execute("INSERT INTO items (name) VALUES (?)", ("Widget",))
        adapter.execute("DELETE FROM items WHERE id = ?", (1,))

        cur = adapter.execute("SELECT COUNT(*) as cnt FROM items")
        assert cur.fetchone()["cnt"] == 0

    def test_get_connection_context_manager_commits(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        adapter.execute("CREATE TABLE ctx_test (id INTEGER PRIMARY KEY, val TEXT)")

        with adapter.get_connection() as conn:
            conn.execute("INSERT INTO ctx_test (id, val) VALUES (?, ?)", (1, "ok"))

        cur = adapter.execute("SELECT val FROM ctx_test WHERE id = ?", (1,))
        assert cur.fetchone()["val"] == "ok"

    def test_connection_context_manager_rollback_on_error(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        adapter.execute("CREATE TABLE rb_test (id INTEGER PRIMARY KEY, val TEXT)")

        with pytest.raises(ValueError):
            with adapter.connection() as conn:
                conn.execute("INSERT INTO rb_test (id, val) VALUES (?, ?)", (1, "nope"))
                raise ValueError("boom")

        cur = adapter.execute("SELECT COUNT(*) as cnt FROM rb_test")
        assert cur.fetchone()["cnt"] == 0

    def test_close_is_safe(self, tmp_path):
        adapter = self._make_adapter(tmp_path)
        adapter.close()  # should not raise


# =========================================================================
# DatabaseFactory — URL parsing and auto-detection
# =========================================================================

class TestDatabaseFactory:
    def test_sqlite_url_returns_sqlite_adapter(self, tmp_path):
        db_file = tmp_path / "factory.db"
        adapter = DatabaseFactory.create(f"sqlite:///{db_file}")
        assert isinstance(adapter, SQLiteAdapter)

    def test_postgresql_url_returns_pg_adapter(self):
        adapter = DatabaseFactory.create("postgresql://user:pass@localhost:5432/mydb")
        assert isinstance(adapter, PostgreSQLAdapter)

    def test_postgres_shorthand_returns_pg_adapter(self):
        adapter = DatabaseFactory.create("postgres://user:pass@localhost:5432/mydb")
        assert isinstance(adapter, PostgreSQLAdapter)

    def test_supabase_host_detected(self):
        adapter = DatabaseFactory.create(
            "postgresql://postgres:pw@db.abc.supabase.co:5432/postgres"
        )
        assert isinstance(adapter, SupabaseAdapter)

    def test_supabase_host_with_custom_port(self):
        adapter = DatabaseFactory.create(
            "postgresql://postgres:secret@db.xyz.supabase.co:6543/postgres"
        )
        assert isinstance(adapter, SupabaseAdapter)
        assert "6543" in adapter._pg.dsn

    def test_unsupported_scheme_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            DatabaseFactory.create("mysql://localhost/db")

    def test_factory_sqlite_adapter_is_functional(self, tmp_path):
        db_file = tmp_path / "factory_crud.db"
        adapter = DatabaseFactory.create(f"sqlite:///{db_file}")
        adapter.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
        adapter.execute("INSERT INTO t (v) VALUES (?)", ("hello",))
        cur = adapter.execute("SELECT v FROM t WHERE id = ?", (1,))
        assert cur.fetchone()["v"] == "hello"


# =========================================================================
# PostgreSQLAdapter — with fakes (no real server needed)
# =========================================================================

class _FakePSCursor:
    """Mimics psycopg2 RealDictCursor."""
    def __init__(self):
        self.executed = []
        self.rowcount = 1

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def close(self):
        pass


class _FakePSConnection:
    """Mimics psycopg2 connection."""
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, cursor_factory=None):
        return _FakePSCursor()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class TestPostgreSQLAdapter:
    def test_connection_proxy_wraps_raw(self):
        from database import PostgresConnectionProxy
        raw = _FakePSConnection()
        proxy = PostgresConnectionProxy(raw)
        result = proxy.execute("SELECT 1")
        assert result is not None

    def test_connection_proxy_commits_on_success(self):
        from database import PostgresConnectionProxy
        raw = _FakePSConnection()
        with PostgresConnectionProxy(raw) as conn:
            conn.execute("SELECT 1")
        assert raw.committed is True
        assert raw.rolled_back is False

    def test_connection_proxy_rollback_on_error(self):
        from database import PostgresConnectionProxy
        raw = _FakePSConnection()
        with pytest.raises(RuntimeError):
            with PostgresConnectionProxy(raw) as conn:
                conn.execute("SELECT 1")
                raise RuntimeError("fail")
        assert raw.rolled_back is True
        assert raw.committed is False


# =========================================================================
# SupabaseAdapter — construction and delegation
# =========================================================================

class TestSupabaseAdapter:
    def test_construction_builds_dsn_with_ssl(self):
        adapter = SupabaseAdapter(
            host="db.test.supabase.co",
            port=5432,
            dbname="postgres",
            user="postgres",
            password="secret",
        )
        assert "db.test.supabase.co" in adapter._pg.dsn
        assert "sslmode=require" in adapter._pg.dsn

    def test_service_role_key_from_env(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key-123")
        adapter = SupabaseAdapter(host="db.x.supabase.co", password="pw")
        assert adapter.service_role_key == "test-key-123"

    def test_service_role_key_from_constructor(self):
        adapter = SupabaseAdapter(
            host="db.x.supabase.co",
            password="pw",
            service_role_key="explicit-key",
        )
        assert adapter.service_role_key == "explicit-key"


# =========================================================================
# Connection pool — basic semantics
# =========================================================================

class TestConnectionPool:
    def test_pool_raises_when_closed(self):
        pool = _ConnectionPool.__new__(_ConnectionPool)
        pool._dsn = ""
        pool._min = 0
        pool._max = 1
        pool._pool = []
        pool._lock = threading.Lock()
        pool._in_use = 0
        pool._closed = True

        with pytest.raises(RuntimeError, match="Pool is closed"):
            pool.acquire()

    def test_pool_close_all_is_idempotent(self):
        pool = _ConnectionPool.__new__(_ConnectionPool)
        pool._dsn = ""
        pool._min = 0
        pool._max = 1
        pool._pool = []
        pool._lock = threading.Lock()
        pool._in_use = 0
        pool._closed = False

        pool.close_all()
        pool.close_all()  # should not raise
