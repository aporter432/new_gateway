"""OGx protocol exceptions as defined in N214 specification"""

from typing import Optional


class OGxProtocolError(Exception):
    """Base exception for all OGx protocol errors"""

    def __init__(self, message: str, error_code: Optional[int] = None):
        self.error_code = error_code
        super().__init__(message)


class ProtocolError(OGxProtocolError):
    """Protocol-level errors from Section 2 of N214 specification"""

    # Protocol-specific errors
    ERR_SUBMIT_MESSAGE_RATE_EXCEEDED = 24579  # Rate limit exceeded for message submission
    ERR_RETRIEVE_STATUS_RATE_EXCEEDED = 24581  # Rate limit exceeded for status retrieval
    ERR_NDN_INVALID_BEAM = 12308  # Invalid beam number in delivery notification

    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(f"Protocol error: {message}", error_code)


class MessageFormatError(OGxProtocolError):
    """Raised when message format violates protocol requirements"""

    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(f"Message format error: {message}", error_code)


class FieldFormatError(OGxProtocolError):
    """Raised when field format violates protocol requirements"""

    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(f"Field format error: {message}", error_code)


class ElementFormatError(OGxProtocolError):
    """Raised when element format violates protocol requirements"""

    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(f"Element format error: {message}", error_code)


class ValidationError(OGxProtocolError):
    """Raised when message validation fails"""

    MISSING_REQUIRED_FIELD = 1001
    INVALID_FIELD_TYPE = 1002
    INVALID_FIELD_VALUE = 1003
    DUPLICATE_FIELD_NAME = 1004
    INVALID_ELEMENT_INDEX = 1005
    FIELD_VALUE_AND_ELEMENTS = 1006  # When field has both value and elements
    INVALID_MESSAGE_FORMAT = 1007
    INVALID_FIELD_FORMAT = 1008
    INVALID_ELEMENT_FORMAT = 1009

    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(f"Validation error: {message}", error_code)


class EncodingError(OGxProtocolError):
    """Raised when message encoding/decoding fails"""

    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(f"Encoding error: {message}", error_code)
