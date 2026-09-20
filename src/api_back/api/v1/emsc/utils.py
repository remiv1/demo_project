"""Utility functions for the EMSC API (v1)."""

from datetime import datetime, timezone, timedelta
from typing import Any
import httpx
import pandas as pd
from config import InfraConfig
from .models import Feature

API_URL = "https://www.seismicportal.eu/fdsnws/event/1/query"

async def fetch_emsc_data() -> list[Feature]:
    """Fetch EMSC data from the API."""
    infra_config = InfraConfig()
    start_history = infra_config.ingestion.history_start
    timeout = infra_config.ingestion.timeout
    end_history = datetime.now(timezone.utc)
    date_list = pd.date_range(start=start_history, end=end_history, freq='D').tolist()
    all_responses: list[Feature] = []

    for d in date_list:
        d_plus_one = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(days=1)
        params: dict[str, Any] = {
            "limit": 10000,
            "start": d,
            "end": d_plus_one,
            "format": "json",
            "nodata": 204,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                API_URL,
                params=params,
                timeout=timeout,
            )
        response = response.json()["features"]
        all_responses.extend([Feature(**item) for item in response])

    return all_responses
