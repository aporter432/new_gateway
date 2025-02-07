"""HTTP error codes for OGWS API.

This module defines the HTTP error codes returned by OGWS API endpoints.

Usage:
    from protocols.ogx.constants import HTTPError
    
    if response.status_code == HTTPError.TOO_MANY_REQUESTS:
        # Handle rate limiting
"""

from enum import IntEnum


class HTTPError(IntEnum):
    """HTTP error codes returned by OGWS API."""

    OK = 200
    UNAUTHORIZED = 401  # Authentication/authorization failed
    FORBIDDEN = 403  # Not a super account user
    TOO_MANY_REQUESTS = 429  # Rate limit exceeded
