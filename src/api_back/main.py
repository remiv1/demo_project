"""Main application for the API backend."""
from fastapi import FastAPI
from .api import router as api_router

app = FastAPI()
app.include_router(api_router)

@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
