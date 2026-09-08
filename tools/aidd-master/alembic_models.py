# -*- coding: utf-8 -*-
"""
Alembic Model Registry — AIDD Master Enterprise.

SQLAlchemy ORM models that mirror the existing raw-sql schemas from:
  - src/core/database.py (init_system_tables: _schema_migrations, _outbox_events, _audit_log)
  - src/modules/*/models.py (init_schema: mod_* tables)

These models are used exclusively by Alembic for autogenerate support.
The application code continues to use raw sqlite3 — this file is the
single source of truth for Alembic's schema introspection.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Index,
    create_engine,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ---------------------------------------------------------------------------
# System tables (from src/core/database.py → SQLiteAdapter.init_system_tables)
# ---------------------------------------------------------------------------

class SchemaMigration(Base):
    __tablename__ = "_schema_migrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_name = Column(String, nullable=False, unique=True)
    version = Column(Integer, nullable=False)
    applied_at = Column(DateTime, server_default="CURRENT_TIMESTAMP")


class OutboxEvent(Base):
    __tablename__ = "_outbox_events"

    id = Column(String, primary_key=True)
    event_name = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String, nullable=False, server_default="pendente")
    criado_em = Column(String, nullable=False)
    processado_em = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_outbox_status", "status"),
    )


class AuditLog(Base):
    __tablename__ = "_audit_log"

    id = Column(String, primary_key=True)
    timestamp = Column(String, nullable=False)
    action = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    prev_hash = Column(String, nullable=False)
    curr_hash = Column(String, nullable=False)


# ---------------------------------------------------------------------------
# Business module tables (from src/modules/modulo1/models.py → init_schema)
# ---------------------------------------------------------------------------

class ModModulo1(Base):
    __tablename__ = "mod_modulo1"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    dados_json = Column(Text, nullable=True)
    status = Column(String, server_default="ativo")
    ativo = Column(Integer, server_default="1")
    criado_em = Column(DateTime, server_default="CURRENT_TIMESTAMP")
    atualizado_em = Column(DateTime, server_default="CURRENT_TIMESTAMP")
    deletado_em = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_modulo1_ativo", "ativo"),
        Index("idx_modulo1_status", "status"),
        Index("idx_modulo1_deletado", "deletado_em"),
    )
