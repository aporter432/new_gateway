"""Mock responses for integration tests.

This module provides mock responses for integration tests.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from httpx import Request, Response


@dataclass
class OGxMockResponse:
    """Standard structure for OGx mock responses."""

    status_code: int
    body: Dict[str, Any]
    headers: Dict[str, str]
    request: Optional[Request] = None

    def to_response(self) -> Response:
        """Convert to httpx Response object."""
        return Response(
            status_code=self.status_code,
            json=self.body,
            headers=self.headers,
            request=self.request or Request("GET", "https://OGx.swlab.ca/api/v1.0/"),
        )


class OGxMockResponses:
    """Collection of standard OGx mock responses."""

    BASE_URL = "https://OGx.swlab.ca/api/v1.0"

    @staticmethod
    def token_success(token: str = "test_token", expires_in: int = 3600) -> Response:
        """Create a successful token response."""
        return OGxMockResponse(
            status_code=200,
            body={"access_token": token, "expires_in": expires_in, "token_type": "Bearer"},
            headers={"Content-Type": "application/json"},
            request=Request("POST", f"{OGxMockResponses.BASE_URL}/token"),
        ).to_response()

    @staticmethod
    def token_invalid_credentials() -> Response:
        """Create an invalid credentials response."""
        return OGxMockResponse(
            status_code=401,
            body={"error": "invalid_client", "error_description": "Invalid client credentials"},
            headers={"Content-Type": "application/json"},
            request=Request("POST", f"{OGxMockResponses.BASE_URL}/token"),
        ).to_response()

    @staticmethod
    def token_expired() -> Response:
        """Create an expired token response."""
        return OGxMockResponse(
            status_code=401,
            body={"error": "invalid_token", "error_description": "Token has expired"},
            headers={"Content-Type": "application/json"},
            request=Request("GET", f"{OGxMockResponses.BASE_URL}/validate"),
        ).to_response()

    @staticmethod
    def validation_success() -> Response:
        """Create a successful validation response."""
        return OGxMockResponse(
            status_code=200,
            body={"valid": True},
            headers={"Content-Type": "application/json"},
            request=Request("GET", f"{OGxMockResponses.BASE_URL}/validate"),
        ).to_response()

    @staticmethod
    def validation_failure() -> Response:
        """Create a failed validation response."""
        return OGxMockResponse(
            status_code=401,
            body={"error": "invalid_token", "error_description": "Token validation failed"},
            headers={"Content-Type": "application/json"},
            request=Request("GET", f"{OGxMockResponses.BASE_URL}/validate"),
        ).to_response()

    @staticmethod
    def rate_limit_exceeded() -> Response:
        """Create a rate limit exceeded response."""
        return OGxMockResponse(
            status_code=429,
            body={
                "error": "too_many_requests",
                "error_description": "Rate limit exceeded",
                "retry_after": 60,
            },
            headers={"Content-Type": "application/json", "Retry-After": "60"},
            request=Request("POST", f"{OGxMockResponses.BASE_URL}/token"),
        ).to_response()
