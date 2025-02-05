"""
MTBP Protocol Exceptions

Based on IGWS2 error codes and categories from N210 IGWS2 User Guide Section 4.2 and Appendix B.
"""


class MTBPError(Exception):
    """Base exception for MTBP protocol errors"""

    def __init__(self, message: str, error_code: int | None = None):
        self.error_code = error_code
        super().__init__(message)


class ParseError(MTBPError):
    """Message parsing errors (N210 IGWS2 Section 4.2)

    Error codes:
    3 - Invalid message format - Message format is invalid or cannot be parsed
    4 - Invalid SIN value - Service Identification Number is not valid
    5 - Invalid MIN value - Message Identification Number is not valid
    6 - Invalid field type - Field type specified in message is not valid
    7 - Invalid field value - Field value specified in message is not valid
    8 - Missing required field - Required field is missing from message
    9 - Invalid message size - Message size exceeds maximum allowed
    10 - Invalid checksum - Message checksum validation failed
    11 - Unsupported message version - Message version is not supported
    12 - Message decoding failed - Unable to decode message content
    13 - Invalid message structure - Message structure does not match specification
    14 - Message validation failed - Message failed validation rules
    15 - Invalid sequence number - Invalid sequence number in message
    """

    INVALID_FORMAT = 3
    INVALID_SIN = 4
    INVALID_MIN = 5
    INVALID_FIELD_TYPE = 6
    INVALID_FIELD_VALUE = 7
    MISSING_FIELD = 8
    INVALID_SIZE = 9
    INVALID_CHECKSUM = 10
    UNSUPPORTED_VERSION = 11
    DECODE_FAILED = 12
    INVALID_STRUCTURE = 13
    VALIDATION_FAILED = 14
    INVALID_SEQUENCE = 15


class ValidationError(MTBPError):
    """Message validation errors (N210 IGWS2 Section 4.2)

    Error codes:
    17 - Invalid timestamp format - Timestamp format in message is invalid
    23 - Invalid input data - Input data format or content is invalid
    50 - Invalid terminal ID - Mobile ID or terminal identifier is invalid
    51 - Invalid message priority - Message priority level is not valid
    52 - Invalid destination ID - Destination identifier is not valid
    53 - Invalid source ID - Source identifier is not valid
    """

    INVALID_TIMESTAMP_FORMAT = 17
    INVALID_INPUT_DATA = 23
    INVALID_TERMINAL_ID = 50
    INVALID_MESSAGE_PRIORITY = 51
    INVALID_DESTINATION_ID = 52
    INVALID_SOURCE_ID = 53


class FormatError(MTBPError):
    """Message format errors (N210 IGWS2 Section 4.2)

    Error codes:
    115 - Invalid message format - Message format does not comply with specification
    116 - Invalid message content - Message content cannot be processed
    117 - Message too large - Message size exceeds maximum allowed length
    118 - Invalid message type - Message type is not supported or invalid
    """

    INVALID_MESSAGE_FORMAT = 115
    INVALID_MESSAGE_CONTENT = 116
    MESSAGE_TOO_LARGE = 117
    INVALID_MESSAGE_TYPE = 118


class MTBPSystemError(MTBPError):
    """System-level errors (N210 IGWS2 Section 4.2)

    Error codes:
    200 - Internal system error - General system error occurred
    201 - Database error - Error accessing or updating database
    202 - Network error - Network communication error
    203 - Service unavailable - Required service is temporarily unavailable
    """

    INTERNAL_ERROR = 200
    DATABASE_ERROR = 201
    NETWORK_ERROR = 202
    SERVICE_UNAVAILABLE = 203


class TransmissionError(MTBPError):
    """Transmission-related errors (N210 IGWS2 Appendix B.1)"""

    TRANSMISSION_FAILED = 30  # Message transmission failed
    NETWORK_CONGESTION = 31  # Network congestion or capacity issues
    SIGNAL_LOST = 32  # Signal lost during transmission
    TERMINAL_UNREACHABLE = 33  # Terminal cannot be reached
    TRANSPORT_UNAVAILABLE = 34  # Selected transport is unavailable
    BANDWIDTH_EXCEEDED = 35  # Bandwidth limit exceeded
    TERMINAL_BUSY = 36  # Terminal busy or processing other messages


class QueueError(MTBPError):
    """Queue management errors (N210 IGWS2 Appendix B.2)"""

    QUEUE_FULL = 40  # Message queue is full
    PRIORITY_INVALID = 41  # Invalid message priority for queue
    QUEUE_DISABLED = 42  # Queue is temporarily disabled
    MESSAGE_EXPIRED = 43  # Message expired in queue
    DUPLICATE_MESSAGE = 44  # Duplicate message detected
    QUEUE_SUSPENDED = 45  # Queue operations suspended


class PowerError(MTBPError):
    """Power management errors (N210 IGWS2 Appendix B.3)"""

    LOW_BATTERY = 60  # Terminal battery too low
    POWER_MODE_INVALID = 61  # Invalid power mode transition
    WAKE_SCHEDULE_ERROR = 62  # Wake schedule configuration error
    POWER_SAVING_ACTIVE = 63  # Terminal in power saving mode
    CHARGING_REQUIRED = 64  # Terminal requires charging


class RoutingError(MTBPError):
    """Routing and delivery errors (N210 IGWS2 Appendix B.4)"""

    NO_ROUTE_AVAILABLE = 70  # No valid route to terminal
    ROUTE_EXPIRED = 71  # Route information expired
    DELIVERY_FAILED = 72  # Message delivery failed
    ROUTE_INVALID = 73  # Invalid or corrupted route
    TRANSPORT_MISMATCH = 74  # Transport type mismatch
    ROUTING_DISABLED = 75  # Routing temporarily disabled


class SecurityError(MTBPError):
    """Security-related errors (N210 IGWS2 Appendix B.5)"""

    AUTHENTICATION_FAILED = 80  # Authentication failed
    UNAUTHORIZED_ACCESS = 81  # Unauthorized access attempt
    ENCRYPTION_FAILED = 82  # Message encryption failed
    CERTIFICATE_INVALID = 83  # Invalid security certificate
    KEY_EXPIRED = 84  # Security key expired
    SECURITY_VIOLATION = 85  # Security policy violation


class ResourceError(MTBPError):
    """Resource management errors (N210 IGWS2 Appendix B.6)"""

    MEMORY_FULL = 90  # Insufficient memory
    CPU_OVERLOAD = 91  # Processing capacity exceeded
    RESOURCE_UNAVAILABLE = 92  # Required resource unavailable
    STORAGE_FULL = 93  # Storage capacity exceeded
    RESOURCE_TIMEOUT = 94  # Resource access timeout
    RESOURCE_LOCKED = 95  # Resource temporarily locked


class ProtocolError(MTBPError):
    """Protocol-specific errors (N210 IGWS2 Appendix B.7)"""

    VERSION_MISMATCH = 100  # Protocol version mismatch
    SEQUENCE_ERROR = 101  # Message sequence error
    HANDSHAKE_FAILED = 102  # Protocol handshake failed
    PROTOCOL_TIMEOUT = 103  # Protocol operation timeout
    SYNC_ERROR = 104  # Synchronization error
    PROTOCOL_VIOLATION = 105  # Protocol rule violation
