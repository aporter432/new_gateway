"""Validation exceptions for OGx protocol."""

from typing import Optional

from Protexis_Command.protocol.ogx.constants.http_error_codes import HTTPErrorCode
from Protexis_Command.protocol.ogx.constants.ogx_error_codes import GatewayErrorCode


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
        error_code = error_code or GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED
        formatted_message = f"Protocol error: {message}"
        super().__init__(formatted_message, error_code)


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
        error_code = error_code or HTTPErrorCode.UNAUTHORIZED
        formatted_message = f"Authentication error: {message}"
        super().__init__(formatted_message, error_code)
        self._original_message = message  # Override the original message after super().__init__


class RateLimitError(OGxProtocolError):
    """Rate limit error with HTTP 429 code."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        """Initialize rate limit error.

        Args:
            message: Error message
            error_code: Optional error code
        """
        error_code = error_code or HTTPErrorCode.TOO_MANY_REQUESTS
        formatted_message = f"Rate limit error: {message}"
        super().__init__(formatted_message, error_code)
        self._original_message = message  # Override the original message after super().__init__


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
