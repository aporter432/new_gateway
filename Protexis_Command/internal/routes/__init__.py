"""
This module contains the routes for the API.
"""

from ...api.internal.routes.messages import router as messages_router

__all__ = ["messages_router"]
