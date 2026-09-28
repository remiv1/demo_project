"""Repository d'ingestion des tremblements de terre."""

from typing import Any
from .common import IngestionRepository, RepositoryNotImplementedError

class Earthquakes(IngestionRepository):
    """Repository des tremblements de terre."""

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Ingère un tremblement de terre."""
        raise RepositoryNotImplementedError("Le repository earthquakes n'est pas prêt.")
