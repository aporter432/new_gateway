"""
OGx message models according to N214 specification section 5.
Implements message format definitions from the Common Message Format.
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, Sequence

from ..constants import FieldType
from .fields import ArrayField, Element, Field

__all__ = ["OGxMessage"]


@dataclass
class OGxMessage:
    """Message structure as defined in N214 section 5"""

    name: str
    sin: int
    min: int
    fields: Sequence[Field] = dataclass_field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OGxMessage":
        """
        Create message instance from dictionary data.

        Args:
            data: Dictionary containing message data

        Returns:
            OGxMessage instance
        """
        fields_data = data.get("Fields", [])
        message_fields = []

        for field_data in fields_data:
            field_type = field_data.get("Type")
            if field_type == "array":
                elements = []
                for element_data in field_data.get("Elements", []):
                    element_fields = [
                        Field(name=f["Name"], type=FieldType(f["Type"]), value=f.get("Value"))
                        for f in element_data.get("Fields", [])
                    ]
                    elements.append(Element(index=element_data["Index"], fields=element_fields))
                message_fields.append(
                    ArrayField(name=field_data["Name"], type=FieldType.ARRAY, elements=elements)
                )
            else:
                message_fields.append(
                    Field(
                        name=field_data["Name"],
                        type=FieldType(field_data["Type"]),
                        value=field_data.get("Value"),
                    )
                )

        return cls(name=data["Name"], sin=data["SIN"], min=data["MIN"], fields=message_fields)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert message to dictionary format.

        Returns:
            Dictionary representation of the message
        """
        return {
            "Name": self.name,
            "SIN": self.sin,
            "MIN": self.min,
            "Fields": [message_field.to_dict() for message_field in self.fields],
        }

    def validate(self) -> None:
        """
        Validate message structure and field values.

        Raises:
            ValidationError: If validation fails
        """
        for message_field in self.fields:
            message_field.validate()
