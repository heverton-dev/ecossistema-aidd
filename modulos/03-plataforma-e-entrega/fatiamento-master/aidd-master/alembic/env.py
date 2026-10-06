# -*- coding: utf-8 -*-
"""
Alembic environment configuration — AIDD Master Enterprise.

Reads DATABASE_URL from environment (or falls back to sqlite:///app.db),
imports the SQLAlchemy model registry from alembic_models.py, and
configures the Alembic context for autogeneration against SQLite.
"""

import os
import sys
import re
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# Ensure src/ is on the path so we can import alembic_models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from alembic_models import Base  # noqa: E402

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata for autogenerate support
target_metadata = Base.metadata


def _resolve_database_url() -> str:
    """Resolve the database URL from environment or config."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        url = config.get_main_option("sqlalchemy.url")
    if not url:
        url = "sqlite:///app.db"

    # Alembic needs a raw sqlite:/// URL (not the RLSConnection wrapper)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL without connecting."""
    url = _resolve_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to the database."""
    url = _resolve_database_url()
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        # SQLite-specific: enable WAL mode for concurrent reads
        connect_args={"timeout": 10} if "sqlite" in url else {},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
