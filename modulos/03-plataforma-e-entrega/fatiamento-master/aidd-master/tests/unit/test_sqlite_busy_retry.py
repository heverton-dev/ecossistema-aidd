# -*- coding: utf-8 -*-
"""
Testes REAIS (sem mocks, sem stubs) do retry exponencial SQLITE_BUSY
(PLAN-0017, item retry-backoff-sqlite).

Cobre:
  1. Facade: lock externo (sqlite3 cru) liberado em thread -> retry real com
     sucesso e contador `_lock_retries >= 1`.
  2. Facade: lock externo preso -> os SQLITE_BUSY_MAX_ATTEMPTS retries esgotam
     e o `sqlite3.OperationalError` sobe cru, reconhecido por is_db_locked().
  3. Facade: OperationalError que NÃO é "database is locked" NÃO é retentado.
  4. is_db_locked(): unwrapped, wrapped via orig, tabela locked e casos falsos.
  5. Backoff exponencial monotônico com teto (50ms -> 2s).
  6. Pool: engine criado com pool_pre_ping=True (validado no pool real).
  7. Result.fail(codigo='DB_LOCKED') serializa com a estrutura esperada
     pela fronteira HTTP (sucesso=False, codigo, detalhes.retry_after_segundos).

O mapeamento HTTP completo (503 + Retry-After via servidor real em subprocess)
vive em tests/integration/test_sqlite_busy_http_503.py.
"""

import os
import sqlite3
import sys
import tempfile
import threading
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from core.database import (
    EngineFacadeConnection,
    SQLITE_BUSY_DELAY_S,
    SQLITE_BUSY_MAX_ATTEMPTS,
    SQLITE_BUSY_MAX_DELAY_S,
    _create_sqlite_engine,
    _sqlite_busy_backoff,
    is_db_locked,
)


@pytest.fixture
def db_file():
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "retry_test.db")
    engine = _create_sqlite_engine(path)
    engine.connect().close()
    yield engine, path
    engine.dispose()


@pytest.fixture
def facade(db_file):
    engine, _ = db_file
    conn = EngineFacadeConnection(engine.connect())
    conn.execute("CREATE TABLE IF NOT EXISTS _busy_test (id INTEGER PRIMARY KEY, v TEXT)")
    conn.execute("PRAGMA busy_timeout=50")
    yield conn
    try:
        conn.close()
    except Exception:
        pass


class TestRetrySQLITE_BUSY:

    def test_retry_succeeds_quando_lock_liberado_por_thread(self, facade, db_file):
        _, db_path = db_file
        ext = sqlite3.connect(db_path, check_same_thread=False)
        ext.execute("BEGIN IMMEDIATE")
        ext.execute("INSERT INTO _busy_test (v) VALUES ('externo')")

        def liberar():
            time.sleep(0.4)
            ext.commit()
            ext.close()

        th = threading.Thread(target=liberar)
        th.start()
        t0 = time.time()
        facade.execute("INSERT INTO _busy_test (v) VALUES ('fachada')")
        facade.commit()
        th.join()
        duracao = time.time() - t0

        assert facade._lock_retries >= 1, (
            f"Deveria registrar retry real; contador={facade._lock_retries}"
        )
        assert duracao < 3.0, f"Retry deveria ser rápido; levou {duracao:.2f}s"
        row = facade.execute("SELECT v FROM _busy_test WHERE v='fachada'").fetchone()
        assert row is not None and row["v"] == "fachada"

    def test_retries_esgotam_e_excecao_crua_sobe(self, facade, db_file):
        _, db_path = db_file
        ext = sqlite3.connect(db_path, check_same_thread=False)
        ext.execute("BEGIN IMMEDIATE")
        ext.execute("INSERT INTO _busy_test (v) VALUES ('externo2')")
        try:
            with pytest.raises(sqlite3.OperationalError) as exc_info:
                facade.execute("INSERT INTO _busy_test (v) VALUES ('esgota')")
            assert is_db_locked(exc_info.value)
            assert facade._lock_retries == SQLITE_BUSY_MAX_ATTEMPTS
        finally:
            ext.rollback()
            ext.close()

    def test_ja_committed_e_relock_libera_mas_insere_fora(self, facade, db_file):
        """Garante que rollback do lock externo deixa a fachada escrever depois."""
        _, db_path = db_file
        ext = sqlite3.connect(db_path, check_same_thread=False)
        ext.execute("BEGIN IMMEDIATE")
        ext.execute("INSERT INTO _busy_test (v) VALUES ('temp')")
        ext.commit()
        ext.close()
        facade.execute("INSERT INTO _busy_test (v) VALUES ('pos-lock')")
        facade.commit()
        row = facade.execute("SELECT v FROM _busy_test WHERE v='pos-lock'").fetchone()
        assert row is not None


class TestRetryOutrosErrosNaoRetenta:

    def test_erro_nao_locked_propaga_sem_retry(self, facade):
        facade._lock_retries = 0
        with pytest.raises(sqlite3.OperationalError, match="no such table"):
            facade.execute("SELECT * FROM tabela_que_nao_existe_42")
        assert facade._lock_retries == 0


class TestIsDbLocked:

    def test_unwrapped_busy(self):
        assert is_db_locked(sqlite3.OperationalError("database is locked"))

    def test_unwrapped_table_locked(self):
        assert is_db_locked(sqlite3.OperationalError("database table is locked"))

    def test_wrapped_via_orig(self):
        class FakeExc(Exception):
            def __init__(self):
                self.orig = sqlite3.OperationalError("database is locked")

        assert is_db_locked(FakeExc())

    def test_nao_locked_outro_operational(self):
        assert not is_db_locked(sqlite3.OperationalError("no such table: x"))

    def test_nao_locked_runtime(self):
        assert not is_db_locked(RuntimeError("qualquer"))


class TestBackoff:

    def test_monotonico_e_limitado(self):
        valores = [_sqlite_busy_backoff(i) for i in range(SQLITE_BUSY_MAX_ATTEMPTS)]
        assert valores[0] == pytest.approx(SQLITE_BUSY_DELAY_S)
        for i in range(1, len(valores)):
            assert valores[i] >= valores[i - 1]
        assert valores[-1] <= SQLITE_BUSY_MAX_DELAY_S


class TestPoolPrePing:

    def test_pool_pre_ping_ligado(self, db_file):
        engine, _ = db_file
        assert engine.pool._pre_ping is True


class TestResultDbLockedShape:

    def test_to_dict_carrega_codigo_e_retry_after(self):
        from core.result import Result

        resultado = Result.fail(
            "Banco de dados temporariamente bloqueado por outra conexão (SQLITE_BUSY).",
            codigo="DB_LOCKED",
            detalhes={"retry_after_segundos": 2},
        ).to_dict()
        assert resultado["sucesso"] is False
        assert resultado["codigo"] == "DB_LOCKED"
        assert resultado["detalhes"]["retry_after_segundos"] == 2