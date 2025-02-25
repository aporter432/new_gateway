"""Base client for OGx API.

This module provides the base client implementation for OGx API interactions.
"""

from typing import Any, Dict, Optional

import httpx
from httpx import Response

from ...api_ogx.services.auth.manager import OGxAuthManager
from ...core.settings.app_settings import Settings
from ...protocol.ogx.constants.http_error_codes import HTTPErrorCode
from ...protocol.ogx.validation.ogx_validation_exceptions import OGxProtocolError


class BaseAPIClient:
    """Base client for making authenticated requests to OGx."""

    def __init__(self, auth_manager: OGxAuthManager, settings: Settings):
        """Initialize API client.

        Args:
            auth_manager: Authentication manager for token handling
            settings: Application settings
        """
        self.auth_manager = auth_manager
        self.settings = settings
        self.base_url = settings.OGx_BASE_URL

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Response:
        """Make authenticated GET request.

        Args:
            endpoint: API endpoint path
            params: Optional query parameters

        Returns:
            Response from the API

        Raises:
            httpx.HTTPError: If request fails
        """
        headers = await self.auth_manager.get_auth_header()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}", headers=headers, params=params
            )
            response.raise_for_status()
            return response

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Make authenticated POST request.

        Args:
            endpoint: API endpoint path
            json_data: Optional JSON request body
            data: Optional form data

        Returns:
            Response from the API

        Raises:
            httpx.HTTPError: If request fails
        """
        headers = await self.auth_manager.get_auth_header()
        if json_data:
            headers["Content-Type"] = "application/json"
        elif data:
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{endpoint}", headers=headers, json=json_data, data=data
            )
            response.raise_for_status()
            return response

    async def handle_response(self, response: Response) -> Dict[str, Any]:
        """Handle API response and check for errors.

        Args:
            response: Response from the API

        Returns:
            Dict[str, Any]: Parsed response data

        Raises:
            OGxProtocolError: If response contains an API-level error
        """
        data: Dict[str, Any] = response.json()

        # Check for API-level errors even with 200 status
        if "ErrorID" in data and data["ErrorID"] != 0:
            if response.status_code == HTTPErrorCode.TOO_MANY_REQUESTS:
                retry_after = data.get("RetryAfter", 60)
                raise OGxProtocolError(f"Rate limit exceeded. Retry after {retry_after} seconds.")
            raise OGxProtocolError(f"API error: {data.get('ErrorMessage', 'Unknown error')}")

        return data
