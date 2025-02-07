"""Base API client for making authenticated requests to OGWS.

This module provides:
- Automatic token management
- Request authentication
- Error handling
- Rate limiting
"""

from typing import Any, Dict, Optional

import httpx
from httpx import Response

from core.app_settings import Settings
from core.security import OGWSAuthManager
from protocols.ogx.constants import HTTPError


class BaseAPIClient:
    """Base client for making authenticated requests to OGWS."""

    def __init__(self, auth_manager: OGWSAuthManager, settings: Settings):
        """Initialize API client.

        Args:
            auth_manager: Authentication manager for token handling
            settings: Application settings
        """
        self.auth_manager = auth_manager
        self.settings = settings
        self.base_url = settings.OGWS_BASE_URL

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Response:
        """Make authenticated GET request.

        Args:
            endpoint: API endpoint path
            params: Optional query parameters

        Returns:
            Response from the API

        Raises:
            HTTPError: If request fails
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
            HTTPError: If request fails
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
            Parsed response data

        Raises:
            HTTPError: If response contains an error
        """
        data = response.json()

        # Check for API-level errors even with 200 status
        if "ErrorID" in data and data["ErrorID"] != 0:
            raise HTTPError(f"API error: {data.get('ErrorMessage', 'Unknown error')}")

        return data
