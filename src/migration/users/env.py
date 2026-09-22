"""Moteur Alembic généré pour la base users."""

import sys
import importlib
import os
import urllib.parse
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, "/app")

from common.config.db import BaseUsers  # pylint: disable=C0413
from common.models.sqlalchemy.users import Users, UsersPassword, UserSession # pylint: disable=W0611, C0413

configuration = context.config  # pylint: disable=E1101
password = urllib.parse.quote(os.getenv("POSTGRES_PASSWORD_MIGR", ""), safe="")
database_url = (
    "postgresql+psycopg2://"
    f"{os.getenv('POSTGRES_USER_MIGR', '')}:{password}"
    f"@{os.getenv('POSTGRES_HOST', '')}:{os.getenv('POSTGRES_PORT', '')}"
    f"/{os.getenv('POSTGRES_DB_USERS', '')}"
)
configuration.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

if configuration.config_file_name is not None:
    fileConfig(configuration.config_file_name)

target_metadata = BaseUsers.metadata


def run_migrations_offline() -> None:
    """Produire le SQL sans ouvrir de connexion."""

    context.configure(  # pylint: disable=E1101
        url=configuration.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="migr_users",
    )
    with context.begin_transaction():  # pylint: disable=E1101
        context.run_migrations()  # pylint: disable=E1101


def run_migrations_online() -> None:
    """Exécuter les migrations avec une connexion PostgreSQL."""

    connectable = engine_from_config(
        configuration.get_section(configuration.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(  # pylint: disable=E1101
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="migr_users",
            version_table="alembic_version",
        )
        with context.begin_transaction():  # pylint: disable=E1101
            context.run_migrations()  # pylint: disable=E1101


if context.is_offline_mode():  # pylint: disable=E1101
    run_migrations_offline()
else:
    run_migrations_online()
