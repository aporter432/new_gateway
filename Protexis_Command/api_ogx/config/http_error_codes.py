"""HTTP error codes for OGx API as defined in OGx-1.txt Appendix A.

This module defines the HTTP error codes used in the OGx API.
These codes indicate the overall status of API requests.

Implementation Notes from OGx-1.txt:
    - HTTP 401: Authentication/authorization failure
    - HTTP 403: Not a super account user
    - HTTP 429: Rate limits exceeded per Section 3.4.2
    - HTTP 503: Global limiter triggered per Section 3.4
"""

from enum import IntEnum


class HTTPErrorCode(IntEnum):
    """HTTP error codes from OGx-1.txt Appendix A and Section 3.4.

    These codes indicate the overall status of the API request:
    - 200: Success, check ErrorID for possible errors
    - 401: Authentication or authorization failed
    - 403: Insufficient permissions (not super user)
    - 429: Rate limits exceeded
    - 503: Service-wide rate limit exceeded
    """

    SUCCESS = 200  # Check ErrorID for possible errors
    UNAUTHORIZED = 401  # Authentication/authorization failure
    FORBIDDEN = 403  # Not a super account user
    TOO_MANY_REQUESTS = 429  # Rate limits exceeded
    SERVICE_UNAVAILABLE = 503  # Global limiter triggered
