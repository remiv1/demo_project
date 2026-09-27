"""Initialisation du package des repositories d'ingestion."""

from .earthquakes import Earthquakes
from .floods import Flood
from .common import IngestionRepository, RepositoryNotImplementedError

REPOSITORIES: dict[str, IngestionRepository] = {
    "earthquakes": Earthquakes(),
    "flood": Flood(),
}

__all__ = [
    "Earthquakes",
    "Flood",
    "IngestionRepository",
    "RepositoryNotImplementedError",
    "REPOSITORIES"
]
