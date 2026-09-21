"""Configuration de la connexion à la base de données."""

from os import getenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker
from common.config.db.db_config import DatabaseConfig, DatabaseUsage


BaseMain = declarative_base()
BaseUsers = declarative_base()

main_engine = create_engine(DatabaseConfig(DatabaseUsage.MAIN).get_url(getenv('SAFEPASS')))
users_engine = create_engine(DatabaseConfig(DatabaseUsage.USERS).get_url(getenv('SAFEPASS')))

main_session = scoped_session(sessionmaker(bind=main_engine))
users_session = scoped_session(sessionmaker(bind=users_engine))
