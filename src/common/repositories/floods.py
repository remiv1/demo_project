"""Repository d'ingestion des inondations."""
from typing import Any

from sqlalchemy.orm import Session, scoped_session
from .common import RepositoryNotImplementedError

class FloodsRepo():
    """Repository des inondations."""
    def __init__(self, session: Session | scoped_session[Session]) -> None:
        self.session = session

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Ingère une inondation."""
        raise RepositoryNotImplementedError("Le repository flood n'est pas prêt.")
