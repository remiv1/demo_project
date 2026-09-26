"""Models for Redis interactions in the API backend."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

class ImportanceMessage(Enum):
    """Enum representing the importance of a seism message."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    WARNING = "warning"

class NewSeismMessage(BaseModel):
    """Model representing a new seism message for Redis."""

    emsc_id: str
    db_id: str
    timestamp: datetime
    importance: ImportanceMessage = ImportanceMessage.LOW
    magnitude: float
    latitude: float
    longitude: float
    depth: float
