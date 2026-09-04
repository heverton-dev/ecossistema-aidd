# -*- coding: utf-8 -*-
"""
Testes do DatabaseAdapter (Onda 1 / v5.0-Alpha): SQLite real de ponta a ponta,
e a lógica de tradução/emulação do PostgresConnectionProxy validada com um
duplo de teste (fake connection/cursor) — sem exigir um servidor Postgres real.

Um teste de integração real via container Docker (postgres:16) roda apenas se
o daemon Docker estiver disponível; caso contrário é pulado (skip) com motivo
explícito, nunca falha o gate por ausência de infraestrutura.
"""

import os
import sys
import json
import shutil
import socket
import sqlite3
import subprocess
import time

import pytest

TEMPLATES_V2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates", "v2"))
if TEMPLATES_V2 not in sys.path:
    sys.path.insert(0, TEMPLATES_V2)

from database import (  # noqa: E402
    Database,
    PostgresConnectionProxy,
    PostgresCursorProxy,
    _translate_ddl_for_postgres,
)


# ---------------------------------------------------------------------------
# Duplos de teste (fakes) para validar a lógica do proxy sem psycopg2/Postgres
# ---------------------------------------------------------------------------

class _FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.executed = []
        self._fetchone_result = fetchone_result
        self._fetchall_result = fetchall_result if fetchall_result is not None else []
        self.rowcount = 1

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def executemany(self, query, seq_of_params):
        self.executed.append((query, list(seq_of_params)))

    def fetchone(self):
        return self._fetchone_result

    def fetchall(self):
        return self._fetchall_result


class _FakeConnection:
    def __init__(self, cursor_factory=None):
        self._cursor_factory = cursor_factory or (lambda: _FakeCursor())
        self.cursors_created = []
        self.committed = False
        self.rolledback = False
        self.closed = False

    def cursor(self):
        c = self._cursor_factory()
        self.cursors_created.append(c)
        return c

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolledback = True

    def close(self):
        self.closed = True


# ---------------------------------------------------------------------------
# PostgresCursorProxy: tradução de placeholders e emulação de lastrowid
# ---------------------------------------------------------------------------

def test_cursor_proxy_translates_select_placeholders():
    fake = _FakeCursor(fetchall_result=[{"id": 1, "titulo": "a"}])
    proxy = PostgresCursorProxy(fake)

    proxy.execute("SELECT * FROM mod_x WHERE a = ? AND b = ?", (1, 2))

    query, params = fake.executed[0]
    assert query == "SELECT * FROM mod_x WHERE a = %s AND b = %s"
    assert params == (1, 2)
    assert proxy.fetchall() == [{"id": 1, "titulo": "a"}]


def test_cursor_proxy_emulates_lastrowid_on_insert():
    fake = _FakeCursor(fetchone_result={"id": 42})
    proxy = PostgresCursorProxy(fake)

    proxy.execute("INSERT INTO mod_x (titulo) VALUES (?)", ("abc",))

    query, params = fake.executed[0]
    assert query == "INSERT INTO mod_x (titulo) VALUES (%s) RETURNING id"
    assert params == ("abc",)
    assert proxy.lastrowid == 42


def test_cursor_proxy_respects_existing_returning_clause():
    fake = _FakeCursor(fetchone_result={"id": 7})
    proxy = PostgresCursorProxy(fake)

    proxy.execute("INSERT INTO mod_x (titulo) VALUES (?) RETURNING id", ("abc",))

    query, _ = fake.executed[0]
    assert query.count("RETURNING") == 1
    assert proxy.lastrowid == 7


def test_cursor_proxy_does_not_emulate_lastrowid_for_update():
    fake = _FakeCursor(fetchall_result=[])
    proxy = PostgresCursorProxy(fake)

    proxy.execute("UPDATE mod_x SET titulo = ? WHERE id = ?", ("novo", 1))

    query, _ = fake.executed[0]
    assert "RETURNING" not in query
    assert proxy.lastrowid is None


# ---------------------------------------------------------------------------
# Tradutor de DDL SQLite -> PostgreSQL
# ---------------------------------------------------------------------------

def test_translate_ddl_autoincrement_to_serial():
    sql = "CREATE TABLE mod_x (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT)"
    translated = _translate_ddl_for_postgres(sql)
    assert "SERIAL PRIMARY KEY" in translated
    assert "AUTOINCREMENT" not in translated


# ---------------------------------------------------------------------------
# PostgresConnectionProxy: execute/executemany/executescript/context manager
# ---------------------------------------------------------------------------

def test_connection_proxy_execute_creates_cursor_and_returns_proxy():
    conn = _FakeConnection()
    proxy = PostgresConnectionProxy(conn)

    result = proxy.execute("SELECT * FROM mod_x WHERE a = ?", (1,))

    assert isinstance(result, PostgresCursorProxy)
    assert len(conn.cursors_created) == 1


def test_connection_proxy_executemany_translates_placeholders():
    conn = _FakeConnection()
    proxy = PostgresConnectionProxy(conn)

    proxy.executemany("INSERT INTO mod_x (titulo) VALUES (?)", [("a",), ("b",)])

    query, params = conn.cursors_created[0].executed[0]
    assert query == "INSERT INTO mod_x (titulo) VALUES (%s)"
    assert params == [("a",), ("b",)]


def test_connection_proxy_executescript_translates_ddl():
    conn = _FakeConnection()
    proxy = PostgresConnectionProxy(conn)

    proxy.executescript("CREATE TABLE mod_x (id INTEGER PRIMARY KEY AUTOINCREMENT);")

    query, _ = conn.cursors_created[0].executed[0]
    assert "SERIAL PRIMARY KEY" in query


def test_connection_proxy_context_manager_commits_on_success():
    conn = _FakeConnection()
    with PostgresConnectionProxy(conn) as c:
        assert c is not None
    assert conn.committed is True
    assert conn.rolledback is False


def test_connection_proxy_context_manager_rolls_back_on_exception():
    conn = _FakeConnection()
    with pytest.raises(ValueError):
        with PostgresConnectionProxy(conn):
            raise ValueError("boom")
    assert conn.rolledback is True
    assert conn.committed is False


# ---------------------------------------------------------------------------
# Database (SQLite) — ponta a ponta real, sem fakes
# ---------------------------------------------------------------------------

def test_sqlite_system_tables_created_on_init(tmp_path):
    db_file = tmp_path / "t_init.db"
    Database(f"sqlite:///{db_file}")

    conn = sqlite3.connect(str(db_file))
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()

    assert "_schema_migrations" in tables
    assert "_outbox_events" in tables


def test_sqlite_crud_and_outbox_same_transaction(tmp_path):
    db_file = tmp_path / "t_crud.db"
    db = Database(f"sqlite:///{db_file}")

    with db.get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS mod_teste (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL
            );
        """)
        cur = conn.execute("INSERT INTO mod_teste (titulo) VALUES (?)", ("Item 1",))
        novo_id = cur.lastrowid
        assert novo_id == 1

        event_id = db.enqueue_outbox_event(conn, "teste_criado", {"id": novo_id, "titulo": "Item 1"})
        conn.commit()

    assert event_id

    with db.get_connection() as conn:
        row = dict(conn.execute("SELECT * FROM mod_teste WHERE id = ?", (novo_id,)).fetchone())
        assert row["titulo"] == "Item 1"

        outbox_row = dict(conn.execute("SELECT * FROM _outbox_events WHERE id = ?", (event_id,)).fetchone())
        assert outbox_row["status"] == "pendente"
        assert json.loads(outbox_row["payload"])["titulo"] == "Item 1"


def test_sqlite_record_migration_is_idempotent(tmp_path):
    db_file = tmp_path / "t_mig.db"
    db = Database(f"sqlite:///{db_file}")

    db.record_migration("modulo_teste", 1)
    db.record_migration("modulo_teste", 2)  # deve atualizar, não duplicar (ON CONFLICT)

    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM _schema_migrations WHERE module_name = ?", ("modulo_teste",)).fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["version"] == 2


# ---------------------------------------------------------------------------
# Integração real opcional com PostgreSQL via Docker (skip se indisponível)
# ---------------------------------------------------------------------------

def _docker_daemon_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.skipif(not _docker_daemon_available(), reason="Docker daemon indisponível neste ambiente")
def test_postgres_adapter_real_integration_via_docker():
    port = _find_free_port()
    container_name = f"aidd-v5-pgtest-{port}"
    run_cmd = [
        "docker", "run", "--rm", "-d",
        "--name", container_name,
        "-e", "POSTGRES_PASSWORD=test",
        "-e", "POSTGRES_USER=test",
        "-e", "POSTGRES_DB=test_db",
        "-p", f"{port}:5432",
        "postgres:16",
    ]
    started = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
    if started.returncode != 0:
        pytest.skip(f"Não foi possível iniciar container postgres:16: {started.stderr.strip()}")

    try:
        db_url = f"postgresql://test:test@127.0.0.1:{port}/test_db"
        deadline = time.time() + 30
        last_error = None
        db = None
        while time.time() < deadline:
            try:
                db = Database(db_url)
                break
            except Exception as e:
                last_error = e
                time.sleep(1)
        if db is None:
            pytest.skip(f"Postgres não ficou pronto a tempo: {last_error}")

        with db.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS mod_teste (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL
                );
            """)
            cur = conn.execute("INSERT INTO mod_teste (titulo) VALUES (?)", ("Item Postgres",))
            novo_id = cur.lastrowid
            assert novo_id is not None
            event_id = db.enqueue_outbox_event(conn, "teste_criado", {"id": novo_id})
            conn.commit()

        with db.get_connection() as conn:
            row = dict(conn.execute("SELECT * FROM mod_teste WHERE id = ?", (novo_id,)).fetchone())
            assert row["titulo"] == "Item Postgres"
            outbox_row = dict(conn.execute("SELECT * FROM _outbox_events WHERE id = ?", (event_id,)).fetchone())
            assert outbox_row["status"] == "pendente"
    finally:
        subprocess.run(["docker", "stop", container_name], capture_output=True, timeout=30)
