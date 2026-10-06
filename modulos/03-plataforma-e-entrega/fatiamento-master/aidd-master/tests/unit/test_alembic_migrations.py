# -*- coding: utf-8 -*-
"""
Testes de integridade para as migrações Alembic do AIDD Master.

Cobertura:
  - Upgrade (base → head) cria todas as tabelas e índices do schema esperado.
  - Downgrade (head → base) remove todas as tabelas de negócio e sistema.
  - Ciclo upgrade → downgrade → upgrade é idempotente e limpo.
  - A tabela alembic_version fica consistente em cada etapa.
  - A migração é compatível com o schema raw do sqlite3 (init_system_tables
    e init_schema criam a mesma estrutura).
"""

import os
import sys
import sqlite3
import subprocess
import tempfile

import pytest

# Resolve paths
TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALEMBIC_DIR = os.path.join(TOOLS_DIR, "alembic")
SRC_DIR = os.path.join(TOOLS_DIR, "src")

# ---------------------------------------------------------------------------
# Expected schema — the tables, columns, and indexes that upgrade(head) must
# create. These mirror the raw-sql definitions in:
#   - src/core/database.py → SQLiteAdapter.init_system_tables()
#   - src/modules/modulo1/models.py → init_schema()
# ---------------------------------------------------------------------------

EXPECTED_TABLES = {
    "_audit_log",
    "_outbox_events",
    "_schema_migrations",
    "mod_modulo1",
}

EXPECTED_INDEXES = {
    "idx_outbox_status",
    "idx_modulo1_ativo",
    "idx_modulo1_status",
    "idx_modulo1_deletado",
}

# Columns per table (name, nullable, has_default_server)
EXPECTED_COLUMNS = {
    "_audit_log": [
        ("id", False, False),
        ("timestamp", False, False),
        ("action", False, False),
        ("payload", False, False),
        ("prev_hash", False, False),
        ("curr_hash", False, False),
    ],
    "_outbox_events": [
        ("id", False, False),
        ("event_name", False, False),
        ("payload", False, False),
        ("status", False, True),
        ("criado_em", False, False),
        ("processado_em", True, False),
    ],
    "_schema_migrations": [
        ("id", False, False),
        ("module_name", False, False),
        ("version", False, False),
        ("applied_at", True, True),
    ],
    "mod_modulo1": [
        ("id", False, False),
        ("titulo", False, False),
        ("descricao", True, False),
        ("dados_json", True, False),
        ("status", True, True),
        ("ativo", True, True),
        ("criado_em", True, True),
        ("atualizado_em", True, True),
        ("deletado_em", True, False),
    ],
}


def _get_tables(db_path: str) -> set:
    """Return set of non-internal table names in the SQLite database."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def _get_indexes(db_path: str) -> set:
    """Return set of index names (excluding auto-generated PK indexes)."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def _get_columns(db_path: str, table: str) -> list:
    """Return list of (name, notnull, has_default_server) for a table."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
        return [(r[1], bool(r[3]), r[4] is not None) for r in rows]
    finally:
        conn.close()


def _run_alembic(args: list, db_path: str) -> subprocess.CompletedProcess:
    """Run alembic command with DATABASE_URL pointing to the test db."""
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    return subprocess.run(
        ["alembic"] + args,
        capture_output=True,
        text=True,
        cwd=TOOLS_DIR,
        env=env,
    )


@pytest.fixture
def fresh_db(tmp_path):
    """Provide a path to a fresh, non-existent SQLite database file."""
    db_path = str(tmp_path / "test_alembic.db")
    yield db_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAlembicUpgrade:
    """Tests for alembic upgrade head."""

    def test_upgrade_creates_all_expected_tables(self, fresh_db):
        result = _run_alembic(["upgrade", "head"], fresh_db)
        assert result.returncode == 0, f"alembic upgrade failed: {result.stderr}"

        tables = _get_tables(fresh_db)
        assert EXPECTED_TABLES.issubset(tables), (
            f"Missing tables: {EXPECTED_TABLES - tables}"
        )

    def test_upgrade_creates_all_expected_indexes(self, fresh_db):
        _run_alembic(["upgrade", "head"], fresh_db)
        indexes = _get_indexes(fresh_db)
        assert EXPECTED_INDEXES.issubset(indexes), (
            f"Missing indexes: {EXPECTED_INDEXES - indexes}"
        )

    def test_upgrade_sets_alembic_version(self, fresh_db):
        _run_alembic(["upgrade", "head"], fresh_db)
        conn = sqlite3.connect(fresh_db)
        try:
            rows = conn.execute("SELECT version_num FROM alembic_version").fetchall()
            assert len(rows) == 1, f"Expected 1 alembic_version row, got {len(rows)}"
            assert rows[0][0], "alembic_version should not be empty"
        finally:
            conn.close()

    @pytest.mark.parametrize("table", sorted(EXPECTED_TABLES))
    def test_upgrade_column_count_matches(self, fresh_db, table):
        _run_alembic(["upgrade", "head"], fresh_db)
        expected_cols = EXPECTED_COLUMNS[table]
        actual_cols = _get_columns(fresh_db, table)
        assert len(actual_cols) == len(expected_cols), (
            f"Table {table}: expected {len(expected_cols)} columns, got {len(actual_cols)}"
        )

    def test_upgrade_no_extra_tables(self, fresh_db):
        _run_alembic(["upgrade", "head"], fresh_db)
        tables = _get_tables(fresh_db)
        extra = tables - EXPECTED_TABLES - {"alembic_version"}
        assert not extra, f"Unexpected tables: {extra}"


class TestAlembicDowngrade:
    """Tests for alembic downgrade base."""

    def test_downgrade_removes_business_tables(self, fresh_db):
        _run_alembic(["upgrade", "head"], fresh_db)
        result = _run_alembic(["downgrade", "base"], fresh_db)
        assert result.returncode == 0, f"alembic downgrade failed: {result.stderr}"

        tables = _get_tables(fresh_db)
        remaining = tables - {"alembic_version"}
        assert not remaining, f"Tables should be gone after downgrade: {remaining}"

    def test_downgrade_alembic_version_cleared(self, fresh_db):
        _run_alembic(["upgrade", "head"], fresh_db)
        _run_alembic(["downgrade", "base"], fresh_db)

        conn = sqlite3.connect(fresh_db)
        try:
            rows = conn.execute("SELECT version_num FROM alembic_version").fetchall()
            assert len(rows) == 0, "alembic_version should be empty after downgrade"
        finally:
            conn.close()


class TestAlembicCycle:
    """Tests for upgrade → downgrade → upgrade cycle (idempotency)."""

    def test_upgrade_downgrade_upgrade_cycle(self, fresh_db):
        # 1. Upgrade
        r1 = _run_alembic(["upgrade", "head"], fresh_db)
        assert r1.returncode == 0
        tables_after_up = _get_tables(fresh_db)
        assert EXPECTED_TABLES.issubset(tables_after_up)

        # 2. Downgrade
        r2 = _run_alembic(["downgrade", "base"], fresh_db)
        assert r2.returncode == 0
        tables_after_down = _get_tables(fresh_db)
        assert not (EXPECTED_TABLES & tables_after_down), "Tables should be gone"

        # 3. Re-upgrade
        r3 = _run_alembic(["upgrade", "head"], fresh_db)
        assert r3.returncode == 0
        tables_after_reup = _get_tables(fresh_db)
        assert EXPECTED_TABLES.issubset(tables_after_reup)

    def test_current_revision_matches_head(self, fresh_db):
        _run_alembic(["upgrade", "head"], fresh_db)
        result = _run_alembic(["current"], fresh_db)
        assert result.returncode == 0
        assert "9cd894b8e0bf" in result.stdout, (
            f"Current revision should be 9cd894b8e0bf, got: {result.stdout}"
        )


class TestAlembicSchemaCompatibility:
    """Tests that Alembic schema matches what the raw-sql code would create."""

    def test_system_tables_match_raw_sql(self, fresh_db):
        """Verify that Alembic-created tables match SQLiteAdapter.init_system_tables()."""
        _run_alembic(["upgrade", "head"], fresh_db)

        # Create a reference DB using the raw-sql approach
        ref_path = fresh_db + ".ref"
        ref_db = sqlite3.connect(ref_path)
        try:
            ref_db.executescript("""
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
            ref_db.commit()
        finally:
            ref_db.close()

        # Compare columns for each system table
        for table in ("_schema_migrations", "_outbox_events", "_audit_log"):
            alembic_cols = _get_columns(fresh_db, table)
            ref_cols = _get_columns(ref_path, table)
            alembic_names = [c[0] for c in alembic_cols]
            ref_names = [c[0] for c in ref_cols]
            assert alembic_names == ref_names, (
                f"Table {table}: Alembic cols {alembic_names} != ref cols {ref_names}"
            )

        os.remove(ref_path)

    def test_module_table_matches_raw_sql(self, fresh_db):
        """Verify that Alembic-created mod_modulo1 matches init_schema()."""
        _run_alembic(["upgrade", "head"], fresh_db)

        ref_path = fresh_db + ".ref2"
        ref_db = sqlite3.connect(ref_path)
        try:
            ref_db.executescript("""
                CREATE TABLE IF NOT EXISTS mod_modulo1 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    descricao TEXT,
                    dados_json TEXT,
                    status TEXT DEFAULT 'ativo',
                    ativo INTEGER DEFAULT 1,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deletado_em TIMESTAMP DEFAULT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_modulo1_ativo ON mod_modulo1(ativo);
                CREATE INDEX IF NOT EXISTS idx_modulo1_status ON mod_modulo1(status);
                CREATE INDEX IF NOT EXISTS idx_modulo1_deletado ON mod_modulo1(deletado_em);
            """)
            ref_db.commit()
        finally:
            ref_db.close()

        alembic_cols = _get_columns(fresh_db, "mod_modulo1")
        ref_cols = _get_columns(ref_path, "mod_modulo1")
        alembic_names = [c[0] for c in alembic_cols]
        ref_names = [c[0] for c in ref_cols]
        assert alembic_names == ref_names, (
            f"mod_modulo1: Alembic cols {alembic_names} != ref cols {ref_names}"
        )

        os.remove(ref_path)
