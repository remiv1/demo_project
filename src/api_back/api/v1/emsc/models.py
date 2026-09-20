"""
Pydantic models for the EMSC API.
"""

from datetime import datetime
from pydantic import BaseModel

class Geometri(BaseModel):
    """Geometric information for a feature."""
    type: str
    coordinates: list[float]

class Properties(BaseModel):
    """Properties of a seismic event."""
    source_id: int
    source_catalog: str
    last_update: datetime
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
    """A seismic event feature."""
    type: str
    id: str
    geometry: Geometri
    properties: Properties
