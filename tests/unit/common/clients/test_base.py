"""Unit tests for base API client.

This module tests the base API client functionality:
- GET requests
- POST requests
- Response handling
- Error handling
- Authentication header management
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import Response

from Protexis_Command.api.common.auth.manager import OGxAuthManager
from Protexis_Command.api.common.clients.base import BaseAPIClient
from Protexis_Command.api.config.http_error_codes import HTTPErrorCode
from Protexis_Command.core.settings.app_settings import Settings
from Protexis_Command.protocols.ogx.validation.ogx_validation_exceptions import OGxProtocolError


@pytest.fixture
def mock_auth_manager():
    """Create a mock authentication manager."""
    manager = AsyncMock(spec=OGxAuthManager)
    manager.get_auth_header.return_value = {"Authorization": "Bearer test_token"}
    return manager


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    settings.OGx_BASE_URL = "http://test.api/v1"
    return settings


@pytest.fixture
def base_client(mock_auth_manager, mock_settings):
    """Create a BaseAPIClient instance with mocked dependencies."""
    return BaseAPIClient(mock_auth_manager, mock_settings)


@pytest.fixture
def mock_response():
    """Create a mock successful response."""
    response = MagicMock(spec=Response)
    response.status_code = 200
    response.json.return_value = {"ErrorID": 0, "data": "test_data"}
    return response


class TestBaseAPIClient:
    """Test suite for BaseAPIClient."""

    @pytest.mark.asyncio
    async def test_get_request_success(self, base_client, mock_response):
        """Test successful GET request."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            response = await base_client.get("/test", {"param": "value"})

            # Verify response
            assert response == mock_response

            # Verify request was made correctly
            mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
                "http://test.api/v1/test",
                headers={"Authorization": "Bearer test_token"},
                params={"param": "value"},
            )

    @pytest.mark.asyncio
    async def test_post_request_json_success(self, base_client, mock_response):
        """Test successful POST request with JSON data."""
        json_data = {"key": "value"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            response = await base_client.post("/test", json_data=json_data)

            # Verify response
            assert response == mock_response

            # Verify request was made correctly
            mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
                "http://test.api/v1/test",
                headers={"Authorization": "Bearer test_token", "Content-Type": "application/json"},
                json=json_data,
                data=None,
            )

    @pytest.mark.asyncio
    async def test_post_request_form_data_success(self, base_client, mock_response):
        """Test successful POST request with form data."""
        form_data = {"key": "value"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            response = await base_client.post("/test", data=form_data)

            # Verify response
            assert response == mock_response

            # Verify request was made correctly
            mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
                "http://test.api/v1/test",
                headers={
                    "Authorization": "Bearer test_token",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                json=None,
                data=form_data,
            )

    @pytest.mark.asyncio
    async def test_get_request_http_error(self, base_client):
        """Test GET request with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.HTTPError(
                "HTTP Error"
            )

            with pytest.raises(httpx.HTTPError):
                await base_client.get("/test")

    @pytest.mark.asyncio
    async def test_post_request_http_error(self, base_client):
        """Test POST request with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.HTTPError(
                "HTTP Error"
            )

            with pytest.raises(httpx.HTTPError):
                await base_client.post("/test", json_data={"key": "value"})

    @pytest.mark.asyncio
    async def test_handle_response_success(self, base_client, mock_response):
        """Test successful response handling."""
        result = await base_client.handle_response(mock_response)

        assert result == {"ErrorID": 0, "data": "test_data"}

    @pytest.mark.asyncio
    async def test_handle_response_api_error(self, base_client):
        """Test handling of API-level error."""
        error_response = MagicMock(spec=Response)
        error_response.status_code = 200
        error_response.json.return_value = {"ErrorID": 1, "ErrorMessage": "API Error"}

        with pytest.raises(OGxProtocolError) as exc_info:
            await base_client.handle_response(error_response)

        assert "API error: API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_response_rate_limit(self, base_client):
        """Test handling of rate limit error."""
        rate_limit_response = MagicMock(spec=Response)
        rate_limit_response.status_code = HTTPErrorCode.TOO_MANY_REQUESTS
        rate_limit_response.json.return_value = {"ErrorID": 1, "RetryAfter": 30}

        with pytest.raises(OGxProtocolError) as exc_info:
            await base_client.handle_response(rate_limit_response)

        assert "Rate limit exceeded. Retry after 30 seconds" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_auth_header_propagation(self, base_client, mock_auth_manager, mock_response):
        """Test that authentication headers are properly propagated."""
        custom_auth_header = {"Authorization": "Bearer custom_token"}
        mock_auth_manager.get_auth_header.return_value = custom_auth_header

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            await base_client.get("/test")

            # Verify auth header was used
            mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
                "http://test.api/v1/test", headers=custom_auth_header, params=None
            )
