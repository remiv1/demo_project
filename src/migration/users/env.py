"""Moteur Alembic généré pour la base users."""

import importlib
import os
import urllib.parse
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool


def resolve_object(dotted_path: str) -> Any:
    """Résoudre un objet depuis son chemin Python qualifié."""

    parts = dotted_path.split(".")
    for index in range(len(parts), 0, -1):
        try:
            value: Any = importlib.import_module(".".join(parts[:index]))
        except ModuleNotFoundError:
            continue
        for attribute in parts[index:]:
            value = getattr(value, attribute)
        return value
    raise ImportError(f"Objet Python introuvable : {dotted_path}")



importlib.import_module("common.models")


configuration = context.config
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

target_metadata = resolve_object("common.SecureBase.metadata")


def run_migrations_offline() -> None:
    """Produire le SQL sans ouvrir de connexion."""

    context.configure(
        url=configuration.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="migr_users",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécuter les migrations avec une connexion PostgreSQL."""

    connectable = engine_from_config(
        configuration.get_section(configuration.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="migr_users",
            version_table="alembic_version",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()