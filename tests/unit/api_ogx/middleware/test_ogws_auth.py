"""Unit tests for authentication middleware.

This module tests the authentication middleware functionality:
- Request processing
- Token validation
- Error handling
- Response management
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp

from Protexis_Command.api_protexis.middleware.protexis_auth import (
    ProtexisAuthMiddleware,
    add_protexis_auth_middleware,
)


@pytest.fixture
def mock_app():
    """Fixture for mocked ASGI application."""
    return MagicMock(spec=ASGIApp)


@pytest.fixture
def mock_request():
    """Fixture for mocked HTTP request."""
    request = MagicMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/api/test"  # Not health check path
    request.headers = {}  # Initialize empty headers
    return request


@pytest.fixture
def mock_response():
    """Fixture for mocked response."""
    response = MagicMock(spec=Response)
    response.status_code = 200
    return response


@pytest.fixture
def valid_jwt_token():
    """Provide a valid format JWT token for testing."""
    return "header.payload.signature"


@pytest.mark.asyncio
async def test_successful_request(mock_app, mock_request, mock_response, valid_jwt_token):
    """Test successful request processing.

    Verifies:
    - Request is processed normally
    - Original response is returned
    """
    middleware = ProtexisAuthMiddleware(mock_app)
    call_next = AsyncMock(return_value=mock_response)

    # Add valid JWT token
    mock_request.headers = {"Authorization": f"Bearer {valid_jwt_token}"}

    response = await middleware.dispatch(mock_request, call_next)

    assert response == mock_response
    call_next.assert_awaited_once_with(mock_request)


@pytest.mark.asyncio
async def test_http_error_handling(mock_app, mock_request, valid_jwt_token):
    """Test handling of HTTP errors."""
    middleware = ProtexisAuthMiddleware(mock_app)
    mock_request.headers = {"Authorization": f"Bearer {valid_jwt_token}"}

    # Create error with actual message
    error_msg = "HTTP connection failed"
    error = httpx.HTTPError(error_msg)
    call_next = AsyncMock(side_effect=error)

    response = await middleware.dispatch(mock_request, call_next)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    response_data = bytes(response.body).decode()
    assert "error_type" in response_data
    assert "http_error" in response_data
    assert error_msg in response_data


@pytest.mark.asyncio
async def test_network_error_handling(mock_app, mock_request, valid_jwt_token):
    """Test handling of network errors."""
    middleware = ProtexisAuthMiddleware(mock_app)
    mock_request.headers = {"Authorization": f"Bearer {valid_jwt_token}"}

    # Create error with actual message
    error_msg = "Connection failed"
    error = ConnectionError(error_msg)
    call_next = AsyncMock(side_effect=error)

    response = await middleware.dispatch(mock_request, call_next)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    response_data = bytes(response.body).decode()
    assert "error_type" in response_data
    assert "system_error" in response_data
    assert error_msg in response_data


@pytest.mark.asyncio
async def test_timeout_error_handling(mock_app, mock_request, valid_jwt_token):
    """Test handling of timeout errors."""
    middleware = ProtexisAuthMiddleware(mock_app)
    mock_request.headers = {"Authorization": f"Bearer {valid_jwt_token}"}

    # Create error with actual message
    error_msg = "Request timed out"
    error = TimeoutError(error_msg)
    call_next = AsyncMock(side_effect=error)

    response = await middleware.dispatch(mock_request, call_next)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    response_data = bytes(response.body).decode()
    assert "error_type" in response_data
    assert "system_error" in response_data
    assert error_msg in response_data


@pytest.mark.asyncio
async def test_missing_auth_header(mock_app, mock_request):
    """Test request without auth header."""
    middleware = ProtexisAuthMiddleware(mock_app)
    mock_request.headers = {}  # No Authorization header

    response = await middleware.dispatch(mock_request, AsyncMock())

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    response_data = bytes(response.body).decode()
    assert "error_type" in response_data
    assert "auth_error" in response_data


@pytest.mark.asyncio
async def test_invalid_token_format(mock_app, mock_request):
    """Test request with invalid token format."""
    middleware = ProtexisAuthMiddleware(mock_app)
    mock_request.headers = {"Authorization": "Bearer invalid"}  # Invalid token format

    response = await middleware.dispatch(mock_request, AsyncMock())

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    response_data = bytes(response.body).decode()
    assert "error_type" in response_data
    assert "auth_error" in response_data


def test_add_auth_middleware():
    """Test middleware registration.

    Verifies:
    - Middleware is properly added to FastAPI app
    - Correct middleware class is used
    """
    app = FastAPI()
    add_protexis_auth_middleware(app)

    # Verify middleware was added
    middleware_added = False
    for middleware in app.user_middleware:
        if middleware.cls == ProtexisAuthMiddleware:
            middleware_added = True
            break

    assert middleware_added, "Protexis AuthMiddleware was not added to the FastAPI application"
