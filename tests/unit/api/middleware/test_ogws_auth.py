"""Unit tests for authentication middleware.

This module tests the authentication middleware functionality:
- Request processing
- Token refresh handling
- Error handling
- Response management
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp

from Protexis_Command.api_ogx.auth.manager import OGxAuthManager
from Protexis_Command.api_ogx.middleware.ogx_auth import OGxAuthMiddleware, add_ogx_auth_middleware


@pytest.fixture
def mock_app():
    """Fixture for mocked ASGI application."""
    return MagicMock(spec=ASGIApp)


@pytest.fixture
def mock_request():
    """Fixture for mocked HTTP request."""
    return MagicMock(spec=Request)


@pytest.fixture
def mock_auth_manager():
    """Fixture for mocked auth manager."""
    manager = AsyncMock(spec=OGxAuthManager)
    manager.get_valid_token = AsyncMock()
    return manager


@pytest.fixture
def mock_response():
    """Fixture for mocked response."""
    response = MagicMock(spec=Response)
    response.status_code = 200
    return response


@pytest.mark.asyncio
async def test_successful_request(mock_app, mock_request, mock_response):
    """Test successful request processing.

    Verifies:
    - Request is processed normally
    - No token refresh is attempted
    - Original response is returned
    """
    middleware = OGxAuthMiddleware(mock_app)
    call_next = AsyncMock(return_value=mock_response)

    response = await middleware.dispatch(mock_request, call_next)

    assert response == mock_response
    call_next.assert_awaited_once_with(mock_request)


@pytest.mark.asyncio
async def test_auth_failure_with_successful_refresh(
    mock_app, mock_request, mock_auth_manager, mock_response
):
    """Test authentication failure with successful token refresh.

    Verifies:
    - Initial 401 response triggers token refresh
    - Token is refreshed
    - Request is retried
    - New response is returned
    """
    middleware = OGxAuthMiddleware(mock_app)

    # Configure responses for first and second attempts
    failed_response = MagicMock(spec=Response)
    failed_response.status_code = 401

    call_next = AsyncMock(side_effect=[failed_response, mock_response])

    # Mock auth manager
    with patch(
        "api.middleware.OGx_auth.get_auth_manager",
        AsyncMock(return_value=mock_auth_manager),
    ):
        response = await middleware.dispatch(mock_request, call_next)

    # Verify behavior
    assert response == mock_response
    assert call_next.await_count == 2
    mock_auth_manager.get_valid_token.assert_awaited_once_with(force_refresh=True)


@pytest.mark.asyncio
async def test_auth_failure_with_refresh_error(mock_app, mock_request, mock_auth_manager):
    """Test authentication failure with token refresh error.

    Verifies:
    - Initial 401 response triggers token refresh
    - Token refresh fails
    - Error response is returned
    - No retry is attempted
    """
    middleware = OGxAuthMiddleware(mock_app)

    # Configure initial 401 response
    failed_response = MagicMock(spec=Response)
    failed_response.status_code = 401

    call_next = AsyncMock(return_value=failed_response)

    # Mock auth manager to raise error
    mock_auth_manager.get_valid_token.side_effect = httpx.HTTPError("Token refresh failed")

    with patch(
        "api.middleware.OGx_auth.get_auth_manager",
        AsyncMock(return_value=mock_auth_manager),
    ):
        response = await middleware.dispatch(mock_request, call_next)

    # Verify error response
    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    assert response.body.decode().find("Token refresh failed") != -1
    assert call_next.await_count == 1


@pytest.mark.asyncio
async def test_http_error_handling(mock_app, mock_request):
    """Test handling of HTTP errors.

    Verifies:
    - HTTP errors are caught
    - Appropriate error response is returned
    - Error details are included
    """
    middleware = OGxAuthMiddleware(mock_app)

    # Configure call_next to raise HTTP error
    error_msg = "HTTP connection failed"
    call_next = AsyncMock(side_effect=httpx.HTTPError(error_msg))

    response = await middleware.dispatch(mock_request, call_next)

    # Verify error response
    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    assert response.body.decode().find(error_msg) != -1
    assert response.body.decode().find("http_error") != -1


@pytest.mark.asyncio
async def test_network_error_handling(mock_app, mock_request):
    """Test handling of network errors.

    Verifies:
    - Network errors are caught
    - Appropriate error response is returned
    - Error details are included
    """
    middleware = OGxAuthMiddleware(mock_app)

    # Configure call_next to raise network error
    error_msg = "Connection failed"
    call_next = AsyncMock(side_effect=ConnectionError(error_msg))

    response = await middleware.dispatch(mock_request, call_next)

    # Verify error response
    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    assert response.body.decode().find(error_msg) != -1
    assert response.body.decode().find("system_error") != -1


@pytest.mark.asyncio
async def test_timeout_error_handling(mock_app, mock_request):
    """Test handling of timeout errors.

    Verifies:
    - Timeout errors are caught
    - Appropriate error response is returned
    - Error details are included
    """
    middleware = OGxAuthMiddleware(mock_app)

    # Configure call_next to raise timeout error
    error_msg = "Request timed out"
    call_next = AsyncMock(side_effect=TimeoutError(error_msg))

    response = await middleware.dispatch(mock_request, call_next)

    # Verify error response
    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    assert response.body.decode().find(error_msg) != -1
    assert response.body.decode().find("system_error") != -1


def test_add_auth_middleware():
    """Test middleware registration.

    Verifies:
    - Middleware is properly added to FastAPI app
    - Correct middleware class is used
    """
    app = FastAPI()
    add_ogx_auth_middleware(app)

    # Verify middleware was added
    middleware_added = False
    for middleware in app.user_middleware:
        if middleware.cls == OGxAuthMiddleware:
            middleware_added = True
            break

    assert middleware_added, "OGx AuthMiddleware was not added to the FastAPI application"


@pytest.mark.asyncio
async def test_auth_failure_with_subsequent_failure(mock_app, mock_request, mock_auth_manager):
    """Test authentication failure with failed retry.

    Verifies:
    - Initial 401 response triggers token refresh
    - Token is refreshed successfully
    - Retry request also fails with 401
    - Original 401 response is returned
    """
    middleware = OGxAuthMiddleware(mock_app)

    # Configure both attempts to return 401
    failed_response = MagicMock(spec=Response)
    failed_response.status_code = 401

    call_next = AsyncMock(return_value=failed_response)

    with patch(
        "Protexis_Command.api_ogx.middleware.ogx_auth.get_auth_manager",
        AsyncMock(return_value=mock_auth_manager),
    ):
        response = await middleware.dispatch(mock_request, call_next)

    # Verify behavior
    assert response == failed_response
    assert call_next.await_count == 2
    mock_auth_manager.get_valid_token.assert_awaited_once_with(force_refresh=True)
