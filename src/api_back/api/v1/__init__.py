"""Module for API version 1 routing."""

from fastapi.routing import APIRouter
from .redis import redis_router
from .user import router as user_router

router = APIRouter(
    prefix="/v1",
    tags=["api", "v1"],
)
router.include_router(redis_router)
router.include_router(user_router)
