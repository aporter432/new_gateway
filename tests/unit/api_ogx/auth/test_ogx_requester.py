"""Unit tests for OGx requester authentication module."""

from unittest.mock import Mock

import httpx
import pytest

from Protexis_Command.api.common.auth.ogx_requester import OGxRequester
from Protexis_Command.api.config.ogx_endpoints import APIEndpoint


@pytest.fixture
def mock_auth_manager(mocker):
    """Mock OGxAuthManager for testing."""
    manager = mocker.Mock()
    # Make get_auth_header a coroutine that returns the header
    manager.get_auth_header = mocker.AsyncMock(return_value={"Authorization": "Bearer test_token"})
    return manager


@pytest.fixture
def mock_http_client(mocker):
    """Mock httpx AsyncClient."""
    client = mocker.Mock()
    client.request = mocker.AsyncMock()
    return client


@pytest.fixture
def ogx_requester(mock_auth_manager, mock_http_client, mocker):
    """Create OGxRequester with mocked dependencies."""
    mocker.patch("httpx.AsyncClient", return_value=mock_http_client)
    return OGxRequester(auth_manager=mock_auth_manager)


@pytest.mark.unit
def test_ogx_requester_initialization(mock_auth_manager):
    """Test OGxRequester initialization."""
    requester = OGxRequester(auth_manager=mock_auth_manager)
    assert requester.auth_manager == mock_auth_manager


@pytest.mark.unit
async def test_get_request_success(ogx_requester, mock_http_client):
    """Test successful GET request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_http_client.request.return_value = mock_response

    endpoint = next(iter(APIEndpoint))  # Get first available endpoint
    response = await ogx_requester.get(endpoint)

    mock_http_client.request.assert_called_once_with(
        "GET", endpoint.value, headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200


@pytest.mark.unit
async def test_post_request_success(ogx_requester, mock_http_client):
    """Test successful POST request."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_http_client.request.return_value = mock_response

    endpoint = next(iter(APIEndpoint))  # Get first available endpoint
    test_data = {"key": "value"}

    response = await ogx_requester.post(endpoint, json=test_data)

    mock_http_client.request.assert_called_once_with(
        "POST", endpoint.value, headers={"Authorization": "Bearer test_token"}, json=test_data
    )
    assert response.status_code == 201


@pytest.mark.unit
async def test_request_with_custom_headers(ogx_requester, mock_http_client):
    """Test request with additional custom headers."""
    custom_headers = {"Custom-Header": "test_value"}
    mock_response = Mock()
    mock_http_client.request.return_value = mock_response

    endpoint = next(iter(APIEndpoint))  # Get first available endpoint
    await ogx_requester.get(endpoint, headers=custom_headers)

    expected_headers = {"Authorization": "Bearer test_token", "Custom-Header": "test_value"}
    mock_http_client.request.assert_called_once_with(
        "GET", endpoint.value, headers=expected_headers
    )


@pytest.mark.unit
async def test_request_error_handling(ogx_requester, mock_http_client):
    """Test handling of request errors."""
    mock_http_client.request.side_effect = httpx.RequestError("Connection failed")
    endpoint = next(iter(APIEndpoint))  # Get first available endpoint

    with pytest.raises(httpx.RequestError) as exc_info:
        await ogx_requester.get(endpoint)
    assert "Connection failed" in str(exc_info.value)


@pytest.mark.unit
async def test_auth_header_refresh(ogx_requester, mock_auth_manager, mock_http_client):
    """Test that auth header is fetched for each request."""
    mock_response = Mock()
    mock_http_client.request.return_value = mock_response
    endpoint = next(iter(APIEndpoint))  # Get first available endpoint

    await ogx_requester.get(endpoint)
    await ogx_requester.post(endpoint)

    assert mock_auth_manager.get_auth_header.call_count == 2


@pytest.mark.unit
async def test_put_request_success(ogx_requester, mock_http_client):
    """Test successful PUT request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_http_client.request.return_value = mock_response

    endpoint = next(iter(APIEndpoint))
    test_data = {"key": "updated_value"}

    response = await ogx_requester.put(endpoint, json=test_data)

    mock_http_client.request.assert_called_once_with(
        "PUT", endpoint.value, headers={"Authorization": "Bearer test_token"}, json=test_data
    )
    assert response.status_code == 200


@pytest.mark.unit
async def test_delete_request_success(ogx_requester, mock_http_client):
    """Test successful DELETE request."""
    mock_response = Mock()
    mock_response.status_code = 204
    mock_http_client.request.return_value = mock_response

    endpoint = next(iter(APIEndpoint))
    response = await ogx_requester.delete(endpoint)

    mock_http_client.request.assert_called_once_with(
        "DELETE", endpoint.value, headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 204
