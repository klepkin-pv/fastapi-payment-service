"""Окружение Alembic: URL базы из окружения и метаданные моделей приложения."""

import importlib
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import MetaData, create_engine, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _target_metadata() -> MetaData:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "src"))
    base = importlib.import_module("app.core.db").Base
    importlib.import_module("app.tariffs.models")
    importlib.import_module("app.payments.models")
    return base.metadata


def _database_url() -> str:
    return importlib.import_module("app.core.config").settings.database_url


def run_migrations_offline() -> None:
    """Выполняет миграции в offline-режиме: генерация SQL без подключения."""
    context.configure(
        url=_database_url(),
        target_metadata=_target_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Выполняет миграции в online-режиме через подключение к базе."""
    connectable = create_engine(_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=_target_metadata())

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
