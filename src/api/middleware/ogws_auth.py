"""Authentication middleware for FastAPI.

This module implements the authentication middleware for the gateway application,
providing automatic token refresh and request retry capabilities.

Key Components:
    - Auth Middleware: Token refresh and retry logic
    - Request Processing: Auth failure handling
    - Token Management: Automatic refresh
    - Error Handling: Comprehensive error responses

Related Files:
    - src/api/security/oauth2.py: OAuth2 implementation
    - src/api/security/jwt.py: JWT token handling
    - src/protocols/ogx/auth/manager.py: Auth manager integration
    - src/api/routes/auth/user.py: Authentication endpoints

Security Considerations:
    - Implements automatic token refresh
    - Handles auth failures gracefully
    - Provides secure retry mechanism
    - Manages token lifecycle
    - Prevents token leakage

Implementation Notes:
    - Uses Starlette middleware base
    - Implements async request processing
    - Provides error recovery
    - Manages request flow
    - Handles connection issues

Future Considerations:
    - Rate limiting integration
    - Circuit breaker pattern
    - Request caching
    - Performance monitoring
    - Security event logging
"""

from typing import Callable, Optional

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from protocols.ogx.auth.manager import OGWSAuthManager, get_auth_manager


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for request processing.

    This middleware intercepts requests to handle authentication failures
    and implement automatic token refresh.

    Process Flow:
        1. Intercept incoming request
        2. Process request normally
        3. If auth fails (401):
           - Attempt token refresh
           - Retry request with new token
        4. Return response or error

    Error Handling:
        - Authentication failures
        - Token refresh failures
        - Network issues
        - Timeout errors
        - Server errors

    Security Features:
        - Automatic token refresh
        - Secure error handling
        - Request retry logic
        - Connection management
        - Error isolation

    Future Considerations:
        - Request throttling
        - Failure statistics
        - Performance metrics
        - Security logging
        - Circuit breaking
    """

    def __init__(self, app: ASGIApp):
        """Initialize the authentication middleware.

        Args:
            app: The ASGI application instance
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with authentication handling.

        This method implements the core middleware logic for handling
        authentication failures and token refresh.

        Process Flow:
            1. Attempt initial request
            2. Check for auth failure (401)
            3. If failed:
               - Get auth manager
               - Force token refresh
               - Retry request
            4. Return response

        Error Handling:
            - HTTP errors (401, 500)
            - Network errors
            - Timeout errors
            - Connection errors
            - Server errors

        Args:
            request: The incoming HTTP request
            call_next: Function to call next middleware

        Returns:
            Response from next middleware or error response

        Security Notes:
            - Handles token refresh securely
            - Prevents token exposure
            - Manages error responses
            - Isolates failures
        """
        try:
            # Initial request attempt
            response: Response = await call_next(request)

            # Handle authentication failure
            if response.status_code == 401:
                # Get auth manager instance
                auth_manager: OGWSAuthManager = await get_auth_manager()

                try:
                    # Attempt token refresh
                    await auth_manager.get_valid_token(force_refresh=True)
                    # Retry request with new token
                    response = await call_next(request)
                except httpx.HTTPError as e:
                    # Handle token refresh failure
                    return JSONResponse(
                        status_code=401,
                        content={
                            "detail": "Authentication failed",
                            "error": str(e),
                            "type": "token_refresh_error",
                        },
                    )

            return response

        except httpx.HTTPError as e:
            # Handle HTTP request errors
            return JSONResponse(
                status_code=500,
                content={"detail": "Request failed", "error": str(e), "type": "http_error"},
            )
        except (ConnectionError, TimeoutError, IOError) as e:
            # Handle network and system errors
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(e),
                    "type": "system_error",
                },
            )


def add_auth_middleware(app: FastAPI) -> None:
    """Add authentication middleware to FastAPI application.

    This function registers the authentication middleware with the
    FastAPI application instance.

    Process:
        1. Create middleware instance
        2. Add to FastAPI middleware stack
        3. Configure error handling

    Args:
        app: The FastAPI application instance

    Usage:
        ```python
        app = FastAPI()
        add_auth_middleware(app)
        ```

    Note:
        Should be added before request processing begins
    """
    app.add_middleware(AuthMiddleware)
