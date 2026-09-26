"""Module for handling GET requests for the EMSC API (v1)."""

from fastapi import APIRouter
from .utils import fetch_emsc_data
from .models import Feature

router = APIRouter(
    prefix="/emsc",
    tags=["api", "v1", "emsc"],
)

@router.get("/")
async def get_emsc_data() -> dict[str, str | list[Feature]]:
    """Handle GET requests for EMSC data."""
    all_responses: list[Feature] = await fetch_emsc_data()
    return {"message": "EMSC GET endpoint", "data": all_responses}
