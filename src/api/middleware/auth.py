"""Authentication middleware for FastAPI.

This module provides:
- Automatic token refresh
- Error handling for auth failures
- Request retry with new token
"""

from typing import Callable
import httpx
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.security import OGWSAuthManager, get_auth_manager


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for handling authentication and token refresh."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle auth errors.

        This middleware:
        1. Attempts the request
        2. If auth fails, tries to refresh token
        3. Retries request with new token
        4. Returns error if all attempts fail
        """
        try:
            # First attempt
            response = await call_next(request)

            # Check if auth failed
            if response.status_code == 401:
                # Get auth manager
                auth_manager: OGWSAuthManager = await get_auth_manager()

                # Force token refresh
                try:
                    await auth_manager.get_valid_token(force_refresh=True)
                    # Retry request with new token
                    response = await call_next(request)
                except httpx.HTTPError as e:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Authentication failed", "error": str(e)},
                    )

            return response

        except httpx.HTTPError as e:
            return JSONResponse(
                status_code=500, content={"detail": "Request failed", "error": str(e)}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500, content={"detail": "Internal server error", "error": str(e)}
            )


# Helper function to add middleware to FastAPI app
def add_auth_middleware(app):
    """Add authentication middleware to FastAPI app."""
    app.add_middleware(AuthMiddleware)
