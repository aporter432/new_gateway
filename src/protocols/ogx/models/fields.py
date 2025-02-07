"""
OGx field models according to N214 specification section 5.
Implements field type definitions from Table 3 of the Common Message Format.
"""

from base64 import b64decode, b64encode
from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..constants import FieldType
from ..exceptions import ValidationError

__all__ = ["Field", "Element", "DynamicField", "PropertyField", "ArrayField"]


@dataclass
class Field:
    """Base field structure as defined in N214 section 5 Table 3"""

    name: str
    type: FieldType
    value: Optional[Any] = None

    def validate(self) -> None:
        """Validate field value matches its type"""
        if self.value is None:
            return

        try:
            if self.type == FieldType.BOOLEAN:
                if not isinstance(self.value, bool):
                    raise ValueError("Must be true or false")

            elif self.type == FieldType.UNSIGNED_INT:
                val = int(self.value)
                if val < 0:
                    raise ValueError("Must be non-negative")

            elif self.type == FieldType.SIGNED_INT:
                int(self.value)  # Validates it's an integer

            elif self.type == FieldType.STRING:
                if not isinstance(self.value, str):
                    raise ValueError("Must be a string")

            elif self.type == FieldType.ENUM:
                if not isinstance(self.value, str):
                    raise ValueError("Must be a string")

            elif self.type == FieldType.DATA:
                if isinstance(self.value, str):
                    try:
                        b64decode(self.value)
                    except Exception as e:
                        raise ValueError("Must be valid base64") from e
                elif not isinstance(self.value, bytes):
                    raise ValueError("Must be base64 string or bytes")

        except (TypeError, ValueError) as e:
            raise ValidationError(f"Invalid value for {self.type.value}: {self.value}") from e

    def to_dict(self) -> dict:
        """Convert field to dictionary format"""
        result = {
            "Name": self.name,
            "Type": self.type.value,
        }
        if self.value is not None:
            # Handle bytes for DATA fields
            if self.type == FieldType.DATA and isinstance(self.value, bytes):
                result["Value"] = b64encode(self.value).decode()
            else:
                result["Value"] = self.value
        return result


@dataclass
class ArrayField(Field):
    """Array field type as defined in N214 section 5 Table 3"""

    elements: List["Element"] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure type is set correctly"""
        self.type = FieldType.ARRAY
        self.value = None  # Arrays use elements instead of value

    def to_dict(self) -> dict:
        """Convert array field to dictionary format"""
        result = super().to_dict()
        result["Elements"] = [element.to_dict() for element in self.elements]
        return result


@dataclass
class Element:
    """Element structure as defined in N214 section 5"""

    index: int
    fields: List[Field]

    def to_dict(self) -> dict:
        """Convert element to dictionary format"""
        return {"Index": self.index, "Fields": [field.to_dict() for field in self.fields]}


@dataclass
class DynamicField(Field):
    """Dynamic field type as defined in N214 section 5 Table 3"""

    type_attribute: str = ""  # One of the base field types

    def __post_init__(self) -> None:
        """Ensure type is set correctly"""
        self.type = FieldType.DYNAMIC

    def to_dict(self) -> dict:
        """Convert dynamic field to dictionary format"""
        result = super().to_dict()
        result["Type"] = self.type_attribute
        return result


@dataclass
class PropertyField(Field):
    """Property field type as defined in N214 section 5 Table 3"""

    type_attribute: str = ""  # One of the base field types

    def __post_init__(self) -> None:
        """Ensure type is set correctly"""
        self.type = FieldType.PROPERTY

    def to_dict(self) -> dict:
        """Convert property field to dictionary format"""
        result = super().to_dict()
        result["Type"] = self.type_attribute
        return result
