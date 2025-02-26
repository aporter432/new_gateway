"""OGx API requester module.

This module provides a client for making HTTP requests to OGx API endpoints
with automatic authentication header management.
"""

import logging

import httpx
from httpx import Response

from Protexis_Command.api.common.auth.manager import OGxAuthManager
from Protexis_Command.api.config.ogx_endpoints import APIEndpoint

logger = logging.getLogger(__name__)


class OGxRequester:
    """Client for making authenticated requests to OGx API endpoints."""

    def __init__(self, auth_manager: OGxAuthManager):
        """Initialize the OGx API requester.

        Args:
            auth_manager: Authentication manager for OGx API to handle tokens
        """
        self.auth_manager = auth_manager
        self.client = httpx.AsyncClient(timeout=30.0)  # 30 second timeout

    async def get(self, endpoint: APIEndpoint, **kwargs) -> Response:
        """Make a GET request to an OGx API endpoint.

        Args:
            endpoint: The API endpoint to request
            **kwargs: Additional arguments to pass to the request

        Returns:
            The HTTP response
        """
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: APIEndpoint, **kwargs) -> Response:
        """Make a POST request to an OGx API endpoint.

        Args:
            endpoint: The API endpoint to request
            **kwargs: Additional arguments to pass to the request

        Returns:
            The HTTP response
        """
        return await self._request("POST", endpoint, **kwargs)

    async def put(self, endpoint: APIEndpoint, **kwargs) -> Response:
        """Make a PUT request to an OGx API endpoint.

        Args:
            endpoint: The API endpoint to request
            **kwargs: Additional arguments to pass to the request

        Returns:
            The HTTP response
        """
        return await self._request("PUT", endpoint, **kwargs)

    async def delete(self, endpoint: APIEndpoint, **kwargs) -> Response:
        """Make a DELETE request to an OGx API endpoint.

        Args:
            endpoint: The API endpoint to request
            **kwargs: Additional arguments to pass to the request

        Returns:
            The HTTP response
        """
        return await self._request("DELETE", endpoint, **kwargs)

    async def _request(self, method: str, endpoint: APIEndpoint, **kwargs) -> Response:
        """Make an HTTP request to an OGx API endpoint.

        Args:
            method: HTTP method to use
            endpoint: The API endpoint to request
            **kwargs: Additional arguments to pass to the request

        Returns:
            The HTTP response
        """
        # Get authentication header
        auth_header = await self.auth_manager.get_auth_header()

        # Add authentication to headers
        headers = kwargs.get("headers", {})
        headers.update(auth_header)
        kwargs["headers"] = headers

        # Make the request
        logger.debug(f"Making {method} request to {endpoint.value}")
        try:
            response = await self.client.request(method, endpoint.value, **kwargs)
            logger.debug(f"Response status: {response.status_code}")
            return response
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise
