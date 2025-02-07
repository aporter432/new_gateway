"""HTTP error codes as defined in OGWS-1.txt.

This module defines the HTTP error codes returned by OGWS API endpoints.

HTTP Error Codes (from OGWS-1.txt):
- 200: Success. Check ErrorID in response for possible errors
- 401: Authentication/authorization failure
- 403: Not a super account user ("Forbidden")
- 429: Rate limit exceeded ("Too Many Requests")
- 503: Service-wide limits exceeded ("Service Unavailable")

OGWS API Usage Examples:

    # Example 1: Authentication failure
    # POST https://ogws.orbcomm.com/api/v1.0/auth/token
    response = {
        "status_code": HTTPError.UNAUTHORIZED,
        "error": "Invalid credentials"
    }

    # Example 2: Rate limit exceeded
    # GET https://ogws.orbcomm.com/api/v1.0/get/re_messages
    response = {
        "status_code": HTTPError.TOO_MANY_REQUESTS,
        "error": "Rate limit exceeded. Wait 60 seconds before retrying."
    }

    # Example 3: Subaccount access denied
    # GET https://ogws.orbcomm.com/api/v1.0/get/subaccount/re_messages
    response = {
        "status_code": HTTPError.FORBIDDEN,
        "error": "Account does not have super user privileges"
    }

Implementation Notes from OGWS-1.txt:
    - 200 responses may still contain errors (check ErrorID)
    - 401 indicates invalid/expired token or credentials
    - 403 returned when accessing subaccount endpoints without privileges
    - 429 indicates account-level rate limits exceeded
    - 503 indicates service-wide limits exceeded
    - Rate limits apply per account and throttle group
    - Some limits configurable via Partner Support
    - Retry after delay when receiving 429/503
"""

from enum import IntEnum


class HTTPError(IntEnum):
    """HTTP error codes as defined in OGWS-1.txt.

    Attributes:
        OK (200): Success. Check ErrorID in response for possible errors.
        UNAUTHORIZED (401): Authentication/authorization failed.
        FORBIDDEN (403): Not a super account user.
        TOO_MANY_REQUESTS (429): Rate limit exceeded.
        SERVICE_UNAVAILABLE (503): Service-wide limits exceeded.

    API Response Examples:
        # Rate limit exceeded response
        {
            "status_code": HTTPError.TOO_MANY_REQUESTS,
            "error": "Rate limit exceeded",
            "retry_after": 60
        }

        # Authentication failure response
        {
            "status_code": HTTPError.UNAUTHORIZED,
            "error": "Bearer token expired"
        }
    """

    OK = 200
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    TOO_MANY_REQUESTS = 429
    SERVICE_UNAVAILABLE = 503
