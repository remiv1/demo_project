"""Module for Pydantic models related to infrastructure configuration."""

from pydantic import BaseModel

class IngestionModel(BaseModel):
    """Pydantic model for ingestion configuration."""
    history_start: str
    timeout: int

class InfraConfigModel(BaseModel):
    """Pydantic model for infrastructure configuration."""
    ingestion: IngestionModel
