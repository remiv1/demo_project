"""Repositories d'ingestion des différents types d'événements."""

from abc import ABC, abstractmethod
from typing import Any


class RepositoryNotImplementedError(NotImplementedError):
    """Signale qu'un repository attend encore son modèle et son mapping."""

class IngestionRepository(ABC):
    """Contrat d'ingestion transactionnelle vers PostgreSQL."""

    @abstractmethod
    def ingest(self, payload: dict[str, Any]) -> None:
        """Ingère un événement et valide sa transaction PostgreSQL."""
        raise RepositoryNotImplementedError
