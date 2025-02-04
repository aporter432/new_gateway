"""
OGx field validation according to N214 specification section 5.
Implements field-level validation rules for the Common Message Format.
"""

import base64
import re
from datetime import datetime

# Standard library imports
from typing import Any, Dict

# Local imports
from ..constants import FieldType
from ..exceptions import ValidationError


class OGxFieldValidator:
    """Validates individual OGx fields according to N214 specification section 5"""

    # Field type mappings from Table 3 of N214 spec
    TYPE_ATTRIBUTES: Dict[str, str] = {
        "enum": "enum",
        "boolean": "boolean",
        "unsignedint": "unsignedint",
        "signedint": "signedint",
        "string": "string",
        "data": "data",
        "array": "array",
        "message": "message",
        "dynamic": "(one of above)",
        "property": "(one of above)",
    }

    # Message size limits from Section 2.1
    MAX_SMALL_MESSAGE_SIZE = 100
    MAX_REGULAR_MESSAGE_SIZE = 2000
    MAX_LARGE_MESSAGE_SIZE = 10000

    # UTC timestamp format from Section 2.1
    TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

    def validate_field_value(
        self, field_type: FieldType, value: Any, type_attribute: str | None = None
    ) -> None:
        """
        Validates a field value against its declared type per Table 3 of N214 spec.

        Args:
            field_type: Type of the field from FieldType enum
            value: Value to validate
            type_attribute: Type attribute for dynamic/property fields

        Raises:
            ValidationError: If value doesn't match field type requirements
        """
        try:
            # Handle dynamic and property fields
            if field_type in (FieldType.DYNAMIC, FieldType.PROPERTY):
                if not type_attribute:
                    raise ValidationError(
                        "Type attribute required for dynamic/property fields",
                        ValidationError.INVALID_FIELD_TYPE,
                    )
                if type_attribute not in self.TYPE_ATTRIBUTES:
                    raise ValidationError(
                        f"Invalid type attribute: {type_attribute}",
                        ValidationError.INVALID_FIELD_TYPE,
                    )
                # Validate against the specified type
                return self.validate_field_value(
                    FieldType(self.TYPE_ATTRIBUTES[type_attribute]), value
                )

            if field_type == FieldType.BOOLEAN:
                if not isinstance(value, bool):
                    raise ValueError("Boolean value must be true or false")

            elif field_type == FieldType.UNSIGNED_INT:
                int_val = int(value)
                if int_val < 0:
                    raise ValueError("Decimal number must be non-negative")

            elif field_type == FieldType.SIGNED_INT:
                int(value)  # Validate it's a decimal number

            elif field_type == FieldType.STRING:
                if not isinstance(value, str):
                    raise ValueError("Value must be a string")

            elif field_type == FieldType.DATA:
                if isinstance(value, str):
                    self.validate_base64(value)  # Enhanced base64 validation
                elif not isinstance(value, bytes):
                    raise ValueError("Data must be base64 string or bytes")

            elif field_type == FieldType.ENUM:
                if not isinstance(value, str):
                    raise ValueError("Enumeration value must be a string")

            elif field_type == FieldType.ARRAY:
                if value is not None:  # Array can be None per Table 3
                    if not isinstance(value, list):
                        raise ValueError("Array value must be a list or None")

            elif field_type == FieldType.MESSAGE:
                if value is not None:  # Message can be None per Table 3
                    if not isinstance(value, dict):
                        raise ValueError("Message value must be a dictionary or None")

            else:
                raise ValidationError(
                    f"Unknown field type: {field_type}", ValidationError.INVALID_FIELD_TYPE
                )

        except (TypeError, ValueError) as exc:
            raise ValidationError(
                f"Invalid value for field type {field_type}: {value}",
                ValidationError.INVALID_FIELD_VALUE,
            ) from exc

    def validate_message_size(self, message_data: bytes, message_class: str) -> None:
        """
        Validates message size limits according to Section 2.1 of N214 spec.

        Args:
            message_data: Raw message data in bytes
            message_class: Message size class ('small', 'regular', or 'large')

        Raises:
            ValidationError: If message size exceeds limit for its class
        """
        size = len(message_data)
        if message_class == "small" and size > self.MAX_SMALL_MESSAGE_SIZE:
            raise ValidationError(
                f"Small message exceeds {self.MAX_SMALL_MESSAGE_SIZE} byte limit",
                ValidationError.INVALID_MESSAGE_FORMAT,
            )
        elif message_class == "regular" and size > self.MAX_REGULAR_MESSAGE_SIZE:
            raise ValidationError(
                f"Regular message exceeds {self.MAX_REGULAR_MESSAGE_SIZE} byte limit",
                ValidationError.INVALID_MESSAGE_FORMAT,
            )
        elif message_class == "large" and size > self.MAX_LARGE_MESSAGE_SIZE:
            raise ValidationError(
                f"Large message exceeds {self.MAX_LARGE_MESSAGE_SIZE} byte limit",
                ValidationError.INVALID_MESSAGE_FORMAT,
            )

    def validate_terminal_id(self, terminal_id: str) -> None:
        """
        Validates terminal ID format according to Section 4.2 of N214 spec.

        Args:
            terminal_id: Terminal ID to validate

        Raises:
            ValidationError: If terminal ID format is invalid
        """
        if not re.match(r"^[0-9A-F]{12}$", terminal_id):
            raise ValidationError(
                "Invalid terminal ID format - must be 12 hexadecimal characters",
                ValidationError.INVALID_FIELD_FORMAT,
            )

    def validate_mac_address(self, mac: str) -> None:
        """
        Validates MAC address format.

        Args:
            mac: MAC address to validate

        Raises:
            ValidationError: If MAC address format is invalid
        """
        if not re.match(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$", mac):
            raise ValidationError(
                "Invalid MAC address format - must be XX:XX:XX:XX:XX:XX hexadecimal",
                ValidationError.INVALID_FIELD_FORMAT,
            )

    def validate_satellite_network(self, network: int) -> None:
        """
        Validates satellite network value.

        Args:
            network: Network value to validate (0-IsatData Pro, 1-OGx)

        Raises:
            ValidationError: If network value is invalid
        """
        if network not in (0, 1):
            raise ValidationError(
                "Invalid satellite network value - must be 0 (IsatData Pro) or 1 (OGx)",
                ValidationError.INVALID_FIELD_VALUE,
            )

    def validate_base64(self, value: str) -> None:
        """
        Enhanced base64 validation with padding check.

        Args:
            value: Base64 string to validate

        Raises:
            ValidationError: If base64 encoding or padding is invalid
        """
        try:
            decoded = base64.b64decode(value)
            # Check if the decoded value can be properly re-encoded
            if base64.b64encode(decoded).decode() != value:
                raise ValidationError(
                    "Invalid base64 padding",
                    ValidationError.INVALID_FIELD_FORMAT,
                )
        except Exception as exc:
            raise ValidationError(
                "Invalid base64 encoding",
                ValidationError.INVALID_FIELD_FORMAT,
            ) from exc

    def validate_timestamp(self, timestamp: str) -> None:
        """
        Validates UTC timestamp format according to Section 2.1 of N214 spec.
        Format: YYYY-MM-DD hh:mm:ss
        where:
        YYYY - year (4 digits)
        MM - month (01-12)
        DD - day (01-31)
        hh - hour (00-23)
        mm - minutes (00-59)
        ss - seconds (00-59)

        Args:
            timestamp: UTC timestamp to validate

        Raises:
            ValidationError: If timestamp format is invalid
        """
        try:
            datetime.strptime(timestamp, self.TIMESTAMP_FORMAT)
        except ValueError as exc:
            raise ValidationError(
                "Invalid UTC timestamp format - must be YYYY-MM-DD hh:mm:ss",
                ValidationError.INVALID_FIELD_FORMAT,
            ) from exc

    def validate_message_name(self, name: str) -> None:
        """
        Validates message name format.
        Must be non-empty string matching terminal message definition.

        Args:
            name: Message name to validate

        Raises:
            ValidationError: If message name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError(
                "Message name must be a non-empty string",
                ValidationError.INVALID_FIELD_FORMAT,
            )

    def validate_sin_min(self, sin: int, min_id: int) -> None:
        """
        Validates Service Identification Number (SIN) and
        Message Identification Number (MIN) combination.
        Must be non-negative integers matching terminal message definition.

        Args:
            sin: Service Identification Number
            min_id: Message Identification Number

        Raises:
            ValidationError: If SIN or MIN is invalid
        """
        try:
            if not isinstance(sin, int) or sin < 0:
                raise ValueError("SIN must be a non-negative integer")
            if not isinstance(min_id, int) or min_id < 0:
                raise ValueError("MIN must be a non-negative integer")
        except ValueError as exc:
            raise ValidationError(
                str(exc),
                ValidationError.INVALID_FIELD_VALUE,
            ) from exc
