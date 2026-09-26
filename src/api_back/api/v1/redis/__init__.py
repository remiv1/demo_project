"""Redis API v1 package."""

from .commands import router as redis_router

__all__ = ["redis_router"]
