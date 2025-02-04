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
                    "Field must have one of: Value, Message, or Elements",
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
                size += FIELD_VALUE_BASE_SIZE + len(str(field_dict["Value"]))
            elif "Elements" in field_dict:
                elements = field_dict["Elements"]
                size += self.size_components.elements_envelope

                # Validate element indices
                indices = [elem.get("Index") for elem in elements]
                if len(indices) != len(set(indices)):
                    raise MTWSElementError(
                        "Element indices must be unique", MTWSElementError.INVALID_INDEX
                    )
                if any(not isinstance(idx, int) or idx < 0 for idx in indices):
                    raise MTWSElementError(
                        "Element indices must be non-negative integers",
                        MTWSElementError.NEGATIVE_INDEX,
                    )

                for element in elements:
                    size += self.size_components.index_base + len(str(element.get("Index", 0)))
                    if "Fields" not in element:
                        raise MTWSElementError(
                            "Element must contain Fields array",
                            MTWSElementError.MISSING_FIELDS,
                            element_index=element.get("Index"),
                        )
                    for field in element.get("Fields", []):
                        size += self.calculate_field_size(field)
            elif "Message" in field_dict:
                size += self.calculate_message_size(field_dict["Message"])

            return size

        except (MTWSFieldError, MTWSElementError):
            raise
        except Exception as e:
            raise MTWSFieldError(
                f"Field validation failed: {str(e)}",
                MTWSFieldError.INVALID_VALUE,
                field_name=field_dict.get("Name"),
            ) from e

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

    def validate_field_constraints(self, field_dict: Dict[str, Any]) -> None:
        """Validate field constraints according to N206 section 2.4.3.1"""
        # This method now primarily handles structural validation
        # Size calculation and validation is handled in calculate_field_size
        try:
            name = field_dict.get("Name")
            if not name:
                raise MTWSFieldError("Field name is required", MTWSFieldError.INVALID_NAME)

            # Validate field type if present
            if "Type" in field_dict and not isinstance(field_dict["Type"], str):
                raise MTWSFieldError(
                    "Field type must be a string", MTWSFieldError.INVALID_TYPE, field_name=name
                )

            # Calculate size to trigger all size-related validations
            self.calculate_field_size(field_dict)

        except MTWSFieldError:
            raise
        except Exception as e:
            raise MTWSFieldError(
                f"Field validation failed: {str(e)}",
                MTWSFieldError.INVALID_VALUE,
                field_name=field_dict.get("Name"),
            ) from e
