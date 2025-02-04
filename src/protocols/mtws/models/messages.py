"""MTWS Protocol Message Model.

This module defines the core message structure for the MTWS protocol as specified in
N206 section 2.4.1.
It includes message, field, and element structures in a single module to avoid circular
dependencies."""

import json
from dataclasses import dataclass
from dataclasses import field as field_decorator
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from ..constants import (
    MAX_NAME_LENGTH,
    MAX_TYPE_LENGTH,
    NAME_PATTERN,
    PROTOCOL_VERSION,
    TYPE_PATTERN,
)
from ..exceptions import MTWSElementError, MTWSFieldError
from ..validation.validation import MTWSProtocolValidator


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
                f"Element index must be an integer, got {type(self.index).__name__}",
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
                    MTWSElementError.INVALID_STRUCTURE,
                    element_index=self.index,
                )
            field_names.add(field.name)
            field.validate_structure()

    def to_dict(self) -> Dict[str, Any]:
        """Convert element to dictionary format according to N206 section 2.4.1."""
        return {"Index": self.index, "Fields": [field.to_dict() for field in self.fields]}

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
            raise MTWSElementError("Element list cannot be empty", MTWSElementError.MISSING_FIELDS)

        # Ensure elements are in the correct order; sort if necessary
        if not all(self.elements[i].index == i for i in range(len(self.elements))):
            self.elements.sort(key=lambda x: x.index)

        # Validate indices are sequential starting from 0
        expected_index = 0
        for element in self.elements:
            if element.index != expected_index:
                msg = (
                    f"Element indices must be sequential starting from 0, "
                    f"missing index {expected_index}"
                )
                raise MTWSElementError(
                    msg,
                    MTWSElementError.NON_SEQUENTIAL,
                    element_index=element.index,
                )
            expected_index += 1
            element.validate_structure()

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert element list to dictionary format according to N206 section 2.4.1."""
        return [element.to_dict() for element in self.elements]

    @classmethod
    def from_dict(cls, data: List[Dict[str, Any]]) -> "CommonMessageElementList":
        """Create element list from dictionary according to N206 section 2.4.1."""
        if not isinstance(data, list):
            raise MTWSElementError(
                "Element list data must be an array", MTWSElementError.INVALID_STRUCTURE
            )
        return cls(elements=[CommonMessageElement.from_dict(element) for element in data])


@dataclass
class CommonMessageField:
    """Represents a field within a MTWS protocol message.

    As defined in N206 section 2.4.1, each field must contain:
    - Name (required, alphanumeric, max 32 chars)
    - Type (optional, alphanumeric, max 32 chars)
    - Exactly one of: Value (string), Message (nested message), or Elements (list of elements)
    """

    name: str
    type: Optional[str] = None
    value: Optional[str] = None
    message: Optional["CommonMessage"] = None
    elements: Optional[CommonMessageElementList] = None
    _validator: ClassVar[MTWSProtocolValidator] = MTWSProtocolValidator()

    def __post_init__(self):
        """Validate field structure according to N206 specifications."""
        self.validate_structure()

    def validate_structure(self) -> None:
        """Validate field structure according to N206 section 2.4.1."""
        # Validate name
        if not self.name:
            raise MTWSFieldError("Field name is required", MTWSFieldError.INVALID_NAME)
        if not isinstance(self.name, str):
            raise MTWSFieldError(
                f"Field name must be a string, got {type(self.name).__name__}",
                MTWSFieldError.INVALID_TYPE,
                field_name=self.name,
            )
        if len(self.name) > MAX_NAME_LENGTH:
            raise MTWSFieldError(
                f"Field name exceeds maximum length of {MAX_NAME_LENGTH}",
                MTWSFieldError.INVALID_NAME,
                field_name=self.name,
            )
        if not NAME_PATTERN.match(self.name):
            raise MTWSFieldError(
                "Field name must contain only alphanumeric characters and underscores",
                MTWSFieldError.INVALID_NAME,
                field_name=self.name,
            )

        # Validate type if present
        if self.type is not None:
            if not isinstance(self.type, str):
                raise MTWSFieldError(
                    f"Field type must be a string, got {type(self.type).__name__}",
                    MTWSFieldError.INVALID_TYPE,
                    field_name=self.name,
                )
            if len(self.type) > MAX_TYPE_LENGTH:
                raise MTWSFieldError(
                    f"Field type exceeds maximum length of {MAX_TYPE_LENGTH}",
                    MTWSFieldError.INVALID_TYPE,
                    field_name=self.name,
                )
            if not TYPE_PATTERN.match(self.type):
                raise MTWSFieldError(
                    "Field type must contain only alphanumeric characters and underscores",
                    MTWSFieldError.INVALID_TYPE,
                    field_name=self.name,
                )

        # N206 2.4.1: Must have exactly one of Value, Message, or Elements
        values = [v for v in (self.value, self.message, self.elements) if v is not None]
        if len(values) != 1:
            raise MTWSFieldError(
                "Field must have exactly one of: value, message, or elements",
                MTWSFieldError.MULTIPLE_VALUES if len(values) > 1 else MTWSFieldError.MISSING_VALUE,
                field_name=self.name,
            )

        # Validate field constraints using the validator
        self._validator.validate_field_constraints(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """Convert field to dictionary format according to N206 section 2.4.1."""
        field_dict = {"Name": self.name}
        if self.type is not None:
            field_dict["Type"] = self.type
        if self.value is not None:
            field_dict["Value"] = self.value
        elif self.message is not None:
            field_dict["Message"] = json.dumps(self.message.to_dict())
        elif self.elements is not None:
            field_dict["Elements"] = json.dumps(self.elements.to_dict())
        return field_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommonMessageField":
        """Create field from dictionary according to N206 section 2.4.1."""
        if not isinstance(data, dict) or "Name" not in data:
            raise MTWSFieldError(
                "Field data must be a dictionary containing Name",
                MTWSFieldError.INVALID_TYPE,
            )

        field = cls(
            name=data["Name"],
            type=data.get("Type"),
        )

        # Handle exactly one of Value, Message, or Elements
        if "Value" in data:
            field.value = str(data["Value"])
        elif "Message" in data:
            field.message = CommonMessage.from_dict(data["Message"])
        elif "Elements" in data:
            field.elements = CommonMessageElementList.from_dict(data["Elements"])

        return field


@dataclass
class CommonMessage:
    """MTWS protocol message structure as defined in N206 section 2.4.1."""

    sin: int  # Service Identification Number (0-255)
    min: int  # Message Identification Number (0-255)
    is_forward: bool  # True = To-Mobile, False = From-Mobile
    version: str = PROTOCOL_VERSION  # Use imported constant
    name: Optional[str] = None  # Optional message name
    sequence: Optional[int] = None  # Optional sequence number
    fields: List[CommonMessageField] = field_decorator(default_factory=list)
    _validator: ClassVar[MTWSProtocolValidator] = MTWSProtocolValidator()

    def __post_init__(self):
        """Validate message structure according to N206 specifications."""
        self._validate_structure()

    def _validate_structure(self) -> None:
        """Validate message structure according to N206 section 2.4."""
        # SIN validation (0-255)
        if not isinstance(self.sin, int) or not 0 <= self.sin <= 255:
            raise MTWSFieldError(
                f"Invalid SIN value: {self.sin}. Must be an integer between 0-255",
                MTWSFieldError.INVALID_VALUE,
            )
        # MIN validation (0-255)
        if not isinstance(self.min, int) or not 0 <= self.min <= 255:
            raise MTWSFieldError("MIN must be between 0 and 255", MTWSFieldError.INVALID_VALUE)

        # IsForward validation (boolean)
        if not isinstance(self.is_forward, bool):
            raise MTWSFieldError("IsForward must be a boolean", MTWSFieldError.INVALID_VALUE)

        # Version validation (2.0.6)
        if self.version != PROTOCOL_VERSION:
            raise MTWSFieldError("Invalid protocol version", MTWSFieldError.INVALID_VALUE)

        # Add validation for field name max length (32 chars per N206)
        if self.name and len(self.name) > MAX_NAME_LENGTH:
            raise MTWSFieldError(
                "Message name exceeds maximum length of 32 characters", MTWSFieldError.INVALID_NAME
            )

        # Validate message size using the validator
        self._validator.validate_message_size(json.dumps(self.to_dict()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format as per N206."""
        message_dict = {
            "SIN": self.sin,
            "MIN": self.min,
            "Version": self.version,
            "IsForward": self.is_forward,
        }
        if self.name:
            message_dict["Name"] = self.name
        if self.sequence:
            message_dict["Sequence"] = self.sequence
        if self.fields:
            message_dict["Fields"] = [field.to_dict() for field in self.fields]
        return message_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommonMessage":
        """Create message from dictionary as per N206."""
        if not isinstance(data, dict) or "SIN" not in data or "MIN" not in data:
            raise MTWSFieldError(
                "Message data must be a dictionary containing SIN and MIN",
                MTWSFieldError.INVALID_TYPE,
            )

        required = {"SIN", "MIN", "Version", "IsForward"}
        if missing := required - data.keys():
            raise MTWSFieldError(
                f"Missing required fields: {missing}", MTWSFieldError.MISSING_VALUE
            )

        return cls(
            sin=int(data["SIN"]),
            min=int(data["MIN"]),
            is_forward=data["IsForward"],
            version=data["Version"],
            name=data.get("Name"),
            sequence=data.get("Sequence"),
            fields=[CommonMessageField.from_dict(field) for field in data.get("Fields", [])],
        )
