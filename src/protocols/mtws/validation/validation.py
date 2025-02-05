"""MTWS Protocol Validation.

This module provides protocol-level validation functions as specified in N206 section 2.4.3.
Single Responsibility: Validate MTWS protocol message sizes and constraints.
"""

from dataclasses import dataclass
from typing import Any, Dict

from ..constants import (
    BASE_HTTP_HEADER_SIZE,
    ELEMENTS_ENVELOPE_SIZE,
    FIELD_ENVELOPE_SIZE,
    FIELD_NAME_BASE_SIZE,
    FIELD_VALUE_BASE_SIZE,
    FIELDS_ENVELOPE_SIZE,
    INDEX_BASE_SIZE,
    MAX_MESSAGE_SIZE,
    MAX_NAME_LENGTH,
    MAX_VALUE_LENGTH,
    MESSAGE_ENVELOPE_SIZE,
    MESSAGE_NAME_BASE_SIZE,
    MIN_BASE_SIZE,
    SIN_BASE_SIZE,
    TCP_IP_OVERHEAD,
)
from ..exceptions import MTWSElementError, MTWSFieldError, MTWSSizeError


@dataclass
class MTWSMessageSizeComponents:
    """Message size components as defined in N206 section 2.4.3.1"""

    message_envelope: int = MESSAGE_ENVELOPE_SIZE
    message_name_base: int = MESSAGE_NAME_BASE_SIZE
    sin_base: int = SIN_BASE_SIZE
    min_base: int = MIN_BASE_SIZE
    fields_envelope: int = FIELDS_ENVELOPE_SIZE
    field_envelope: int = FIELD_ENVELOPE_SIZE
    field_name_base: int = FIELD_NAME_BASE_SIZE
    elements_envelope: int = ELEMENTS_ENVELOPE_SIZE
    index_base: int = INDEX_BASE_SIZE


class MTWSProtocolValidator:
    """Validates MTWS protocol constraints according to N206 section 2.4.3.

    Single Responsibility: Ensure all message components conform to N206 protocol specifications.
    """

    def __init__(self):
        """Initialize size components for validation"""
        self.size_components = MTWSMessageSizeComponents()

    def calculate_field_size(self, field_dict: Dict[str, Any]) -> int:
        """Calculate field size according to N206 section 2.4.3.1"""
        if not isinstance(field_dict, dict):
            raise MTWSFieldError(
                "Field must be a dictionary",
                MTWSFieldError.INVALID_TYPE,
            )

        try:
            size = self.size_components.field_envelope
            name = field_dict.get("Name", "")
            if not name:
                raise MTWSFieldError("Field name is required", MTWSFieldError.INVALID_NAME)

            size += self.size_components.field_name_base + len(name)

            # Count value types present
            value_types = sum(1 for k in ["Value", "Message", "Elements"] if k in field_dict)
            if value_types == 0:
                raise MTWSFieldError(
                    "Field must have exactly one of: Value, Message, or Elements",
                    MTWSFieldError.MISSING_VALUE,
                    field_name=name,
                )
            if value_types > 1:
                raise MTWSFieldError(
                    "Field can only have one of: Value, Message, or Elements",
                    MTWSFieldError.MULTIPLE_VALUES,
                    field_name=name,
                )

            if "Value" in field_dict:
                value_size = FIELD_VALUE_BASE_SIZE + len(str(field_dict["Value"]))
                if value_size > MAX_VALUE_LENGTH:
                    raise MTWSSizeError(
                        f"Field value exceeds maximum length of {MAX_VALUE_LENGTH} bytes",
                        MTWSSizeError.EXCEEDS_FIELD_SIZE,
                        current_size=value_size,
                        max_size=MAX_VALUE_LENGTH,
                    )
                size += value_size

            if "Message" in field_dict:
                message_size = self.calculate_message_size(field_dict["Message"])
                size += message_size

            if "Elements" in field_dict:
                elements_size = self.calculate_elements_size(field_dict["Elements"])
                size += elements_size

            return size
        except MTWSFieldError as e:
            raise e
        except MTWSSizeError as e:
            raise e
        except Exception as e:
            raise MTWSFieldError(
                f"Error calculating field size: {str(e)}",
                MTWSFieldError.INVALID_VALUE,
                field_name=name,
            ) from e

    def calculate_elements_size(self, elements: list) -> int:
        """Calculate size of elements array according to N206 section 2.4.3.1"""
        if not isinstance(elements, list):
            raise MTWSElementError(
                "Elements must be a list",
                MTWSElementError.INVALID_STRUCTURE,
            )
        if not elements:
            raise MTWSElementError(
                "Elements list cannot be empty",
                MTWSElementError.MISSING_FIELDS,
            )
        size = self.size_components.elements_envelope

        for element in elements:
            # Add index size
            size += self.size_components.index_base + len(str(element.get("Index", "")))

            # Add fields envelope
            if "Fields" in element:
                size += self.size_components.fields_envelope
                for field in element["Fields"]:
                    size += self.calculate_field_size(field)

        return size

    def calculate_message_size(self, message_dict: Dict[str, Any]) -> int:
        """Calculate total message size according to N206 section 2.4.3.1"""
        size = self.size_components.message_envelope
        size += self.size_components.message_name_base + len(message_dict.get("Name", ""))
        size += self.size_components.sin_base + len(str(message_dict["SIN"]))
        size += self.size_components.min_base + len(str(message_dict["MIN"]))

        if "Fields" in message_dict:
            size += self.size_components.fields_envelope
            for field in message_dict["Fields"]:
                size += self.calculate_field_size(field)

        return size

    def validate_message_size(self, encoded_json: str) -> None:
        """Validate message size according to N206 section 2.4.3.

        Size components:
        1. JSON content: max 1KB
        2. HTTP header: BASE_HTTP_HEADER_SIZE + content length
        3. TCP/IP: TCP_IP_OVERHEAD each direction
        """
        # 1. JSON content size
        json_size = len(encoded_json)
        if json_size > MAX_MESSAGE_SIZE:
            raise MTWSSizeError(
                "JSON content exceeds 1KB limit",
                MTWSSizeError.EXCEEDS_MESSAGE_SIZE,
                json_size,
                MAX_MESSAGE_SIZE,
            )

        # 2. HTTP header size
        http_header_size = BASE_HTTP_HEADER_SIZE + len(str(json_size))

        # 3. Total size including TCP/IP overhead
        total_size = json_size + http_header_size + (TCP_IP_OVERHEAD * 2)

        # Must fit in 1KB GPRS block
        if total_size > MAX_MESSAGE_SIZE:
            raise MTWSSizeError(
                "Total message size exceeds GPRS block size",
                MTWSSizeError.EXCEEDS_MESSAGE_SIZE,
                total_size,
                MAX_MESSAGE_SIZE,
            )

    def validate_field_constraints(self, field: Dict[str, Any]) -> None:
        """Validate field constraints according to N206 section 2.4.3.1"""
        if not isinstance(field, dict):
            raise MTWSFieldError(
                "Field must be a dictionary",
                MTWSFieldError.INVALID_TYPE,
            )

        # Validate name
        name = field.get("Name", "")
        if not name:
            raise MTWSFieldError("Field name is required", MTWSFieldError.INVALID_NAME)
        if len(name) > MAX_NAME_LENGTH:
            raise MTWSFieldError(
                f"Field name exceeds maximum length of {MAX_NAME_LENGTH}",
                MTWSFieldError.INVALID_LENGTH,
            )

        # Validate value size if present
        if "Value" in field:
            value_size = FIELD_VALUE_BASE_SIZE + len(str(field["Value"]))
            if value_size > MAX_VALUE_LENGTH:
                raise MTWSSizeError(
                    f"Field value exceeds maximum length of {MAX_VALUE_LENGTH} bytes",
                    MTWSSizeError.EXCEEDS_FIELD_SIZE,
                    current_size=value_size,
                    max_size=MAX_VALUE_LENGTH,
                )

        # Count value types present
        value_types = sum(1 for k in ["Value", "Message", "Elements"] if k in field)
        if value_types == 0:
            raise MTWSFieldError(
                "Field must have exactly one of: Value, Message, or Elements",
                MTWSFieldError.MISSING_VALUE,
                field_name=name,
            )
        if value_types > 1:
            raise MTWSFieldError(
                "Field can only have one of: Value, Message, or Elements",
                MTWSFieldError.MULTIPLE_VALUES,
                field_name=name,
            )

        if "Elements" in field:
            if not field["Elements"]:
                raise MTWSElementError(
                    "Elements array cannot be empty",
                    MTWSElementError.MISSING_FIELDS,
                )

            # Validate element indices are sequential
            indices = []
            for element in field["Elements"]:
                if "Index" not in element:
                    raise MTWSElementError(
                        "Element must have an Index",
                        MTWSElementError.MISSING_FIELDS,
                    )
                if not isinstance(element["Index"], int):
                    raise MTWSElementError(
                        f"Element index must be an integer, got {type(element['Index']).__name__}",
                        MTWSElementError.INVALID_INDEX,
                    )
                if element["Index"] < 0:
                    raise MTWSElementError(
                        "Element index must be non-negative",
                        MTWSElementError.NEGATIVE_INDEX,
                        element_index=element["Index"],
                    )
                indices.append(element["Index"])

            if sorted(indices) != list(range(len(indices))):
                raise MTWSElementError(
                    "Element indices must be sequential starting from 0",
                    MTWSElementError.NON_SEQUENTIAL,
                )

            for element in field["Elements"]:
                if "Fields" not in element:
                    raise MTWSElementError(
                        "Element must have a Fields array",
                        MTWSElementError.MISSING_FIELDS,
                    )
                if not element["Fields"]:
                    raise MTWSElementError(
                        "Element Fields array cannot be empty",
                        MTWSElementError.MISSING_FIELDS,
                    )

                # Validate each field in the element
                for field in element["Fields"]:
                    self.validate_field_constraints(field)

    def validate_message(self, message: Dict[str, Any]) -> None:
        """Validate message structure and constraints."""
        if not isinstance(message, dict):
            raise MTWSFieldError(
                "Message must be a dictionary",
                MTWSFieldError.INVALID_TYPE,
            )

        # Check required fields
        required_fields = {"SIN", "MIN", "Version", "IsForward"}
        if missing := required_fields - message.keys():
            raise MTWSFieldError(
                f"Missing required fields: {missing}",
                MTWSFieldError.MISSING_VALUE,
            )

        # Validate SIN (0-255)
        if not isinstance(message["SIN"], int):
            raise MTWSFieldError(
                "SIN must be an integer",
                MTWSFieldError.INVALID_TYPE,
            )
        if not 0 <= message["SIN"] <= 255:
            raise MTWSFieldError(
                "SIN must be between 0 and 255",
                MTWSFieldError.INVALID_VALUE,
            )

        # Validate MIN (0-255)
        if not isinstance(message["MIN"], int):
            raise MTWSFieldError(
                "MIN must be an integer",
                MTWSFieldError.INVALID_TYPE,
            )
        if not 0 <= message["MIN"] <= 255:
            raise MTWSFieldError(
                "MIN must be between 0 and 255",
                MTWSFieldError.INVALID_VALUE,
            )

        # Validate fields if present
        if "Fields" in message:
            if not isinstance(message["Fields"], list):
                raise MTWSFieldError(
                    "Fields must be an array",
                    MTWSFieldError.INVALID_TYPE,
                )
            field_names = set()
            for field in message["Fields"]:
                self.validate_field_constraints(field)
                if field["Name"] in field_names:
                    raise MTWSFieldError(
                        f"Duplicate field name: {field['Name']}",
                        MTWSFieldError.INVALID_NAME,
                    )
                field_names.add(field["Name"])

        # Calculate and validate total message size
        size = self.calculate_message_size(message)
        if size > MAX_MESSAGE_SIZE:
            raise MTWSSizeError(
                "Message size exceeds limit",
                MTWSSizeError.EXCEEDS_MESSAGE_SIZE,
                size,
                MAX_MESSAGE_SIZE,
            )
