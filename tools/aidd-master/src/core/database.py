# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.0-Alpha — Camada de Persistência Poliglota (DatabaseAdapter Bridge)
=============================================================================
Database é uma fachada fina que delega para um DatabaseAdapter (SQLite ou
PostgreSQL) escolhido a partir de DATABASE_URL. A API pública usada pelo
código gerado (get_connection, record_migration, enqueue_outbox_event)
permanece idêntica independente do motor escolhido: os módulos gerados por
add_module.py continuam usando `?` como placeholder, `cur.lastrowid` e linhas
sqlite3.Row (dict(row)) sem nenhuma alteração, mesmo rodando contra PostgreSQL.

Desde a troca de motor NIH #8 (Fase 2), o motor SQLite é gerenciado pelo
SQLAlchemy: o Engine cuida de pooling, ciclo de vida da conexão e de aplicar o
modo WAL (journal_mode=WAL) e os demais PRAGMAs via event listener de
"connect". O código gerado vê apenas a fachada legada (EngineFacadeConnection),
que preserva a superfície de cursor do sqlite3 por cima da conexão gerenciada
pelo SQLAlchemy.
"""

import os
import re
import json
import uuid
import sqlite3
import datetime
import hashlib
import threading
import time
from abc import ABC, abstractmethod

import sqlglot
from sqlglot import exp
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# psycopg2 é opcional: só é usado quando DATABASE_URL aponta para PostgreSQL
# (ver PostgresAdapter._connect_raw abaixo, mesmo padrão de import condicional).
# Carregado aqui também para expor DB_ERRORS — a tupla de exceções nativas de
# banco que o resto do módulo (e outros arquivos de core/) usa para não
# capturar erro genérico, sem arriscar quebrar instalações só-SQLite.
try:
    import psycopg2
except ImportError:
    psycopg2 = None

DB_ERRORS = (sqlite3.Error, psycopg2.Error) if psycopg2 is not None else (sqlite3.Error,)

# ---------------------------------------------------------------------------
# SQLITE_BUSY — Retry com Backoff Exponencial (PLAN-0017, item retry-backoff-sqlite)
# ---------------------------------------------------------------------------
# SQLite (WAL) tem um único escritor por vez. Sob concorrência real — migração
# de schema no boot, worktrees paralelos, gravações simultâneas — o
# busy_timeout do driver pode estourar e subir
# `sqlite3.OperationalError: database is locked`. Em vez de falhar a
# requisição, `EngineFacadeConnection` reexecuta apenas ESSA exceção com
# espera exponencial (50ms -> 2s, 5 tentativas). Qualquer outro
# OperationalError (ex.: "no such table") continua subindo cru, sem retry.

SQLITE_BUSY_MAX_ATTEMPTS = 5
SQLITE_BUSY_DELAY_S = 0.05          # 50ms — espera da primeira tentativa
SQLITE_BUSY_MAX_DELAY_S = 2.0       # teto de 2s por espera individual
SQLITE_BUSY_CONNECT_TIMEOUT_S = 10.0  # timeout de checkout/connect do pool
SQLITE_BUSY_PRAGMA_TIMEOUT_MS = 5000  # busy_timeout aplicado no listener


def is_db_locked(exc: BaseException) -> bool:
    """True apenas para SQLITE_BUSY real: ``sqlite3.OperationalError`` com a
    mensagem canônica "database is locked" (ou a variante antiga "database
    table is locked"). Também reconhece o erro EMbrulhado por SQLAlchemy
    (``exc.orig``), para a mesma decisão ser tomada na fronteira HTTP."""
    candidatos = [exc]
    orig = getattr(exc, "orig", None)
    if orig is not None:
        candidatos.append(orig)
    for cand in candidatos:
        if isinstance(cand, sqlite3.OperationalError):
            msg = str(cand).lower()
            if "database is locked" in msg or "database table is locked" in msg:
                return True
    return False


def _sqlite_busy_backoff(tentativa: int) -> float:
    """Espera exponencial para a tentativa N (0-based): 50ms, 100ms, 200ms,
    400ms, 800ms... com teto de 2s."""
    return min(SQLITE_BUSY_DELAY_S * (2 ** tentativa), SQLITE_BUSY_MAX_DELAY_S)

# ---------------------------------------------------------------------------
# Row Level Security (RLS) — Application-Layer Enforcement for SQLite
# ---------------------------------------------------------------------------
# PostgreSQL uses native RLS policies (ALTER TABLE ENABLE ROW LEVEL SECURITY).
# SQLite has no native RLS, so we enforce it at the application layer via
# RLSConnection: a transparent wrapper that intercepts DML and injects
# tenant_id filters automatically.
# ---------------------------------------------------------------------------

RLS_TABLE_REGISTRY: set = set()
_RLS_TENANT_CONTEXT = threading.local()


def _get_current_tenant() -> str | None:
    return getattr(_RLS_TENANT_CONTEXT, 'tenant_id', None)


def _strip_sql_comments(sql: str) -> str:
    """Remove SQL line comments (-- ...) for reliable keyword detection."""
    return re.sub(r'--[^\n]*', '', sql)


def _parse_sql(sql: str):
    """Parse SQL com sqlglot (dialeto SQLite). Retorna a AST ou None se ilegivel."""
    try:
        return sqlglot.parse_one(sql, read="sqlite")
    except sqlglot.errors.SqlglotError:
        return None


def _create_sqlite_engine(db_path: str):
    """Cria um Engine SQLAlchemy (pysqlite) com WAL e ajustes de concorrência
    aplicados via event listener de conexão (NIH #8).

Substitui o gerenciamento manual de ``sqlite3.connect()`` + PRAGMAs soltos
    que existia antes: o SQLAlchemy passa a ser o dono do pooling, do ciclo de
    vida das conexões e da configuração WAL (journal_mode, synchronous,
    busy_timeout, foreign_keys) — sempre que uma conexão nova do pool nasce,
    o listener abaixo a configura antes do primeiro uso.

    Pool explícito (PLAN-0017): file-based SQLite já usa QueuePool por padrão,
    mas agora ele é explícito (pool_size=5, max_overflow=10) com
    ``pool_pre_ping=True`` — conexões mortas/esgotadas do keep-alive são
    descartadas antes do checkout em vez de propagar erro. O timeout de
    connect (busy ao abrir o arquivo) e de checkout do pool é controlado por
    ``SQLITE_BUSY_CONNECT_TIMEOUT_S``.
    """
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={
            "timeout": SQLITE_BUSY_CONNECT_TIMEOUT_S,
            "check_same_thread": False,
        },
        pool_pre_ping=True,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=SQLITE_BUSY_CONNECT_TIMEOUT_S,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_PRAGMA_TIMEOUT_MS};")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    return engine


class EngineFacadeConnection:
    """Bridge entre a superfície legada do sqlite3 e uma conexão gerenciada
    pelo SQLAlchemy Engine (NIH #8).

    O código gerado (e ``RLSConnection``) espera uma conexão com
    ``execute/executemany/executescript/cursor/commit/rollback`` e linhas
    ``sqlite3.Row`` (acesso por nome e ``dict(row)``). Esta classe entrega essa
    superfície executando contra a conexão DBAPI real que o SQLAlchemy já
    configurou (WAL via listener de connect), mas ``close()`` apenas devolve a
    conexão ao pool do Engine — nunca fecha o arquivo do banco.

    Retry SQLITE_BUSY (PLAN-0017): os métodos de escrita/commit/rollback são
    definidos de forma EXPLÍCITA — e não passando por ``__getattr__`` — para
    que todo acesso ao driver (``execute``, ``executemany``, ``executescript``,
    ``commit``, ``rollback``) passe pelo retry exponencial de
    ``sqlite3.OperationalError: database is locked`` antes de entregar o erro
    para a camada de rota. ``_lock_retries`` expõe o contador observável de
    retries executados (usado pelos testes reais, sem mock).
    """

    def __init__(self, sqlalchemy_conn):
        self._sqlalchemy_conn = sqlalchemy_conn
        driver = sqlalchemy_conn.connection.driver_connection
        driver.row_factory = sqlite3.Row
        self._driver = driver
        self._lock_retries = 0

    def __getattr__(self, name):
        return getattr(self._driver, name)

    def _run_com_retry(self, fn, *args, **kwargs):
        """Executa ``fn`` reexecutando-o com backoff exponencial enquanto a
        exceção for SQLITE_BUSY real. Esgota ``SQLITE_BUSY_MAX_ATTEMPTS``
        tentativas e então re-sobe o último ``sqlite3.OperationalError`` cru —
        a fronteira HTTP reconhece (``is_db_locked``) e responde 503."""
        ultimo_erro = None
        for tentativa in range(SQLITE_BUSY_MAX_ATTEMPTS):
            try:
                return fn(*args, **kwargs)
            except sqlite3.OperationalError as exc:
                if not is_db_locked(exc):
                    raise
                self._lock_retries += 1
                ultimo_erro = exc
                if tentativa >= SQLITE_BUSY_MAX_ATTEMPTS - 1:
                    break
                time.sleep(_sqlite_busy_backoff(tentativa))
        if ultimo_erro is not None:
            raise ultimo_erro
        return None  # pragma: no cover — inalcançável, guarda de tipo

    def execute(self, sql, params=None):
        return self._run_com_retry(self._driver.execute, sql, () if params is None else params)

    def executemany(self, sql, seq_of_params):
        return self._run_com_retry(self._driver.executemany, sql, seq_of_params)

    def executescript(self, sql):
        return self._run_com_retry(self._driver.executescript, sql)

    def commit(self):
        return self._run_com_retry(self._driver.commit)

    def rollback(self):
        return self._run_com_retry(self._driver.rollback)

    def close(self):
        self._sqlalchemy_conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()
        return False


class RLSConnection:
    """Transparent wrapper around sqlite3.Connection that enforces tenant
    isolation on all RLS‑enabled tables. SELECT/UPDATE/DELETE are filtered
    by ``tenant_id``; INSERT auto‑injects the current ``tenant_id``.
    Provides a ``cursor()`` method delegating to the underlying connection
    so that existing audit utilities (e.g., ``append_audit_log``) work.
    """

    def __init__(self, real_conn):
        self._conn = real_conn

    # expose cursor for legacy callers
    def cursor(self):
        """Return a cursor from the wrapped ``sqlite3.Connection``.
        Required because some modules (e.g., ``services.py``) call
        ``conn.cursor()`` directly.  Delegating keeps the wrapper transparent.
        """
        return self._conn.cursor()

    # -- query rewriting --------------------------------------------------

    def _rewrite_query(self, sql: str, params: tuple) -> tuple:
        """Rewrite *sql* to enforce tenant isolation on RLS‑enabled tables.
        Returns ``(new_sql, new_params)``. Non‑RLS tables pass through unchanged.
        """
        tenant_id = _get_current_tenant()
        if not tenant_id or not RLS_TABLE_REGISTRY:
            return sql, params

        clean = _strip_sql_comments(sql).strip()
        if not clean:
            return sql, params

        first_word = clean.split()[0].upper()

        # --- INSERT: inject tenant_id into column list and VALUES ---------
        if first_word == 'INSERT':
            return self._rewrite_insert(clean, sql, params, tenant_id)

        # --- SELECT: wrap with tenant filter subquery ---------------------
        if first_word == 'SELECT':
            return self._rewrite_select(clean, sql, params, tenant_id)

        # --- UPDATE: add tenant_id WHERE filter --------------------------
        if first_word == 'UPDATE':
            return self._rewrite_update(clean, sql, params, tenant_id)

        # --- DELETE FROM: add tenant_id WHERE filter ---------------------
        if first_word == 'DELETE':
            return self._rewrite_delete(clean, sql, params, tenant_id)

        return sql, params

    def _rewrite_insert(self, clean: str, original_sql: str, params: tuple, tenant_id: str) -> tuple:
        """Reescreve INSERT via AST sqlglot (parser real), injetando tenant_id como
        primeira coluna/valor. Preserva a ordem de parametros (tenant_id, *params)."""
        ast = _parse_sql(original_sql)
        if ast is None or not isinstance(ast, exp.Insert):
            return original_sql, params
        schema = ast.this
        if not isinstance(schema, exp.Schema):
            return original_sql, params
        table = schema.this.name
        if table not in RLS_TABLE_REGISTRY:
            return original_sql, params
        cols = [c.name for c in schema.expressions]
        if 'tenant_id' in cols:
            return original_sql, params
        values = ast.find(exp.Values)
        if values is None or not values.expressions:
            return original_sql, params

        # Intercala tenant_id na ordem correta dos placeholders (por linha de VALUES)
        row_counts = [len(list(row.find_all(exp.Placeholder))) for row in values.expressions]
        new_params = []
        idx = 0
        for row, n in zip(values.expressions, row_counts):
            row.expressions.insert(0, exp.Placeholder())
            new_params.append(tenant_id)
            new_params.extend(params[idx:idx + n])
            idx += n
        new_params.extend(params[idx:])

        schema.expressions.insert(0, exp.column('tenant_id'))
        return ast.sql(dialect='sqlite'), tuple(new_params)

    def _rewrite_select(self, clean: str, original_sql: str, params: tuple, tenant_id: str) -> tuple:
        """Reescreve SELECT via AST sqlglot (parser real), injetando WHERE tenant_id = ?
        antes de qualquer condicao/ordenacao existente. Parametros: (tenant_id, *params)."""
        ast = _parse_sql(original_sql)
        if ast is None or not isinstance(ast, exp.Select):
            return original_sql, params
        from_node = ast.find(exp.From)
        if from_node is None or not isinstance(from_node.this, exp.Table):
            return original_sql, params
        if from_node.this.name not in RLS_TABLE_REGISTRY:
            return original_sql, params

        cond = exp.column('tenant_id').eq(exp.Placeholder())
        where = ast.args.get('where')
        if where is not None:
            ast.args['where'] = exp.Where(this=exp.and_(cond, where.this))
        else:
            ast.args['where'] = exp.Where(this=cond)
        return ast.sql(dialect='sqlite'), (tenant_id,) + params

    def _rewrite_update(self, clean: str, original_sql: str, params: tuple, tenant_id: str) -> tuple:
        m = re.match(r'UPDATE\s+(\w+)', clean, re.IGNORECASE)
        if not m:
            return original_sql, params
        table = m.group(1)
        if table not in RLS_TABLE_REGISTRY:
            return original_sql, params

        if re.search(r'\bWHERE\b', original_sql, re.IGNORECASE):
            # Insert tenant filter after existing WHERE keyword
            new_sql = re.sub(
                r'\bWHERE\b',
                'WHERE tenant_id = ? AND',
                original_sql,
                count=1,
                flags=re.IGNORECASE
            )
            # params order: original first param (e.g., new values), then tenant_id, then remaining params
            if len(params) >= 1:
                new_params = (params[0], tenant_id) + params[1:]
            else:
                new_params = (tenant_id,)
        else:
            stripped = original_sql.rstrip().rstrip(';')
            new_sql = stripped + ' WHERE tenant_id = ?'
            if original_sql.rstrip().endswith(';'):
                new_sql += ';'
            # Append tenant_id after existing params
            new_params = params + (tenant_id,)

        return new_sql, new_params

    def _rewrite_delete(self, clean: str, original_sql: str, params: tuple, tenant_id: str) -> tuple:
        m = re.match(r'DELETE\s+FROM\s+(\w+)', clean, re.IGNORECASE)
        if not m:
            return original_sql, params
        table = m.group(1)
        if table not in RLS_TABLE_REGISTRY:
            return original_sql, params

        if re.search(r'\bWHERE\b', original_sql, re.IGNORECASE):
            new_sql = re.sub(
                r'\bWHERE\b',
                'WHERE tenant_id = ? AND',
                original_sql,
                count=1,
                flags=re.IGNORECASE
            )
        else:
            stripped = original_sql.rstrip().rstrip(';')
            new_sql = stripped + ' WHERE tenant_id = ?'
            if original_sql.rstrip().endswith(';'):
                new_sql += ';'

        return new_sql, (tenant_id,) + params

    # -- delegate to underlying connection --------------------------------

    def execute(self, sql: str, params=None):
        params = params if params is not None else ()
        new_sql, new_params = self._rewrite_query(sql, params)
        return self._conn.execute(new_sql, new_params)

    def executemany(self, sql: str, seq_of_params):
        tenant_id = _get_current_tenant()
        if tenant_id and RLS_TABLE_REGISTRY:
            ast = _parse_sql(sql)
            if (
                isinstance(ast, exp.Insert)
                and isinstance(ast.this, exp.Schema)
                and ast.this.this.name in RLS_TABLE_REGISTRY
                and 'tenant_id' not in [c.name for c in ast.this.expressions]
            ):
                values = ast.find(exp.Values)
                if values is not None and values.expressions:
                    ast.this.expressions.insert(0, exp.column('tenant_id'))
                    for row in values.expressions:
                        row.expressions.insert(0, exp.Placeholder())
                    sql = ast.sql(dialect='sqlite')
                    seq_of_params = [(tenant_id,) + p for p in seq_of_params]
        return self._conn.executemany(sql, seq_of_params)

    def executescript(self, sql: str):
        return self._conn.executescript(sql)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    @property
    def row_factory(self):
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, value):
        self._conn.row_factory = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._conn.rollback()
        else:
            self._conn.commit()
        return False


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
    """Enable RLS for a table.  On PostgreSQL uses native policies; on SQLite
    registers the table for application-layer enforcement via RLSConnection."""
    if hasattr(cursor, '_cursor') or type(cursor).__name__ == 'PostgresCursorProxy':
        cursor.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
        cursor.execute(f"CREATE POLICY tenant_isolation ON {table_name} USING (tenant_id = current_setting('app.current_tenant_id')::uuid);")
    else:
        RLS_TABLE_REGISTRY.add(table_name)


_UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def set_tenant(cursor, tenant_id: str):
    """Set the active tenant context.  On PostgreSQL uses SET; on SQLite
    stores it in thread-local storage for RLSConnection to pick up."""
    if hasattr(cursor, '_cursor') or type(cursor).__name__ == 'PostgresCursorProxy':
        if not _UUID_RE.match(tenant_id):
            raise ValueError(f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.")
        cursor.execute("SET app.current_tenant_id = %s;", (tenant_id,))
    else:
        _RLS_TENANT_CONTEXT.tenant_id = tenant_id


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
    """Motor local embarcado (Zero Setup). Comportamento idêntico ao pré-v5.0.
    Quando RLS_TABLE_REGISTRY não está vazio, get_connection() retorna um
    RLSConnection que intercepta queries e injeta filtros de tenant_id.

    Desde a troca NIH #8, o pooling e o modo WAL são operados pelo SQLAlchemy
    (ver ``_create_sqlite_engine``); ``get_connection()`` entrega a fachada
    legada (``EngineFacadeConnection``) por cima de uma conexão do Engine."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.db_path = db_url.replace("sqlite:///", "")
        self._engine = _create_sqlite_engine(self.db_path)
        self._session_factory = sessionmaker(self._engine)
        self._async_engine = None

    @property
    def engine(self):
        """Engine SQLAlchemy síncrono (pysqlite) — WAL por event listener."""
        return self._engine

    @property
    def session_factory(self):
        """sessionmaker (ORM SQLAlchemy) ligado ao Engine desta adapter."""
        return self._session_factory

    @property
    def async_engine(self):
        """AsyncEngine SQLAlchemy sobre aiosqlite para o mesmo arquivo.

        Criado sob demanda; WAL já está persistido no arquivo pelo Engine
        síncrono (journal_mode=WAL é persistente). Use ``await
        adapter.init_async()`` uma vez para reafirmar os PRAGMAs no fluxo
        assíncrono."""

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

    def get_connection(self):
        return RLSConnection(EngineFacadeConnection(self._engine.connect()))

    def init_system_tables(self):
        statements = [
            "CREATE TABLE IF NOT EXISTS _schema_migrations ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "module_name TEXT NOT NULL UNIQUE,"
            "version INTEGER NOT NULL,"
            "applied_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            ");",
            "CREATE TABLE IF NOT EXISTS _outbox_events ("
            "id TEXT PRIMARY KEY,"
            "event_name TEXT NOT NULL,"
            "payload TEXT NOT NULL,"
            "status TEXT NOT NULL DEFAULT 'pendente',"
            "criado_em TEXT NOT NULL,"
            "processado_em TEXT,"
            "claimed_at TEXT,"
            "claimed_by TEXT,"
            "tentativas INTEGER NOT NULL DEFAULT 0,"
            "seq INTEGER NOT NULL DEFAULT 0"
            ");",
            "CREATE INDEX IF NOT EXISTS idx_outbox_status ON _outbox_events(status);",
            "CREATE TABLE IF NOT EXISTS _eventos_processados ("
            "event_id TEXT PRIMARY KEY,"
            "seq INTEGER NOT NULL,"
            "event_name TEXT NOT NULL,"
            "consumer_id TEXT NOT NULL DEFAULT 'default',"
            "processado_em TEXT NOT NULL"
            ");",
            "CREATE INDEX IF NOT EXISTS idx_eventos_processados_seq ON _eventos_processados(seq, consumer_id);",
            "CREATE TABLE IF NOT EXISTS _audit_log ("
            "id TEXT PRIMARY KEY,"
            "timestamp TEXT NOT NULL,"
            "action TEXT NOT NULL,"
            "payload TEXT NOT NULL,"
            "prev_hash TEXT NOT NULL,"
            "curr_hash TEXT NOT NULL"
            ");",
        ]
        with self._engine.begin() as conn:
            for stmt in statements:
                conn.exec_driver_sql(stmt)
            # Migração idempotente: bancos criados antes das colunas de claim
            # atômico / retry (tentativas, claimed_at, claimed_by, seq) do
            # OutboxWorker recebem as colunas sem perder dados.
            colunas = conn.exec_driver_sql(
                "PRAGMA table_info(_outbox_events)"
            ).fetchall()
            presentes = {row[1] for row in colunas}
            for nome_coluna, ddl in (
                ("tentativas", "ALTER TABLE _outbox_events ADD COLUMN tentativas INTEGER NOT NULL DEFAULT 0;"),
                ("claimed_at", "ALTER TABLE _outbox_events ADD COLUMN claimed_at TEXT;"),
                ("claimed_by", "ALTER TABLE _outbox_events ADD COLUMN claimed_by TEXT;"),
                ("seq", "ALTER TABLE _outbox_events ADD COLUMN seq INTEGER NOT NULL DEFAULT 0;"),
            ):
                if nome_coluna not in presentes:
                    conn.exec_driver_sql(ddl)
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_outbox_claim ON _outbox_events(status, claimed_at);"
            )


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
            except psycopg2.ProgrammingError:
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
                    processado_em TEXT,
                    claimed_at TEXT,
                    claimed_by TEXT,
                    tentativas INTEGER NOT NULL DEFAULT 0,
                    seq INTEGER NOT NULL DEFAULT 0
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_outbox_status ON _outbox_events(status);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_outbox_claim ON _outbox_events(status, claimed_at);")
            # Migração idempotente: bancos PostgreSQL criados antes das colunas
            # de claim atômico / retry do OutboxWorker recebem as colunas.
            cur.execute("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '_outbox_events' AND column_name = 'tentativas'
                    ) THEN
                        ALTER TABLE _outbox_events ADD COLUMN tentativas INTEGER NOT NULL DEFAULT 0;
                    END IF;
                END $$;
            """)
            cur.execute("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '_outbox_events' AND column_name = 'claimed_at'
                    ) THEN
                        ALTER TABLE _outbox_events ADD COLUMN claimed_at TEXT;
                    END IF;
                END $$;
            """)
            cur.execute("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '_outbox_events' AND column_name = 'claimed_by'
                    ) THEN
                        ALTER TABLE _outbox_events ADD COLUMN claimed_by TEXT;
                    END IF;
                END $$;
            """)
            cur.execute("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '_outbox_events' AND column_name = 'seq'
                    ) THEN
                        ALTER TABLE _outbox_events ADD COLUMN seq INTEGER NOT NULL DEFAULT 0;
                    END IF;
                END $$;
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS _eventos_processados (
                    event_id TEXT PRIMARY KEY,
                    seq INTEGER NOT NULL,
                    event_name TEXT NOT NULL,
                    consumer_id TEXT NOT NULL DEFAULT 'default',
                    processado_em TEXT NOT NULL
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_eventos_processados_seq ON _eventos_processados(seq, consumer_id);")
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
        antes do EventBus.emit() em memória ser disparado.

        O campo `seq` é monotônico por transação (MAX(seq)+1): serve de high-water
        mark para deduplicação idempotente do consumidor (_eventos_processados)."""
        event_id = uuid.uuid4().hex
        criado_em = datetime.datetime.now(datetime.timezone.utc).isoformat()
        prox_seq = int(conn.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM _outbox_events"
        ).fetchone()[0])
        conn.execute(
            """
            INSERT INTO _outbox_events (id, event_name, payload, status, criado_em, seq)
            VALUES (?, ?, ?, 'pendente', ?, ?)
            """,
            (event_id, event_name, json.dumps(payload, ensure_ascii=False), criado_em, prox_seq)
        )
        return event_id

    def registrar_evento_processado(
        self,
        conn,
        event_id: str,
        seq: int,
        event_name: str,
        consumer_id: str = "default",
        processado_em: str | None = None,
    ) -> bool:
        """Idempotência do consumidor: registra um evento como já processado por um
        consumer. Retorna True quando o registro é novo (primeira vez) e False quando
        o evento já havia sido processado pelo mesmo consumer (entrega duplicada)."""
        if processado_em is None:
            processado_em = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cur = conn.execute(
            "INSERT INTO _eventos_processados (event_id, seq, event_name, consumer_id, processado_em) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT (event_id) DO NOTHING",
            (event_id, seq, event_name, consumer_id, processado_em)
        )
        return bool(cur.rowcount == 1)

    def evento_ja_processado(self, conn, event_id: str) -> bool:
        """Retorna True se o evento já foi registrado como processado (em qualquer
        consumer). Ponto de checagem do consumidor antes de aplicar efeito colateral."""
        row = conn.execute(
            "SELECT 1 FROM _eventos_processados WHERE event_id = ? LIMIT 1",
            (event_id,)
        ).fetchone()
        return row is not None

    def ultimo_seq_processado(self, conn, consumer_id: str = "default"):
        """Retorna o maior `seq` já processado pelo consumer (high-water mark) ou
        None se o consumer ainda não processou evento nenhum."""
        row = conn.execute(
            "SELECT MAX(seq) FROM _eventos_processados WHERE consumer_id = ?",
            (consumer_id,)
        ).fetchone()
        valor = row[0] if row is not None else None
        return int(valor) if valor is not None else None