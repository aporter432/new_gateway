"""Unit tests for OGx authentication middleware.

Tests the middleware's handling of:
- Normal requests
- 401 responses and token refresh
- Error scenarios
- Middleware registration
"""

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from Protexis_Command.api.common.middleware.ogx_auth import (
    OGxAuthMiddleware,
    add_ogx_auth_middleware,
)


@pytest.fixture
def mock_auth_manager():
    """Create a mock authentication manager."""
    manager = AsyncMock()
    manager.refresh_token.return_value = True
    return manager


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    return AsyncMock()


@pytest.fixture
def mock_asgi_app() -> ASGIApp:
    """Create a mock ASGI application."""

    async def app(_scope: Scope, _receive: Receive, _send: Send) -> None:
        pass

    return app


class TestOGxAuthMiddleware:
    """Test suite for OGx authentication middleware."""

    async def test_successful_request(
        self, mock_request: Any, mock_auth_manager: AsyncMock, mock_asgi_app: ASGIApp
    ):
        """Test successful request processing."""
        middleware = OGxAuthMiddleware(app=mock_asgi_app)

        async def mock_call_next(_request: Any) -> Response:
            return Response(status_code=200)

        patch_path = "Protexis_Command.api.common.middleware.ogx_auth.get_auth_manager"
        with patch(patch_path, return_value=mock_auth_manager):
            response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    async def test_401_with_refresh(
        self, mock_request: Any, mock_auth_manager: AsyncMock, mock_asgi_app: ASGIApp
    ):
        """Test handling of 401 response with token refresh."""
        middleware = OGxAuthMiddleware(app=mock_asgi_app)

        responses = [Response(status_code=401), Response(status_code=200)]
        response_iter = iter(responses)

        async def mock_call_next(_request: Any) -> Response:
            return next(response_iter)

        patch_path = "Protexis_Command.api.common.middleware.ogx_auth.get_auth_manager"
        with patch(patch_path, return_value=mock_auth_manager):
            response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    async def test_401_with_failed_refresh(
        self, mock_request: Any, mock_auth_manager: AsyncMock, mock_asgi_app: ASGIApp
    ):
        """Test handling of 401 when token refresh fails."""
        middleware = OGxAuthMiddleware(app=mock_asgi_app)

        # First response is 401, which triggers token refresh
        responses = [Response(status_code=401), Response(status_code=401)]  # Add second response
        response_iter = iter(responses)

        async def mock_call_next(_request: Any) -> Response:
            return next(response_iter)

        # Mock refresh_token to fail
        mock_auth_manager.refresh_token.return_value = (
            False  # Change to return_value instead of side_effect
        )

        patch_path = "Protexis_Command.api.common.middleware.ogx_auth.get_auth_manager"
        with patch(patch_path, return_value=mock_auth_manager):
            response = await middleware.dispatch(mock_request, mock_call_next)

        # When token refresh fails, middleware should pass through the 401
        assert response.status_code == 401

    async def test_unexpected_error(
        self, mock_request: Any, mock_auth_manager: AsyncMock, mock_asgi_app: ASGIApp
    ):
        """Test handling of unexpected errors during request processing."""
        middleware = OGxAuthMiddleware(app=mock_asgi_app)

        async def mock_call_next(_request: Any) -> Response:
            raise RuntimeError("Unexpected error")

        patch_path = "Protexis_Command.api.common.middleware.ogx_auth.get_auth_manager"
        with patch(patch_path, return_value=mock_auth_manager):
            response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 500
        assert isinstance(response, JSONResponse)
        error_body = json.loads(bytes(response.body).decode("utf-8"))
        assert "Unexpected error" in str(error_body)

    def test_add_middleware(self):
        """Test middleware registration with FastAPI app."""
        app = FastAPI()
        add_ogx_auth_middleware(app)

        # Get the middleware list directly from the app
        middlewares = app.user_middleware

        # Check if our middleware is in the list using proper attribute access
        assert any(
            middleware.cls == OGxAuthMiddleware for middleware in middlewares
        )  # Access cls as an attribute
