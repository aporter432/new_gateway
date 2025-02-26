"""Authentication middleware for Protexis API.

This module implements authentication middleware for the Protexis API.
"""

from typing import Callable

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from Protexis_Command.api.common.auth.token_utils import verify_token_format


class ProtexisAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for validating authentication tokens."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and validate token.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response from next middleware or error response
        """
        try:
            # Skip auth for health check
            if request.url.path == "/health":
                return await call_next(request)

            # Verify JWT token for Protexis API
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "No authentication token provided",
                        "error_type": "auth_error",
                    },
                )

            token = auth_header.split(" ")[1]
            if not verify_token_format(token):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication token", "error_type": "auth_error"},
                )

            return await call_next(request)

        except httpx.HTTPError as e:
            return JSONResponse(
                status_code=500, content={"detail": str(e), "error_type": "http_error"}
            )
        except ConnectionError as e:
            return JSONResponse(
                status_code=500, content={"detail": str(e), "error_type": "system_error"}
            )
        except TimeoutError as e:
            return JSONResponse(
                status_code=500, content={"detail": str(e), "error_type": "system_error"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500, content={"detail": str(e), "error_type": "system_error"}
            )


def add_protexis_auth_middleware(app: FastAPI) -> None:
    """Add authentication middleware to FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(ProtexisAuthMiddleware)
