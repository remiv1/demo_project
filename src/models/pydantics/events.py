"""Pydantic models for representing geological event data."""

from datetime import datetime

from pydantic import BaseModel

class Geometri(BaseModel):
    type: str
    coordinates: list[float]

class Properties(BaseModel):
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
    type: str
    id: str
    geometry: Geometri
    properties: Properties
