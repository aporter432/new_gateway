"""MTWS Protocol Message Model.

This module defines the core message structure for the MTWS protocol as specified in
N206 section 2.4.1.
It includes message, field, and element structures in a single module to avoid circular
dependencies."""

from __future__ import annotations  # Enable forward references in type hints

from dataclasses import dataclass
from dataclasses import field as field_decorator
from enum import Enum
from typing import Any, Dict, List, Optional, Union, cast

from ..constants import (
    FIELD_VALUE_BASE_SIZE,
    MAX_NAME_LENGTH,
    MAX_TYPE_LENGTH,
    MAX_VALUE_LENGTH,
    PROTOCOL_VERSION,
)
from ..exceptions import MTWSElementError, MTWSFieldError


class FieldValueType(Enum):
    """Field value types as defined in N206 section 2.4.1."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    BINARY = "binary"


@dataclass
class CommonMessageElement:
    """Represents an element within a MTWS protocol message field.

    As defined in N206 section 2.4.1, each element contains:
    - Index
    - List of fields
    """

    index: int
    fields: List["CommonMessageField"] = field_decorator(default_factory=list)

    def __post_init__(self):
        """Validate element structure according to protocol specifications."""
        self.validate_structure()

    def validate_structure(self) -> None:
        """Validate element structure according to N206 section 2.4.1."""
        if not isinstance(self.index, int):
            raise MTWSElementError(
                "Element index must be an integer, got " f"{type(self.index).__name__}",
                MTWSElementError.INVALID_INDEX,
                element_index=self.index,
            )

        if self.index < 0:
            raise MTWSElementError(
                "Element index must be non-negative",
                MTWSElementError.NEGATIVE_INDEX,
                element_index=self.index,
            )

        if not self.fields:
            raise MTWSElementError(
                "Element must contain at least one field",
                MTWSElementError.MISSING_FIELDS,
                element_index=self.index,
            )

        # Validate field names are unique within element
        field_names = set()
        for field in self.fields:
            if field.name in field_names:
                raise MTWSElementError(
                    f"Duplicate field name '{field.name}' in element",
                    MTWSElementError.INVALID_FIELDS,
                    element_index=self.index,
                )
            field_names.add(field.name)
            field.validate_structure()

    def to_dict(self) -> Dict[str, Any]:
        """Convert element to dictionary format according to N206 section 2.4.1."""
        return {"Index": self.index, "Fields": [field.to_dict() for field in self.fields]}

    def __json__(self):
        """Make the class JSON serializable."""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommonMessageElement":
        """Create element from dictionary according to N206 section 2.4.1."""
        if (
            not isinstance(data, dict)
            or "Index" not in data
            or "Fields" not in data
            or not isinstance(data["Fields"], list)
        ):
            raise MTWSElementError(
                "Element data must be a dictionary with Index and Fields array",
                MTWSElementError.INVALID_STRUCTURE,
            )

        return cls(
            index=data["Index"],
            fields=[CommonMessageField.from_dict(field) for field in data["Fields"]],
        )


@dataclass
class CommonMessageElementList:
    """Represents a list of elements within a MTWS protocol message field."""

    elements: List[CommonMessageElement] = field_decorator(default_factory=list)

    def __post_init__(self):
        """Validate element list structure according to protocol specifications."""
        self.validate_structure()

    def validate_structure(self) -> None:
        """Validate element list structure according to N206 section 2.4.1."""
        if not self.elements:
            raise MTWSElementError(
                "Elements array cannot be empty",
                MTWSElementError.MISSING_FIELDS,
                element_index=None,
            )

        # Ensure elements are in the correct order; sort if necessary
        if not all(self.elements[i].index == i for i in range(len(self.elements))):
            self.elements.sort(key=lambda x: x.index)

        # Validate indices are sequential starting from 0
        expected_index = 0
        for element in self.elements:
            if element.index != expected_index:
                raise MTWSElementError(
                    f"Element indices must be sequential starting from 0, missing index {expected_index}",
                    MTWSElementError.NON_SEQUENTIAL,
                    element_index=element.index,
                )
            expected_index += 1
            element.validate_structure()

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert element list to dictionary format according to N206 section 2.4.1."""
        return [element.to_dict() for element in self.elements]

    def __json__(self):
        """Make the class JSON serializable."""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: List[Dict[str, Any]]) -> "CommonMessageElementList":
        """Create element list from dictionary according to N206 section 2.4.1."""
        if not isinstance(data, list):
            raise MTWSElementError(
                "Element list data must be an array",
                MTWSElementError.INVALID_STRUCTURE,
                element_index=None,
            )
        return cls(elements=[CommonMessageElement.from_dict(element) for element in data])


class CommonMessageField:
    """Represents a field within a MTWS protocol message.

    As defined in N206 section 2.4.1, each field contains:
    - Name (required)
    - Type (optional)
    - One of:
        - Value
        - Message
        - Elements
    """

    def __init__(
        self,
        name: str,
        field_type: Optional[str] = None,
        value: Optional[Any] = None,
        message: Optional[CommonMessage] = None,
        elements: Optional[Union[List[Dict[str, Any]], CommonMessageElementList]] = None,
    ):
        """Initialize a field."""
        self.name = name
        self.type = field_type
        self._value = str(value) if value is not None else None
        self.message = message

        if elements is not None:
            if isinstance(elements, list):
                self.elements = CommonMessageElementList(
                    elements=[CommonMessageElement.from_dict(element) for element in elements]
                )
            else:
                self.elements = elements
        else:
            self.elements = None

        self.validate_structure()

    def validate_structure(self) -> None:
        """Validate field structure according to N206 section 2.4.1."""
        # Validate name
        if not self.name:
            raise MTWSFieldError("Field name is required", MTWSFieldError.INVALID_NAME)
        if not isinstance(self.name, str):
            raise MTWSFieldError(
                "Field name must be a string, got " f"{type(self.name).__name__}",
                MTWSFieldError.INVALID_TYPE,
            )
        if len(self.name) > MAX_NAME_LENGTH:
            raise MTWSFieldError(
                f"Field name exceeds maximum length of {MAX_NAME_LENGTH}",
                MTWSFieldError.INVALID_LENGTH,
            )

        # Validate type if present
        if self.type is not None:
            if not isinstance(self.type, str):
                raise MTWSFieldError(
                    f"Field type must be a string, got {type(self.type).__name__}",
                    MTWSFieldError.INVALID_TYPE,
                )
            if len(self.type) > MAX_TYPE_LENGTH:
                raise MTWSFieldError(
                    f"Field type exceeds maximum length of {MAX_TYPE_LENGTH}",
                    MTWSFieldError.INVALID_LENGTH,
                )

        # Validate value size if present
        if self._value is not None:
            value_size = FIELD_VALUE_BASE_SIZE + len(str(self._value))
            if value_size > MAX_VALUE_LENGTH:
                raise MTWSFieldError(
                    f"Field value exceeds maximum length of {MAX_VALUE_LENGTH} bytes",
                    MTWSFieldError.INVALID_LENGTH,
                    field_name=self.name,
                )

        # Must have exactly one of Value, Message, or Elements
        values = [v for v in (self._value, self.message, self.elements) if v is not None]
        if len(values) == 0:
            raise MTWSFieldError(
                "Field must have exactly one of: Value, Message, or Elements",
                MTWSFieldError.MISSING_VALUE,
                field_name=self.name,
            )
        if len(values) > 1:
            raise MTWSFieldError(
                "Field can only have one of: Value, Message, or Elements",
                MTWSFieldError.MULTIPLE_VALUES,
                field_name=self.name,
            )

    @property
    def value(self) -> Optional[str]:
        """Get the field value."""
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        """Set the field value, converting to string."""
        self._value = str(val) if val is not None else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert field to dictionary format according to N206 section 2.4.1."""
        result: Dict[str, Any] = {"Name": self.name}
        if self.type is not None:
            result["Type"] = self.type
        if self._value is not None:
            result["Value"] = self._value
        if self.message is not None:
            result["Message"] = cast(Dict[str, Any], self.message.to_dict())
        if self.elements is not None:
            result["Elements"] = cast(List[Dict[str, Any]], self.elements.to_dict())
        return result

    def __json__(self):
        """Make the class JSON serializable."""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommonMessageField":
        """Create field from dictionary according to N206 section 2.4.1."""
        if not isinstance(data, dict) or "Name" not in data:
            raise MTWSFieldError(
                "Field data must be a dictionary with Name",
                MTWSFieldError.INVALID_NAME,
            )

        # Extract optional fields
        field_type = data.get("Type")
        value = data.get("Value")
        message = data.get("Message")
        elements = data.get("Elements")

        # Create field instance
        return cls(
            name=data["Name"],
            field_type=field_type,
            value=value,
            message=CommonMessage.from_dict(message) if message is not None else None,
            elements=elements,
        )


@dataclass
class CommonMessage:
    """Represents a MTWS protocol message.

    As defined in N206 section 2.4.1, each message contains:
    - Name (required)
    - SIN (required, 0-255)
    - MIN (required, 0-255)
    - Version (required)
    - IsForward (required)
    - Fields (optional)
    - Sequence (optional, 16-bit unsigned int)
    """

    name: str
    sin: int
    min_value: int
    version: str = PROTOCOL_VERSION
    is_forward: bool = False
    fields: List[CommonMessageField] = field_decorator(default_factory=list)
    sequence: Optional[int] = None

    def __post_init__(self):
        """Validate message structure according to protocol specifications."""
        self.validate_structure()

    def validate_structure(self) -> None:
        """Validate message structure according to N206 section 2.4.1."""
        # Validate name
        if not isinstance(self.name, str):
            raise MTWSFieldError(
                f"Message name must be a string, got {type(self.name).__name__}",
                MTWSFieldError.INVALID_TYPE,
            )
        if not self.name:
            raise MTWSFieldError("Message name is required", MTWSFieldError.INVALID_NAME)
        if len(self.name) > MAX_NAME_LENGTH:
            raise MTWSFieldError(
                f"Message name exceeds maximum length of {MAX_NAME_LENGTH}",
                MTWSFieldError.INVALID_LENGTH,
            )

        # Validate SIN
        if not isinstance(self.sin, int):
            raise MTWSFieldError(
                f"SIN must be an integer, got {type(self.sin).__name__}",
                MTWSFieldError.INVALID_TYPE,
            )
        if not 0 <= self.sin <= 255:
            raise MTWSFieldError(
                "SIN must be between 0 and 255",
                MTWSFieldError.INVALID_VALUE,
            )

        # Validate MIN
        if not isinstance(self.min_value, int):
            raise MTWSFieldError(
                f"MIN must be an integer, got {type(self.min_value).__name__}",
                MTWSFieldError.INVALID_TYPE,
            )
        if not 0 <= self.min_value <= 255:
            raise MTWSFieldError(
                "MIN must be between 0 and 255",
                MTWSFieldError.INVALID_VALUE,
            )

        # Validate version
        if not isinstance(self.version, str):
            raise MTWSFieldError(
                f"Version must be a string, got {type(self.version).__name__}",
                MTWSFieldError.INVALID_TYPE,
            )

        # Validate is_forward
        if not isinstance(self.is_forward, bool):
            raise MTWSFieldError(
                f"IsForward must be a boolean, got {type(self.is_forward).__name__}",
                MTWSFieldError.INVALID_TYPE,
            )

        # Validate sequence if present
        if self.sequence is not None:
            if not isinstance(self.sequence, int):
                raise MTWSFieldError(
                    f"Sequence must be an integer, got {type(self.sequence).__name__}",
                    MTWSFieldError.INVALID_TYPE,
                )
            if not 0 <= self.sequence <= 65535:  # 16-bit unsigned int
                raise MTWSFieldError(
                    "Sequence must be between 0 and 65535",
                    MTWSFieldError.INVALID_VALUE,
                )

        # Validate fields if present
        field_names = set()
        for field in self.fields:
            if field.name in field_names:
                raise MTWSFieldError(
                    f"Duplicate field name: {field.name}",
                    MTWSFieldError.INVALID_NAME,
                )
            field_names.add(field.name)
            field.validate_structure()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format according to N206 section 2.4.1."""
        result = {
            "Name": self.name,
            "SIN": self.sin,
            "MIN": self.min_value,
            "Version": self.version,
            "IsForward": self.is_forward,
        }
        if self.sequence is not None:
            result["Sequence"] = self.sequence
        if self.fields:  # Only include fields if non-empty
            result["Fields"] = [field.to_dict() for field in self.fields]
        return result

    def __json__(self):
        """Make the class JSON serializable."""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommonMessage":
        """Create message from dictionary according to N206 section 2.4.1."""
        if not isinstance(data, dict):
            raise MTWSFieldError(
                "Message data must be a dictionary",
                MTWSFieldError.INVALID_TYPE,
            )

        # Check required fields
        required_fields = {"Name", "SIN", "MIN", "Version", "IsForward"}
        if missing := required_fields - data.keys():
            raise MTWSFieldError(
                f"Missing required field: {next(iter(missing))}",
                MTWSFieldError.MISSING_VALUE,
            )

        # Create message with required fields
        message = cls(
            name=data["Name"],
            sin=data["SIN"],
            min_value=data["MIN"],
            version=data["Version"],
            is_forward=data["IsForward"],
        )

        # Add optional fields
        if "Sequence" in data:
            message.sequence = data["Sequence"]
        if "Fields" in data:
            message.fields = [CommonMessageField.from_dict(field) for field in data["Fields"]]

        return message
