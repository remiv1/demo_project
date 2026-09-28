"""Moteur Alembic généré pour la base main."""

import os
import urllib.parse
from logging.config import fileConfig

from alembic import context # pylint: disable=E0401
from sqlalchemy import engine_from_config, pool

from common.config.db import BaseMain
from common.models.sqlalchemy.emsc import *  # pylint: disable=W0611, W0401, W0614


configuration = context.config  # pylint: disable=E1101
password = urllib.parse.quote(os.getenv("POSTGRES_PASSWORD_MIGR", ""), safe="")
database_url = (
    "postgresql+psycopg2://"
    f"{os.getenv('POSTGRES_USER_MIGR', '')}:{password}"
    f"@{os.getenv('POSTGRES_HOST', '')}:{os.getenv('POSTGRES_PORT', '')}"
    f"/{os.getenv('POSTGRES_DB_MAIN', '')}"
)
configuration.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

if configuration.config_file_name is not None:
    fileConfig(configuration.config_file_name)

target_metadata = BaseMain.metadata


def include_name(name: str | None, type_: str, _parent_names: dict[str, str | None]) -> bool:
    """Exclut les tables gérées par l'extension PostGIS de l'autogénération.

    Args:
        name: Nom de l'objet inspecté.
        type_: Type de l'objet inspecté par Alembic.
        _parent_names: Noms de ses objets parents, inutilisés ici.

    Returns:
        Vrai si l'objet relève des migrations applicatives.
    """
    return not (type_ == "table" and name == "spatial_ref_sys")


def run_migrations_offline() -> None:
    """Produire le SQL sans ouvrir de connexion."""

    context.configure(  # pylint: disable=E1101
        url=configuration.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        include_name=include_name,  # type: ignore
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="migr_main",
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
            include_name=include_name,  # type: ignore
            version_table_schema="migr_main",
            version_table="alembic_version",
        )
        with context.begin_transaction():  # pylint: disable=E1101
            context.run_migrations()  # pylint: disable=E1101


if context.is_offline_mode():  # pylint: disable=E1101
    run_migrations_offline()
else:
    run_migrations_online()
