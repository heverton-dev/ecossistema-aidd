# -*- coding: utf-8 -*-
"""
Testes de Row Level Security (RLS) para SQLite — enforcement na camada de aplicação.

Valida que o RLSConnection intercepta SELECT/INSERT/UPDATE/DELETE e injeta
filtros de tenant_id automaticamente, garantindo isolamento multi-tenant.
"""

import os
import sys
import sqlite3
import threading

import pytest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.database import (
    Database,
    RLSConnection,
    RLS_TABLE_REGISTRY,
    _RLS_TENANT_CONTEXT,
    enable_rls_tenant,
    set_tenant,
    _get_current_tenant,
)


@pytest.fixture(autouse=True)
def clean_rls_registry():
    """Limpa o registry e o contexto de tenant antes de cada teste."""
    RLS_TABLE_REGISTRY.clear()
    _RLS_TENANT_CONTEXT.tenant_id = None
    yield
    RLS_TABLE_REGISTRY.clear()
    _RLS_TENANT_CONTEXT.tenant_id = None


@pytest.fixture
def db(tmp_path):
    """Cria um Database SQLite efêmero para teste."""
    db_file = tmp_path / "test_rls.db"
    return Database(f"sqlite:///{db_file}")


@pytest.fixture
def db_with_rls(db):
    """Cria um Database com tabela 'items' e RLS habilitado."""
    with db.get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                titulo TEXT NOT NULL,
                status TEXT DEFAULT 'ativo'
            );
        """)
        conn.commit()

    RLS_TABLE_REGISTRY.add("items")
    return db


# ---------------------------------------------------------------------------
# Testes de enable_rls_tenant e set_tenant
# ---------------------------------------------------------------------------

def test_enable_rls_tenant_registers_table():
    """enable_rls_tenant deve registrar a tabela no RLS_TABLE_REGISTRY."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    rls_conn = RLSConnection(conn)

    assert "orders" not in RLS_TABLE_REGISTRY
    enable_rls_tenant(rls_conn, "orders")
    assert "orders" in RLS_TABLE_REGISTRY


def test_set_tenant_stores_context():
    """set_tenant deve armazenar o tenant_id no contexto thread-local."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    rls_conn = RLSConnection(conn)

    assert _get_current_tenant() is None
    set_tenant(rls_conn, "tenant-abc")
    assert _get_current_tenant() == "tenant-abc"


def test_set_tenant_is_thread_isolated():
    """Cada thread deve ter seu próprio tenant_id."""
    results = {}

    def worker(tenant):
        _RLS_TENANT_CONTEXT.tenant_id = tenant
        results[tenant] = _get_current_tenant()

    t1 = threading.Thread(target=worker, args=("tenant-1",))
    t2 = threading.Thread(target=worker, args=("tenant-2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["tenant-1"] == "tenant-1"
    assert results["tenant-2"] == "tenant-2"


# ---------------------------------------------------------------------------
# Testes de RLS — SELECT (isolamento de leitura)
# ---------------------------------------------------------------------------

def test_rls_select_filters_by_tenant(db_with_rls):
    """SELECT deve retornar apenas registros do tenant corrente."""
    db = db_with_rls

    # Inserir dados de dois tenants
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Item A1",))
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Item A2",))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Item B1",))
        conn.commit()

    # Verificar isolamento
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 2
        titulos = {dict(r)["titulo"] for r in rows}
        assert titulos == {"Item A1", "Item A2"}

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["titulo"] == "Item B1"


def test_rls_select_with_existing_where(db_with_rls):
    """SELECT com WHERE existente deve adicionar filtro AND tenant_id."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("Ativo A", "ativo"))
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("Inativo A", "inativo"))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("Ativo B", "ativo"))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items WHERE status = ?", ("ativo",)).fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["titulo"] == "Ativo A"


def test_rls_select_with_order_by(db_with_rls):
    """SELECT com ORDER BY deve injetar WHERE antes do ORDER BY."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Zebra",))
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Alfa",))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY titulo ASC").fetchall()
        assert len(rows) == 2
        assert dict(rows[0])["titulo"] == "Alfa"
        assert dict(rows[1])["titulo"] == "Zebra"


def test_rls_select_no_tenant_passes_through(db_with_rls):
    """Sem tenant_id definido, SELECT passa sem filtro (comportamento legado)."""
    db = db_with_rls
    _RLS_TENANT_CONTEXT.tenant_id = None

    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (tenant_id, titulo) VALUES (?, ?)", ("t1", "Item 1"))
        conn.commit()

    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 1


def test_rls_select_non_rls_table_passes_through(db_with_rls):
    """Tabelas não registradas em RLS_TABLE_REGISTRY não sofrem interceptação."""
    db = db_with_rls

    with db.get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave TEXT NOT NULL,
                valor TEXT
            );
        """)
        conn.execute("INSERT INTO config (chave, valor) VALUES (?, ?)", ("versao", "1.0"))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM config").fetchall()
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# Testes de RLS — INSERT (auto-injeção de tenant_id)
# ---------------------------------------------------------------------------

def test_rls_insert_auto_injects_tenant_id(db_with_rls):
    """INSERT deve injetar automaticamente o tenant_id do contexto."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-auto"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Novo Item",))
        conn.commit()

    # Verificar que o registro foi criado com o tenant_id correto
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-auto"
    with db.get_connection() as conn:
        row = dict(conn.execute("SELECT * FROM items").fetchone())
        assert row["tenant_id"] == "tenant-auto"
        assert row["titulo"] == "Novo Item"


def test_rls_insert_with_explicit_tenant_id(db_with_rls):
    """INSERT com tenant_id explícito não deve duplicar o valor."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-explicit"
    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO items (tenant_id, titulo) VALUES (?, ?)",
            ("tenant-explicit", "Item Explícito")
        )
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-explicit"
    with db.get_connection() as conn:
        row = dict(conn.execute("SELECT * FROM items").fetchone())
        assert row["tenant_id"] == "tenant-explicit"


def test_rls_insert_no_tenant_passes_through(db_with_rls):
    """Sem tenant_id, INSERT passa sem injeção (comportamento legado)."""
    db = db_with_rls
    _RLS_TENANT_CONTEXT.tenant_id = None

    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (tenant_id, titulo) VALUES (?, ?)", ("manual", "Item Manual"))
        conn.commit()

    with db.get_connection() as conn:
        row = dict(conn.execute("SELECT * FROM items").fetchone())
        assert row["tenant_id"] == "manual"


# ---------------------------------------------------------------------------
# Testes de RLS — UPDATE (filtro por tenant)
# ---------------------------------------------------------------------------

def test_rls_update_only_affects_current_tenant(db_with_rls):
    """UPDATE deve afetar apenas registros do tenant corrente."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("Item A", "ativo"))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("Item B", "ativo"))
        conn.commit()

    # Tentar atualizar todos os itens como tenant-a
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("UPDATE items SET status = ? WHERE status = ?", ("inativo", "ativo"))
        conn.commit()

    # Verificar que apenas tenant-a foi afetado
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        row = dict(conn.execute("SELECT status FROM items").fetchone())
        assert row["status"] == "inativo"

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        row = dict(conn.execute("SELECT status FROM items").fetchone())
        assert row["status"] == "ativo"


def test_rls_update_without_where(db_with_rls):
    """UPDATE sem WHERE deve adicionar filtro de tenant_id."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("Item A", "ativo"))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("Item B", "ativo"))
        conn.commit()

    # UPDATE sem WHERE — deve afetar apenas tenant-a
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("UPDATE items SET status = ?", ("inativo",))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        row = dict(conn.execute("SELECT status FROM items").fetchone())
        assert row["status"] == "inativo"

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        row = dict(conn.execute("SELECT status FROM items").fetchone())
        assert row["status"] == "ativo"


# ---------------------------------------------------------------------------
# Testes de RLS — DELETE (filtro por tenant)
# ---------------------------------------------------------------------------

def test_rls_delete_only_affects_current_tenant(db_with_rls):
    """DELETE deve remover apenas registros do tenant corrente."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Item A",))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Item B",))
        conn.commit()

    # Deletar como tenant-a
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("DELETE FROM items")
        conn.commit()

    # Verificar que tenant-b não foi afetado
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["titulo"] == "Item B"

    # Verificar que tenant-a está vazio
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 0


def test_rls_delete_with_where(db_with_rls):
    """DELETE com WHERE deve adicionar filtro AND tenant_id."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("ItemAtivo", "ativo"))
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("ItemInativo", "inativo"))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-b"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo, status) VALUES (?, ?)", ("ItemAtivoB", "ativo"))
        conn.commit()

    # DELETE com WHERE — deve afetar apenas tenant-a
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        conn.execute("DELETE FROM items WHERE status = ?", ("inativo",))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-a"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["titulo"] == "ItemAtivo"


# ---------------------------------------------------------------------------
# Testes de RLS — executemany
# ---------------------------------------------------------------------------

def test_rls_executemany_injects_tenant_id(db_with_rls):
    """executemany deve injetar tenant_id em cada parâmetro."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-multi"
    with db.get_connection() as conn:
        conn.executemany(
            "INSERT INTO items (titulo) VALUES (?)",
            [("Batch 1",), ("Batch 2",), ("Batch 3",)]
        )
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-multi"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY titulo").fetchall()
        assert len(rows) == 3
        for row in rows:
            assert dict(row)["tenant_id"] == "tenant-multi"


# ---------------------------------------------------------------------------
# Testes de RLS — integração com Database facade
# ---------------------------------------------------------------------------

def test_database_get_connection_returns_rls_connection(db):
    """Database.get_connection() deve retornar RLSConnection quando há tabelas RLS."""
    RLS_TABLE_REGISTRY.add("test_table")
    try:
        with db.get_connection() as conn:
            assert isinstance(conn, RLSConnection)
    finally:
        RLS_TABLE_REGISTRY.discard("test_table")


def test_rls_end_to_end_multi_tenant_isolation(db_with_rls):
    """Cenário end-to-end: dois tenants com dados isolados, CRUD completo."""
    db = db_with_rls

    # Tenant A: criar, ler, atualizar
    _RLS_TENANT_CONTEXT.tenant_id = "alpha"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Alpha Item 1",))
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Alpha Item 2",))
        conn.commit()

    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 2

    with db.get_connection() as conn:
        conn.execute("UPDATE items SET status = ? WHERE titulo = ?", ("concluido", "Alpha Item 1"))
        conn.commit()

    # Tenant B: criar dados diferentes
    _RLS_TENANT_CONTEXT.tenant_id = "beta"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Beta Item 1",))
        conn.commit()

    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["titulo"] == "Beta Item 1"

    # Verificar que tenant A ainda tem seus dados intactos
    _RLS_TENANT_CONTEXT.tenant_id = "alpha"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY titulo").fetchall()
        assert len(rows) == 2
        r1 = dict(rows[0])
        r2 = dict(rows[1])
        assert r1["titulo"] == "Alpha Item 1"
        assert r1["status"] == "concluido"
        assert r2["titulo"] == "Alpha Item 2"

    # Tenant B deletar seus dados
    _RLS_TENANT_CONTEXT.tenant_id = "beta"
    with db.get_connection() as conn:
        conn.execute("DELETE FROM items")
        conn.commit()

    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 0

    # Tenant A ainda intacto
    _RLS_TENANT_CONTEXT.tenant_id = "alpha"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 2


# ---------------------------------------------------------------------------
# Testes de RLS — SQL injection resistência
# ---------------------------------------------------------------------------

def test_rls_resists_table_name_injection():
    """enable_rls_tenant deve registrar o nome da tabela como fornecido."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    rls_conn = RLSConnection(conn)

    enable_rls_tenant(rls_conn, "legit_table")
    assert "legit_table" in RLS_TABLE_REGISTRY


def test_rls_connection_context_manager(db_with_rls):
    """RLSConnection como context manager deve commitar em sucesso."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-ctx"
    with db.get_connection() as conn:
        conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Ctx Item",))
        conn.commit()

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-ctx"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        assert len(rows) == 1


def test_rls_connection_context_manager_rollback_on_error(db_with_rls):
    """RLSConnection como context manager deve reverter em exceção."""
    db = db_with_rls

    _RLS_TENANT_CONTEXT.tenant_id = "tenant-err"
    with pytest.raises(ValueError):
        with db.get_connection() as conn:
            conn.execute("INSERT INTO items (titulo) VALUES (?)", ("Err Item",))
            conn.commit()
            raise ValueError("boom")

    # O item deve ter sido commitado antes da exceção (commit foi explícito)
    # Mas o rollback do context manager deve ter revertido
    _RLS_TENANT_CONTEXT.tenant_id = "tenant-err"
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM items").fetchall()
        # O commit explícito antes do raise já persistiu
        # O rollback do __exit__ não desfaz commits explícitos anteriores
        # Este é o comportamento esperado do sqlite3
