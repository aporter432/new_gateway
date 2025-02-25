"""API route handlers for OGx protocol."""

from .messages import router as messages_router
from .terminal import router as terminal_router
from .updates import router as updates_router

__all__ = ["messages_router", "terminal_router", "updates_router"]
