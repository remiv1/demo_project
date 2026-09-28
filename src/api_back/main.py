"""Main application for the API backend."""
import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from .api import router as api_router
from .emsc_stream import relay_emsc_events


@asynccontextmanager
async def lifespan(fastapi_application: FastAPI):   # pylint: disable=W0613
    """Lance puis arrête l'écoute du flux EMSC avec l'API."""
    task = asyncio.create_task(relay_emsc_events())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

app = FastAPI(lifespan=lifespan)
app.include_router(api_router)

@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
