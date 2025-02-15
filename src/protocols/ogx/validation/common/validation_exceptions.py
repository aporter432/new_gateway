"""OGx protocol exceptions using error codes defined in OGWS-1.txt."""

# ruff: noqa: E501
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name

from typing import Any, Dict, Optional

from ...constants.error_codes import GatewayErrorCode, HTTPErrorCode


class OGxProtocolError(Exception):
    """Base exception for all OGx protocol errors."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        self._original_message = message  # Store original message before any formatting
        super().__init__(message)
        self.error_code = error_code

    def __str__(self) -> str:
        return str(self.args[0])

    def __repr__(self) -> str:
        args = [repr(self._original_message)]
        if self.error_code is not None:
            args.append(str(self.error_code))
        elif self.__class__ == OGxProtocolError:  # Only include None for base class
            args.append("None")
        return f"{self.__class__.__name__}({', '.join(args)})"

    def __reduce__(self):
        """Support pickling by preserving the original message."""
        return (self.__class__, (self._original_message, self.error_code))


class ProtocolError(OGxProtocolError):
    """Protocol errors using codes from OGWS-1.txt."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        self._original_message = message  # Store original message before formatting
        error_code = error_code or GatewayErrorCode.SUBMIT_MESSAGE_RATE_EXCEEDED
        formatted_message = f"Protocol error: {message}"
        super().__init__(formatted_message, error_code)
        self._original_message = (
            message  # Ensure original message is preserved after super().__init__
        )


class ValidationError(Exception):
    """Base validation exception class.

    All validation errors will include a 'Validation error:' prefix in their string representation
    and default to GatewayErrorCode.VALIDATION_ERROR if no specific error code is provided.

    Examples:
        >>> err = ValidationError("Invalid format")
        >>> str(err)
        'Validation error: Invalid format'
        >>> err.error_code
        GatewayErrorCode.VALIDATION_ERROR
    """

    def __init__(
        self,
        message: str,
        error_code: GatewayErrorCode = GatewayErrorCode.VALIDATION_ERROR,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._original_message = message
        self.message = message
        super().__init__(message)
        self.error_code = error_code
        self.cause = cause
        self.details = details or {}
        if cause:
            self.__cause__ = cause

    def __str__(self) -> str:
        """Return formatted error message with prefix and optional details."""
        base_msg = f"Validation error: {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base_msg} ({details_str})"
        return base_msg

    def __repr__(self) -> str:
        args = [repr(self._original_message)]
        args.append(str(self.error_code.value))  # Always include error code
        return f"{self.__class__.__name__}({', '.join(args)})"


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
        base_msg = f"Validation error: {self.message}"
        if self.context:
            return f"{base_msg} (Context: {self.context})"
        return base_msg


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
            element_index: Index of the invalid element
            context: Additional context about where error occurred
        """
        super().__init__(message, GatewayErrorCode.INVALID_ELEMENT_FORMAT)
        self.element_index = element_index
        self.context = context

    def __str__(self) -> str:
        parts = [f"Validation error: {self.message}"]
        if self.element_index is not None:
            parts.append(f"at index {self.element_index}")
        if self.context:
            parts.append(f"({self.context})")
        return " ".join(parts)


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
        base_msg = f"Validation error: {self.message}"
        if self.field_name:
            return f"{base_msg} in field '{self.field_name}'"
        return base_msg


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
            filter_details: Additional details about the filter error
        """
        super().__init__(message, GatewayErrorCode.INVALID_MESSAGE_FILTER)
        self.filter_details = filter_details

    def __str__(self) -> str:
        base_msg = f"Validation error: {self.message}"
        if self.filter_details:
            return f"{base_msg} ({self.filter_details})"
        return base_msg


class SizeValidationError(ValidationError):
    """Validation error for size limits."""

    def __init__(
        self,
        message: str,
        current_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> None:
        """Initialize size validation error.

        Args:
            message: Error message
            current_size: Current size that exceeded limit
            max_size: Maximum allowed size
        """
        super().__init__(message, GatewayErrorCode.MESSAGE_SIZE_EXCEEDED)
        self.current_size = current_size
        self.max_size = max_size

    def __str__(self) -> str:
        base_msg = f"Validation error: {self.message}"
        if self.current_size is not None and self.max_size is not None:
            return f"{base_msg} (size: {self.current_size}, max: {self.max_size})"
        return base_msg


class AuthenticationError(OGxProtocolError):
    """Authentication error with HTTP 401 code."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        error_code = error_code or HTTPErrorCode.UNAUTHORIZED
        formatted_message = f"Authentication error: {message}"
        super().__init__(formatted_message, error_code)
        self._original_message = message  # Override the original message after super().__init__

    def __repr__(self) -> str:
        args = [repr(self._original_message)]
        if self.error_code is not None:
            args.append(str(self.error_code))
        return f"{self.__class__.__name__}({', '.join(args)})"


class EncodingError(OGxProtocolError):
    """Encoding error with ENCODE_ERROR code.

    All encoding errors will include an 'Encoding error:' prefix and default to
    GatewayErrorCode.ENCODE_ERROR if no specific error code is provided.

    Examples:
        >>> err = EncodingError("Malformed JSON")
        >>> str(err)
        'Encoding error: Malformed JSON'
        >>> err.error_code
        GatewayErrorCode.ENCODE_ERROR
    """

    def __init__(self, message: str, error_code: Optional[int] = None):
        """Initialize encoding error.

        Args:
            message: Error message
            error_code: Optional error code. Defaults to ENCODE_ERROR if not provided.
        """
        self._original_message = message
        formatted_message = f"Encoding error: {message}"
        error_code = error_code or GatewayErrorCode.ENCODE_ERROR
        super().__init__(formatted_message, error_code)
        self._original_message = message

    def __repr__(self) -> str:
        args = [repr(self._original_message)]
        if self.error_code is not None:
            args.append(str(self.error_code))
        return f"{self.__class__.__name__}({', '.join(args)})"


class RateLimitError(OGxProtocolError):
    """Rate limit error with HTTP 429 code."""

    def __init__(self, message: str, error_code: Optional[int] = None):
        error_code = error_code or HTTPErrorCode.TOO_MANY_REQUESTS
        formatted_message = f"Rate limit error: {message}"
        super().__init__(formatted_message, error_code)
        self._original_message = message  # Override the original message after super().__init__

    def __repr__(self) -> str:
        args = [repr(self._original_message)]
        if self.error_code is not None:
            args.append(str(self.error_code))
        return f"{self.__class__.__name__}({', '.join(args)})"
