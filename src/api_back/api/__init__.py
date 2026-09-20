"""Module for API routing. Defines the main API router with a prefix and tags."""
from fastapi.routing import APIRouter
from .v1 import router as v1_router

router = APIRouter(
    prefix="/api",
    tags=["api"],
)

router.include_router(v1_router)
