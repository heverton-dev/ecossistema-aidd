# -*- coding: utf-8 -*-
"""
Testes de integração reais sobre o motor SQLAlchemy (NIH #8).

Cobrem os três caminhos que a troca de motor introduziu:

1. Facade legada (RLSConnection sobre EngineFacadeConnection): código gerado
   continua vendo sqlite3.Row e WAL, mas a conexão vem do pool do Engine.
2. ORM SQLAlchemy (session_factory): provar que o Engine exposto é usável por
   uma sessão ORM real (metadata autoload + insert/select).
3. Async aiosqlite (async_engine + init_async): round-trip assíncrono real e
   reafirmação do modo WAL no fluxo assíncrono.

Nenhum mock — tudo roda contra arquivos SQLite reais em tmp_path.
"""

import asyncio
import os
import sys

import pytest

# Ensure src/core is importable
CORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src", "core"))
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

from sqlalchemy import MetaData, Table, select  # noqa: E402

from database_adapter import (  # noqa: E402
    SQLiteAdapter,
    RLS_TABLE_REGISTRY,
    set_tenant,
)
from database import Database  # noqa: E402


def _run(coro):
    return asyncio.run(coro)


# =========================================================================
# 1. Facade legada — WAL vindo do Engine SQLAlchemy
# =========================================================================

class TestFacadeWALViaSQLAlchemy:
    def test_wal_on_new_pooled_connection(self, tmp_path):
        adapter = SQLiteAdapter(str(tmp_path / "facade.db"))
        with adapter.get_connection() as conn:
            assert conn._conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            assert conn._conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1

    def test_wal_applied_on_every_fresh_connection(self, tmp_path):
        """Pysqlite usa NullPool para arquivo: cada connect() é uma conexão
        nova, e o event listener do Engine deve reaplicar o WAL em todas."""
        adapter = SQLiteAdapter(str(tmp_path / "facade2.db"))
        for _ in range(5):
            with adapter.get_connection() as conn:
                assert conn._conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"

    def test_rows_are_sqlite3_row_through_facade(self, tmp_path):
        adapter = SQLiteAdapter(str(tmp_path / "facade3.db"))
        with adapter.get_connection() as conn:
            conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)")
            conn.execute("INSERT INTO items (nome) VALUES (?)", ("chave de neve",))
            row = conn.execute("SELECT id, nome FROM items").fetchone()
            assert row["nome"] == "chave de neve"
            assert dict(row)["id"] == 1


class TestDatabaseFacadeWAL:
    def test_database_get_connection_reports_wal(self, tmp_path):
        db = Database(f"sqlite:///{tmp_path}/facade4.db")
        try:
            with db.get_connection() as conn:
                assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        finally:
            db._adapter._engine.dispose()


# =========================================================================
# 2. ORM SQLAlchemy — session_factory real contra o Engine da adapter
# =========================================================================

class TestORMSession:
    def test_orm_session_crud_through_engine(self, tmp_path):
        adapter = SQLiteAdapter(str(tmp_path / "orm.db"))
        with adapter.get_connection() as conn:
            conn.execute(
                "CREATE TABLE produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT NOT NULL, preco REAL)"
            )

        metadata = MetaData()
        produtos = Table("produtos", metadata, autoload_with=adapter.engine)

        with adapter.session_factory() as session:
            session.execute(produtos.insert().values(sku="A-001", preco=9.99))
            session.commit()

        with adapter.session_factory() as session:
            rows = session.execute(select(produtos)).all()
            assert len(rows) == 1
            assert rows[0].sku == "A-001"
        adapter.close()

    def test_rls_tenant_filter_through_facade_and_orm(self, tmp_path):
        RLS_TABLE_REGISTRY.add("pedidos")
        try:
            adapter = SQLiteAdapter(str(tmp_path / "rls.db"))
            with adapter.get_connection() as conn:
                conn.execute(
                    "CREATE TABLE pedidos (id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT, valor REAL)"
                )

            set_tenant(None, "tenant_a")
            with adapter.get_connection() as conn:
                conn.execute("INSERT INTO pedidos (tenant_id, valor) VALUES (?, ?)", ("ignorado", 1.0))
                conn.execute("INSERT INTO pedidos (valor) VALUES (?)", (2.0,))
                rows = conn.execute("SELECT * FROM pedidos").fetchall()
                assert len(rows) == 1
                assert rows[0]["tenant_id"] == "tenant_a"
                conn.execute("DELETE FROM pedidos")
                assert len(conn.execute("SELECT * FROM pedidos").fetchall()) == 0

            set_tenant(None, None)
            with adapter.get_connection() as conn:
                conn.execute("DELETE FROM pedidos")
            metadata = MetaData()
            pedidos = Table("pedidos", metadata, autoload_with=adapter.engine)
            with adapter.session_factory() as session:
                assert session.execute(select(pedidos)).all() == []
            adapter.close()
        finally:
            RLS_TABLE_REGISTRY.discard("pedidos")


# =========================================================================
# 3. Async aiosqlite — round-trip real + WAL persistente
# =========================================================================

class TestAsyncAiosqlite:
    def test_async_roundtrip_and_wal(self, tmp_path):
        adapter = SQLiteAdapter(str(tmp_path / "async.db"))
        with adapter.get_connection() as conn:
            conn.execute("CREATE TABLE notas (id INTEGER PRIMARY KEY AUTOINCREMENT, texto TEXT)")

        _run(adapter.init_async())

        async def _crud():
            async with adapter.async_engine.connect() as conn:
                await conn.exec_driver_sql("INSERT INTO notas (texto) VALUES (?)", ("hello async",))
                res = await conn.exec_driver_sql("SELECT texto FROM notas")
                rows = res.fetchall()
                mode = (await conn.exec_driver_sql("PRAGMA journal_mode")).fetchone()[0]
                return rows, mode

        rows, mode = _run(_crud())
        assert [r[0] for r in rows] == ["hello async"]
        assert mode == "wal"
        adapter.close()

    def test_async_engine_over_shared_file_sees_sync_writes(self, tmp_path):
        adapter = SQLiteAdapter(str(tmp_path / "shared.db"))
        with adapter.get_connection() as conn:
            conn.execute("CREATE TABLE msg (id INTEGER PRIMARY KEY AUTOINCREMENT, corpo TEXT)")
            conn.execute("INSERT INTO msg (corpo) VALUES (?)", ("sync write",))

        _run(adapter.init_async())

        async def _read():
            async with adapter.async_engine.connect() as conn:
                res = await conn.exec_driver_sql("SELECT corpo FROM msg")
                return res.fetchall()

        assert [r[0] for r in _run(_read())] == ["sync write"]
        adapter.close()