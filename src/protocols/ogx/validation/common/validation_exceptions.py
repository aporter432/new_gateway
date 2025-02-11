"""OGx protocol exceptions using error codes defined in OGWS-1.txt."""

# ruff: noqa: E501
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name

from typing import Optional, Any, Dict

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
    """Base validation exception class."""

    def __init__(
        self,
        message: str,
        error_code: GatewayErrorCode = GatewayErrorCode.VALIDATION_ERROR,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            error_code: Error code from GatewayErrorCode enum
            cause: Original exception that caused this error
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.cause = cause
        self.details = details or {}
        if cause:
            self.__cause__ = cause  # Explicitly set cause for exception chaining

    def __str__(self) -> str:
        """Return string representation including details if present."""
        msg = self.message
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            msg = f"{msg} ({details_str})"
        return msg


class MessageValidationError(ValidationError):
    """Validation error for messages."""

    def __init__(
        self,
        message: str,
        error_code: GatewayErrorCode = GatewayErrorCode.INVALID_MESSAGE_FORMAT,
        context: Optional[str] = None,
    ) -> None:
        """Initialize message validation error.

        Args:
            message: Error message
            error_code: Error code from GatewayErrorCode enum
            context: Additional context about where error occurred
        """
        super().__init__(message, error_code)
        self.context = context

    def __str__(self) -> str:
        if self.context:
            return f"{self.message} (Context: {self.context})"
        return self.message


class ElementValidationError(ValidationError):
    """Validation error for array elements."""

    def __init__(
        self,
        message: str,
        element_index: Optional[int] = None,
        context: Optional[str] = None,
    ) -> None:
        """Initialize element validation error.

        Args:
            message: Error message
            element_index: Index of element that failed validation
            context: Additional context about where error occurred
        """
        super().__init__(message, GatewayErrorCode.INVALID_ELEMENT_FORMAT)
        self.element_index = element_index
        self.context = context

    def __str__(self) -> str:
        msg = self.message
        if self.context:
            msg = f"{msg} (Context: {self.context})"
        if self.element_index is not None:
            msg = f"{msg} at index {self.element_index}"
        return msg


class FieldValidationError(ValidationError):
    """Validation error for fields."""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
    ) -> None:
        """Initialize field validation error.

        Args:
            message: Error message
            field_name: Name of field that failed validation
        """
        super().__init__(message, GatewayErrorCode.INVALID_FIELD_FORMAT)
        self.field_name = field_name

    def __str__(self) -> str:
        if self.field_name:
            return f"{self.message} in field '{self.field_name}'"
        return self.message


class MessageFilterValidationError(ValidationError):
    """Validation error for message filters."""

    def __init__(
        self,
        message: str,
        filter_details: Optional[str] = None,
    ) -> None:
        """Initialize message filter validation error.

        Args:
            message: Error message
            filter_details: Additional details about filter validation failure
        """
        super().__init__(message, GatewayErrorCode.INVALID_MESSAGE_FILTER)
        self.filter_details = filter_details

    def __str__(self) -> str:
        if self.filter_details:
            return f"{self.message} ({self.filter_details})"
        return self.message


class SizeValidationError(ValidationError):
    """Validation error for message size limits."""

    def __init__(
        self,
        message: str,
        current_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> None:
        """Initialize size validation error.

        Args:
            message: Error message
            current_size: Actual size that exceeded limit
            max_size: Maximum allowed size
        """
        super().__init__(message, GatewayErrorCode.MESSAGE_SIZE_EXCEEDED)
        self.current_size = current_size
        self.max_size = max_size

    def __str__(self) -> str:
        if self.current_size is not None and self.max_size is not None:
            return f"{self.message} (Size: {self.current_size}, Max: {self.max_size})"
        return self.message


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
