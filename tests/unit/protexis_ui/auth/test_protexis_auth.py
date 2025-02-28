"""Unit tests for Protexis authentication middleware."""

import json

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

from Protexis_Command.api.common.middleware.protexis_auth import (
    ProtexisAuthMiddleware,
    add_protexis_auth_middleware,
)


@pytest.fixture
def app():
    """Create test FastAPI application with auth middleware."""
    app = FastAPI()
    add_protexis_auth_middleware(app)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def test_health_check_bypass(client):
    """Test that health check endpoint bypasses authentication."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_missing_auth_token(client):
    """Test request without authentication token."""
    response = client.get("/test")
    assert response.status_code == 401
    assert response.json() == {
        "detail": "No authentication token provided",
        "error_type": "auth_error",
    }


@pytest.mark.parametrize(
    "auth_header",
    [
        "Bearer",  # Missing token
        "bearer",  # Just the scheme
        "Token xyz",  # Wrong scheme
        "BearerInvalidFormat",  # No space
        "Bearer ",  # Empty token
        " ",  # Just whitespace
    ],
)
def test_invalid_auth_header_format(client, auth_header):
    """Test request with malformed authentication header."""
    response = client.get("/test", headers={"Authorization": auth_header})
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid authentication token",
        "error_type": "auth_error",
    }


def test_invalid_token_format(client):
    """Test request with invalid token format."""
    response = client.get("/test", headers={"Authorization": "Bearer invalid.token"})
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid authentication token",
        "error_type": "auth_error",
    }


def test_valid_token(app, monkeypatch):
    """Test request with valid token format."""
    # Mock verify_token_format to return True
    import Protexis_Command.api.common.middleware.protexis_auth as auth_module

    monkeypatch.setattr(auth_module, "verify_token_format", lambda x: True)

    client = TestClient(app)
    response = client.get("/test", headers={"Authorization": "Bearer valid.token.format"})
    assert response.status_code == 200
    assert response.json() == {"message": "success"}


@pytest.mark.asyncio
async def test_http_error_handling(app, monkeypatch):
    """Test handling of HTTP errors."""
    import httpx

    import Protexis_Command.api.common.middleware.protexis_auth as auth_module

    monkeypatch.setattr(auth_module, "verify_token_format", lambda x: True)

    async def mock_call_next(*args, **kwargs):
        raise httpx.HTTPError("HTTP Error")

    middleware = ProtexisAuthMiddleware(app=app)
    response = await middleware.dispatch(
        Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": [(b"authorization", b"Bearer valid.token")],
            }
        ),
        mock_call_next,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    response_data = json.loads(response.body)
    assert response_data["detail"] == "HTTP Error"
    assert response_data["error_type"] == "http_error"


@pytest.mark.asyncio
async def test_connection_error_handling(app, monkeypatch):
    """Test handling of connection errors."""
    import Protexis_Command.api.common.middleware.protexis_auth as auth_module

    monkeypatch.setattr(auth_module, "verify_token_format", lambda x: True)

    async def mock_call_next(*args, **kwargs):
        raise ConnectionError("Connection Error")

    middleware = ProtexisAuthMiddleware(app=app)
    response = await middleware.dispatch(
        Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": [(b"authorization", b"Bearer valid.token")],
            }
        ),
        mock_call_next,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    response_data = json.loads(response.body)
    assert response_data["detail"] == "Connection Error"
    assert response_data["error_type"] == "system_error"


@pytest.mark.asyncio
async def test_timeout_error_handling(app, monkeypatch):
    """Test handling of timeout errors."""
    import Protexis_Command.api.common.middleware.protexis_auth as auth_module

    monkeypatch.setattr(auth_module, "verify_token_format", lambda x: True)

    async def mock_call_next(*args, **kwargs):
        raise TimeoutError("Timeout Error")

    middleware = ProtexisAuthMiddleware(app=app)
    response = await middleware.dispatch(
        Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": [(b"authorization", b"Bearer valid.token")],
            }
        ),
        mock_call_next,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    response_data = json.loads(response.body)
    assert response_data["detail"] == "Timeout Error"
    assert response_data["error_type"] == "system_error"
