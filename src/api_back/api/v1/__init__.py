"""Module for API version 1 routing."""

from fastapi.routing import APIRouter
from .emsc import get_router as emsc_get_router

router = APIRouter(
    prefix="/v1",
    tags=["api", "v1"],
)
router.include_router(emsc_get_router)
