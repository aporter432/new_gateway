"""OGx protocol exceptions using error codes defined in OGWS-1.txt."""

from typing import Optional

from ...constants.error_codes import GatewayErrorCode, HTTPErrorCode


class OGxProtocolError(Exception):
    """Base exception for all OGx protocol errors."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        self.error_code = error_code
        super().__init__(message)


class ProtocolError(OGxProtocolError):
    """Protocol errors using codes from OGWS-1.txt."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        self.error_code = error_code or GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED
        super().__init__(f"Protocol error: {message}")


class ValidationError(Exception):
    """Validation errors according to OGWS-1.txt Section 5."""

    # Error code references
    INVALID_MESSAGE_FORMAT = GatewayErrorCode.INVALID_MESSAGE_FORMAT
    INVALID_FIELD_TYPE = GatewayErrorCode.INVALID_FIELD_TYPE
    INVALID_FIELD_VALUE = GatewayErrorCode.INVALID_FIELD_VALUE
    INVALID_FIELD_FORMAT = GatewayErrorCode.INVALID_FIELD_FORMAT
    MISSING_REQUIRED_FIELD = GatewayErrorCode.MISSING_REQUIRED_FIELD

    def __init__(self, message: str, error_code: Optional[int] = None):
        self.error_code = error_code or self.INVALID_MESSAGE_FORMAT
        super().__init__(f"Validation error: {message}")


class AuthenticationError(OGxProtocolError):
    """Authentication errors as defined in OGWS-1.txt Section 3.1."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        if error_code is None:
            error_code = HTTPErrorCode.UNAUTHORIZED
        super().__init__(f"Authentication error: {message}", error_code)


class EncodingError(OGxProtocolError):
    """Message encoding/decoding errors according to OGWS-1.txt Section 5."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        if error_code is None:
            error_code = GatewayErrorCode.INVALID_MESSAGE_FORMAT
        super().__init__(f"Encoding error: {message}", error_code)


class RateLimitError(OGxProtocolError):
    """Rate limiting errors as defined in OGWS-1.txt Section 3.4."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        if error_code is None:
            error_code = HTTPErrorCode.TOO_MANY_REQUESTS
        super().__init__(f"Rate limit error: {message}", error_code)
