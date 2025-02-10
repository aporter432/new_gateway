"""
OGx field validation according to N214 specification section 5.
Implements field-level validation rules for the Common Message Format.
"""

import base64
import re
from datetime import datetime
from typing import Any, Dict, Callable, Union

from ...constants.field_types import FieldType
from ...constants.limits import (
    MAX_OGX_PAYLOAD_BYTES,
    MAX_OUTSTANDING_MESSAGES_PER_SIZE,
)
from ...constants.message_format import (
    REQUIRED_ELEMENT_PROPERTIES,
    REQUIRED_FIELD_PROPERTIES,
    REQUIRED_MESSAGE_FIELDS,
)
from ...constants.network_types import NetworkType
from ...exceptions import ValidationError


class OGxFieldValidator:
    """Validates individual OGx fields according to N214 specification section 5"""

    # Update TYPE_ATTRIBUTES to use proper typing
    TYPE_ATTRIBUTES: Dict[FieldType, Union[FieldType, str]] = {
        FieldType.ENUM: FieldType.ENUM,
        FieldType.BOOLEAN: FieldType.BOOLEAN,
        FieldType.UNSIGNED_INT: FieldType.UNSIGNED_INT,
        FieldType.SIGNED_INT: FieldType.SIGNED_INT,
        FieldType.STRING: FieldType.STRING,
        FieldType.DATA: FieldType.DATA,
        FieldType.ARRAY: FieldType.ARRAY,
        FieldType.MESSAGE: FieldType.MESSAGE,
        FieldType.DYNAMIC: "(one of above)",
        FieldType.PROPERTY: "(one of above)",
    }

    # Message size limits from Section 2.1 of N214 spec
    MAX_SMALL_MESSAGE_SIZE = 400  # IsatData Pro small messages
    MAX_REGULAR_MESSAGE_SIZE = 2000  # IsatData Pro medium messages
    MAX_LARGE_MESSAGE_SIZE = 10000  # IsatData Pro large messages
    OGX_MESSAGE_SIZE_LIMIT = MAX_OGX_PAYLOAD_BYTES  # OGx network message limit

    # UTC timestamp format from Section 2.1
    TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

    _TYPE_VALIDATORS: Dict[FieldType, str] = {
        FieldType.ENUM: "validate_enum",
        FieldType.BOOLEAN: "validate_boolean",
        FieldType.UNSIGNED_INT: "validate_unsigned_int",
        FieldType.SIGNED_INT: "validate_signed_int",
        FieldType.STRING: "validate_string",
        FieldType.DATA: "validate_data",
        FieldType.ARRAY: "validate_array",
        FieldType.MESSAGE: "validate_message",
        FieldType.DYNAMIC: "validate_dynamic",
        FieldType.PROPERTY: "validate_property",
    }

    def validate_field(self, field: Dict[str, Any]) -> bool:
        """
        Validate a field based on its type.

        Args:
            field: Dictionary containing field data

        Returns:
            bool: True if validation passes

        Raises:
            ValidationError: If validation fails
        """
        try:
            field_type_str = field.get("Type", "").lower()
            field_type = FieldType(field_type_str)

            validator_name = self._TYPE_VALIDATORS.get(field_type)
            if not validator_name:
                raise ValidationError(
                    f"Invalid field type: {field_type}", ValidationError.INVALID_FIELD_TYPE
                )

            validator = getattr(self, validator_name)
            validator(field)  # Will raise ValidationError if validation fails
            return True

        except (ValueError, AttributeError) as e:
            raise ValidationError(
                f"Field validation failed: {str(e)}", ValidationError.INVALID_FIELD_TYPE
            )

    def validate_enum(self, field: Dict[str, Any]) -> bool:
        # Implement enum validation
        self.validate_field_value(FieldType.ENUM, field.get("Value"))
        return True

    def validate_boolean(self, field: Dict[str, Any]) -> bool:
        # Implement boolean validation
        self.validate_field_value(FieldType.BOOLEAN, field.get("Value"))
        return True

    def validate_field_value(
        self, field_type: FieldType, value: Any, type_attribute: Union[str, FieldType, None] = None
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

                # Convert string type_attribute to FieldType if needed
                if isinstance(type_attribute, str):
                    try:
                        type_attribute = FieldType(type_attribute.lower())
                    except ValueError as e:
                        raise ValidationError(
                            f"Invalid type attribute: {type_attribute}",
                            ValidationError.INVALID_FIELD_TYPE,
                        ) from e

                if type_attribute not in self.TYPE_ATTRIBUTES:
                    raise ValidationError(
                        f"Invalid type attribute: {type_attribute}",
                        ValidationError.INVALID_FIELD_TYPE,
                    )

                # Get the resolved type from TYPE_ATTRIBUTES
                resolved_type = self.TYPE_ATTRIBUTES[type_attribute]
                if isinstance(resolved_type, str):
                    raise ValidationError(
                        f"Cannot resolve type attribute: {type_attribute}",
                        ValidationError.INVALID_FIELD_TYPE,
                    )

                # Validate against the resolved type
                return self.validate_field_value(resolved_type, value)

            if field_type == FieldType.BOOLEAN:
                if not isinstance(value, bool):
                    raise ValueError("Boolean value must be true or false")

            elif field_type == FieldType.UNSIGNED_INT:
                # Handle numeric types that can be converted to int
                if isinstance(value, (int, float)):
                    int_val = int(value)
                elif isinstance(value, str):
                    try:
                        int_val = int(float(value))
                    except ValueError:
                        raise ValueError("String value must be a valid number")
                else:
                    raise ValueError(f"Value must be a number, got {type(value).__name__}")

                if int_val < 0:
                    raise ValueError("Decimal number must be non-negative")

            elif field_type == FieldType.SIGNED_INT:
                # Handle numeric types that can be converted to int
                if isinstance(value, (int, float)):
                    int(value)
                elif isinstance(value, str):
                    try:
                        int(float(value))
                    except ValueError:
                        raise ValueError("String value must be a valid number")
                else:
                    raise ValueError(f"Value must be a number, got {type(value).__name__}")

            elif field_type == FieldType.STRING:
                if not isinstance(value, str):
                    raise ValueError(f"Value must be a string, got {type(value).__name__}")

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
                    # Validate array elements
                    for element in value:
                        if not isinstance(element, dict):
                            raise ValueError("Array elements must be dictionaries")
                        if "Index" not in element:
                            raise ValueError("Array elements must have an Index")
                        if "Fields" not in element:
                            raise ValueError("Array elements must have Fields")

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

    def validate_message_size(
        self, message_data: bytes, network_type: NetworkType, message_class: str | None = None
    ) -> None:
        """
        Validates message size limits according to Section 2.1 of N214 spec.

        Args:
            message_data: Raw message data in bytes
            network_type: Network type from NetworkType enum
            message_class: Message size class for IsatData Pro ('small', 'regular', or 'large')

        Raises:
            ValidationError: If message size exceeds limit for its network/class
        """
        size = len(message_data)

        if network_type == NetworkType.OGX:
            if size > self.OGX_MESSAGE_SIZE_LIMIT:
                raise ValidationError(
                    f"OGx message exceeds {self.OGX_MESSAGE_SIZE_LIMIT} byte limit",
                    ValidationError.INVALID_MESSAGE_FORMAT,
                )
        elif network_type == NetworkType.ISATDATA_PRO:
            if not message_class:
                raise ValidationError(
                    "Message class required for IsatData Pro messages",
                    ValidationError.INVALID_MESSAGE_FORMAT,
                )

            if message_class == "small" and size > self.MAX_SMALL_MESSAGE_SIZE:
                raise ValidationError(
                    f"Small IsatData Pro message exceeds {self.MAX_SMALL_MESSAGE_SIZE} byte limit",
                    ValidationError.INVALID_MESSAGE_FORMAT,
                )
            elif message_class == "regular" and size > self.MAX_REGULAR_MESSAGE_SIZE:
                raise ValidationError(
                    f"Regular IsatData Pro message exceeds {self.MAX_REGULAR_MESSAGE_SIZE} byte limit",
                    ValidationError.INVALID_MESSAGE_FORMAT,
                )
            elif message_class == "large" and size > self.MAX_LARGE_MESSAGE_SIZE:
                raise ValidationError(
                    f"Large IsatData Pro message exceeds {self.MAX_LARGE_MESSAGE_SIZE} byte limit",
                    ValidationError.INVALID_MESSAGE_FORMAT,
                )
        else:
            raise ValidationError(
                f"Invalid network type: {network_type}",
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
        Must be non-empty string containing only alphanumeric characters and underscores.

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

        if not name.replace("_", "").isalnum():
            raise ValidationError(
                "Message name must contain only alphanumeric characters and underscores",
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
