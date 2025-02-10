"""Error codes as defined in OGWS-1.txt Appendix A and Section 3.4.

This module defines the HTTP and Gateway error codes used in the OGWS protocol.
Error codes are grouped into categories:

- HTTP Error Codes (401, 403, 429, 503)
- Gateway Error Codes (24xxx)
- Network Error Codes
- Message Processing Errors

Usage Examples:

    from protocols.ogx.constants import HTTPErrorCode, GatewayErrorCode

    def handle_response(response_code: int, response_data: dict) -> None:
        '''Handle API response codes and errors.'''
        if response_code == HTTPErrorCode.TOO_MANY_REQUESTS:
            # Wait and retry according to Section 3.4.2
            time.sleep(60)
            return

        if response_code == HTTPErrorCode.SERVICE_UNAVAILABLE:
            # Global rate limit hit - Section 3.4
            raise ServiceError("Global rate limit exceeded")

        if response_data.get('ErrorID') == GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED:
            # Section 3.4.2.3 - Message submission rate exceeded
            raise RateLimitError("Message submission rate exceeded")

    def is_auth_error(error_code: HTTPErrorCode) -> bool:
        '''Check if error is authentication related.'''
        return error_code in (
            HTTPErrorCode.UNAUTHORIZED,
            HTTPErrorCode.FORBIDDEN
        )

Implementation Notes from OGWS-1.txt:
    - HTTP 401: Authentication/authorization failure
    - HTTP 403: Not a super account user
    - HTTP 429: Rate limits exceeded per Section 3.4.2
    - HTTP 503: Global limiter triggered per Section 3.4
    - Gateway error 24579: Submit message rate exceeded
    - Gateway error 24581: Status retrieval rate exceeded
    - Gateway error 24582: Invalid message format
    - Gateway error 24583-24585: Token related errors

See Also:
    - Section 3.4: Access Throttling
    - Section 3.4.2: Account Level Request Throttling
    - Appendix A: HTTP Error Codes
"""

from enum import IntEnum


class HTTPErrorCode(IntEnum):
    """HTTP error codes from OGWS-1.txt Appendix A and Section 3.4.

    These codes indicate the overall status of the API request:
    - 200: Success, check ErrorID for possible errors
    - 401: Authentication or authorization failed
    - 403: Insufficient permissions (not super user)
    - 429: Rate limits exceeded
    - 503: Service-wide rate limit exceeded

    Usage:
        def should_retry(status_code: HTTPErrorCode) -> bool:
            '''Determine if request should be retried based on error.'''
            return status_code in (
                HTTPErrorCode.TOO_MANY_REQUESTS,
                HTTPErrorCode.SERVICE_UNAVAILABLE
            )
    """

    SUCCESS = 200  # Check ErrorID for possible errors
    UNAUTHORIZED = 401  # Authentication/authorization failure
    FORBIDDEN = 403  # Not a super account user
    TOO_MANY_REQUESTS = 429  # Rate limits exceeded
    SERVICE_UNAVAILABLE = 503  # Global limiter triggered


class GatewayErrorCode(IntEnum):
    """Gateway-specific error codes from OGWS-1.txt Section 3.4.

    These codes provide detailed error information when HTTP status is 200:
    - 24579: Message submission rate exceeded (Section 3.4.2.3)
    - 24581: Status retrieval rate exceeded (Section 3.4.2.4)
    - 24582: Message format invalid
    - 24583-24585: Token errors

    Usage:
        def is_rate_limit_error(error_id: GatewayErrorCode) -> bool:
            '''Check if error is rate limit related.'''
            return error_id in (
                GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED,
                GatewayErrorCode.RETRIEVE_STATUS_RATE_EXCEEDED
            )

    Rate Limit Notes:
        - Submit rate limits configurable per account (Section 3.4.2.3)
        - Status retrieval limits configurable per account (Section 3.4.2.4)
        - Default window is 60 seconds (Section 3.4.2.1)
    """

    INVALID_MESSAGE_FORMAT = 24582
    TOKEN_EXPIRED = 24583
    TOKEN_INVALID = 24584
    TOKEN_REVOKED = 24585

    # Validation specific codes
    INVALID_FIELD_TYPE = 24590
    INVALID_FIELD_VALUE = 24591
    INVALID_FIELD_FORMAT = 24592
    MISSING_REQUIRED_FIELD = 24593
    SUBMIT_MESSAGE_RATE_EXCEEDED = 24579
    RETRIEVE_STATUS_RATE_EXCEEDED = 24581
