"""Repository d'ingestion des inondations."""
from typing import Any
from .common import IngestionRepository, RepositoryNotImplementedError

class Flood(IngestionRepository):
    """Repository des inondations."""

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Ingère une inondation."""
        raise RepositoryNotImplementedError("Le repository flood n'est pas prêt.")
