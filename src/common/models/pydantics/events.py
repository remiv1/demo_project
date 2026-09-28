"""Pydantic models for representing geological event data."""

from datetime import datetime

from pydantic import BaseModel

class Geometri(BaseModel):
    """Modèle représentant la géométrie d'un événement géologique."""
    type: str
    coordinates: list[float]

class Properties(BaseModel):
    """Modèle représentant les propriétés d'un événement géologique."""
    source_id: int
    source_catalog: str
    lastupdate: datetime
    time: datetime
    flynn_region: str
    lat: float
    lon: float
    depth: float
    evtype: str
    auth: str
    mag: float
    magtype: str
    unid: str

class Feature(BaseModel):
    """Modèle représentant un événement géologique."""
    type: str
    id: str
    geometry: Geometri
    properties: Properties
