"""OGx authentication middleware.

This module implements authentication middleware for the OGx API.
It validates JWT tokens and enforces authentication requirements.
"""

from typing import Callable

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from Protexis_Command.api.services.auth.manager import OGxAuthManager, get_auth_manager


class OGxAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling OGx API authentication.

    This middleware intercepts all requests to check for authentication failures (401).
    If a 401 is encountered, it attempts to refresh the authentication token and retry
    the request. This ensures seamless token refresh without exposing the complexity
    to the client.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request through the authentication middleware.

        Args:
            request (Request): The incoming HTTP request
            call_next (Callable): The next middleware or route handler in the chain

        Returns:
            Response: The HTTP response

        If a 401 is received, attempts to refresh the token and retry the request.
        Falls back to error responses if authentication fails or other errors occur.
        """
        try:
            response = await call_next(request)
            if response.status_code == 401:
                auth_manager: OGxAuthManager = await get_auth_manager()
                try:
                    await auth_manager.get_valid_token(force_refresh=True)
                    response = await call_next(request)
                except httpx.HTTPError as e:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "OGx authentication failed", "error": str(e)},
                    )
            return response
        except Exception as e:
            return JSONResponse(
                status_code=500, content={"detail": "OGx API error", "error": str(e)}
            )


def add_ogx_auth_middleware(app: FastAPI) -> None:
    """
    Register the OGx authentication middleware with a FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance to add the middleware to

    This function should be called during application startup to enable automatic
    token refresh handling for OGx API requests.
    """
    app.add_middleware(OGxAuthMiddleware)
