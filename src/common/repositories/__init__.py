"""Initialisation du package des repositories d'ingestion."""

from common.config.db.db_connection import main_session

from .earthquakes import EarthquakesRepo
from .floods import FloodsRepo
from .common import RepositoryNotImplementedError

REPOSITORIES: dict[str, object] = {
    "earthquakes": EarthquakesRepo(session=main_session),
    "flood": FloodsRepo(session=main_session),
}

__all__ = [
    "EarthquakesRepo",
    "FloodsRepo",
    "RepositoryNotImplementedError",
    "REPOSITORIES"
]
