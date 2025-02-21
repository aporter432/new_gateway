"""Protocol field definitions for OGx Gateway as defined in OGx-1.txt.

This module defines the base field types and structures used in the OGx protocol.
These definitions represent the raw protocol fields before any API-specific serialization.

Implementation Notes from OGx-1.txt:
    - All fields must have a type, name, and optional constraints
    - String fields have max lengths defined in Section 2.3
    - Numeric fields have ranges defined in Section 2.4
    - Binary fields have size limits defined in Section 2.5
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class FieldType(Enum):
    """Field types supported by the OGx protocol."""

    STRING = "string"  # UTF-8 encoded string
    INTEGER = "integer"  # Signed 32-bit integer
    FLOAT = "float"  # IEEE 754 double precision
    BOOLEAN = "boolean"  # True/False value
    BINARY = "binary"  # Raw binary data
    TIMESTAMP = "timestamp"  # Unix timestamp (seconds)
    ENUM = "enum"  # Enumerated value


@dataclass
class FieldConstraints:
    """Constraints that can be applied to protocol fields."""

    min_length: Optional[int] = None  # Minimum length for strings/binary
    max_length: Optional[int] = None  # Maximum length for strings/binary
    min_value: Optional[Any] = None  # Minimum value for numbers
    max_value: Optional[Any] = None  # Maximum value for numbers
    pattern: Optional[str] = None  # Regex pattern for strings
    enum_values: Optional[list[Any]] = None  # Valid values for enums
    required: bool = True  # Whether field is required


@dataclass
class ProtocolField:
    """Base class for all OGx protocol fields."""

    name: str  # Field name in protocol
    field_type: FieldType  # Type of field
    constraints: FieldConstraints  # Field constraints
    description: str  # Field description

    def validate(self, value: Any) -> bool:
        """Validate a value against this field's constraints.

        Args:
            value: The value to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if value is None and self.constraints.required:
            return False

        if value is None:
            return True

        if self.field_type == FieldType.STRING:
            if not isinstance(value, str):
                return False
            if self.constraints.min_length is not None and len(value) < self.constraints.min_length:
                return False
            if self.constraints.max_length is not None and len(value) > self.constraints.max_length:
                return False
            if self.constraints.pattern is not None and not re.match(
                self.constraints.pattern, value
            ):
                return False

        elif self.field_type == FieldType.INTEGER:
            if not isinstance(value, int):
                return False
            if self.constraints.min_value is not None and value < self.constraints.min_value:
                return False
            if self.constraints.max_value is not None and value > self.constraints.max_value:
                return False

        elif self.field_type == FieldType.FLOAT:
            if not isinstance(value, float):
                return False
            if self.constraints.min_value is not None and value < self.constraints.min_value:
                return False
            if self.constraints.max_value is not None and value > self.constraints.max_value:
                return False

        elif self.field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                return False

        elif self.field_type == FieldType.BINARY:
            if not isinstance(value, bytes):
                return False
            if self.constraints.min_length is not None and len(value) < self.constraints.min_length:
                return False
            if self.constraints.max_length is not None and len(value) > self.constraints.max_length:
                return False

        elif self.field_type == FieldType.TIMESTAMP:
            if not isinstance(value, int):
                return False
            if value < 0:
                return False

        elif self.field_type == FieldType.ENUM:
            if (
                self.constraints.enum_values is not None
                and value not in self.constraints.enum_values
            ):
                return False

        return True
