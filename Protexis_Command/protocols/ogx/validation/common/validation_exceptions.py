"""Validation exceptions for OGx protocol."""

from typing import Optional, cast

from Protexis_Command.protocols.ogx.constants.http_error_codes import HTTPErrorCode
from Protexis_Command.protocols.ogx.constants.ogx_error_codes import GatewayErrorCode


class OGxProtocolError(Exception):
    """Base exception for OGx protocol errors."""

    def __init__(self, message: str, error_code: Optional[GatewayErrorCode] = None):
        """Initialize protocol error.

        Args:
            message: Error message
            error_code: Optional error code
        """
        super().__init__(message)
        self.error_code = error_code


class ProtocolError(OGxProtocolError):
    """Protocol errors using codes from OGx-1.txt."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        """Initialize protocol error.

        Args:
            message: Error message
            error_code: Optional error code
        """
        gateway_error = (
            GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED
            if error_code is None
            else cast(GatewayErrorCode, error_code)
        )
        formatted_message = f"Protocol error: {message}"
        super().__init__(formatted_message, gateway_error)


class ValidationError(OGxProtocolError):
    """Base validation error."""

    def __init__(self, message: str, error_code: Optional[GatewayErrorCode] = None):
        """Initialize validation error.

        Args:
            message: Error message
            error_code: Optional error code
        """
        super().__init__(
            f"Validation error: {message}", error_code or GatewayErrorCode.VALIDATION_ERROR
        )


class NetworkValidationError(ValidationError):
    """Network validation error."""

    def __init__(self, message: str):
        """Initialize network validation error.

        Args:
            message: Error message
        """
        super().__init__(message, GatewayErrorCode.INVALID_MESSAGE_FORMAT)


class SizeValidationError(ValidationError):
    """Size validation error."""

    def __init__(
        self, message: str, current_size: Optional[int] = None, max_size: Optional[int] = None
    ):
        """Initialize size validation error.

        Args:
            message: Error message
            current_size: Current size that exceeded limit
            max_size: Maximum allowed size
        """
        super().__init__(message, GatewayErrorCode.MESSAGE_SIZE_EXCEEDED)
        self.current_size = current_size
        self.max_size = max_size


class TransportValidationError(ValidationError):
    """Transport validation error."""

    def __init__(self, message: str):
        """Initialize transport validation error.

        Args:
            message: Error message
        """
        super().__init__(message, GatewayErrorCode.INVALID_MESSAGE_FORMAT)


class AuthenticationError(OGxProtocolError):
    """Authentication error with HTTP 401 code."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        """Initialize authentication error.

        Args:
            message: Error message
            error_code: Optional error code
        """
        http_code = HTTPErrorCode.UNAUTHORIZED if error_code is None else error_code
        formatted_message = f"Authentication error: {message}"
        # Use INVALID_TOKEN as it's the closest authentication-related error code
        super().__init__(formatted_message, cast(GatewayErrorCode, GatewayErrorCode.INVALID_TOKEN))
        self._original_message = message  # Override the original message after super().__init__
        self.http_code = http_code  # Store HTTP code separately


class RateLimitError(OGxProtocolError):
    """Rate limit error with HTTP 429 code."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        """Initialize rate limit error.

        Args:
            message: Error message
            error_code: Optional error code
        """
        http_code = HTTPErrorCode.TOO_MANY_REQUESTS if error_code is None else error_code
        formatted_message = f"Rate limit error: {message}"
        super().__init__(
            formatted_message, cast(GatewayErrorCode, GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED)
        )
        self._original_message = message  # Override the original message after super().__init__
        self.http_code = http_code  # Store HTTP code separately


__all__ = [
    "OGxProtocolError",
    "ProtocolError",
    "ValidationError",
    "NetworkValidationError",
    "SizeValidationError",
    "TransportValidationError",
    "AuthenticationError",
    "RateLimitError",
]
