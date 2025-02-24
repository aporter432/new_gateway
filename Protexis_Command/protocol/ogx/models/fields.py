"""Protocol field models as defined in OGx-1.txt Table 3.

This module implements the core field structures required by the OGx-1.txt specification.

Field Types (Table 3):
- enum: Enumeration values
- boolean: True/False values
- unsignedint: Non-negative decimal numbers
- signedint: Signed decimal numbers
- string: String values
- data: Base64 encoded data
- array: Array of elements (no Value attribute)
- message: Embedded message (no Value attribute)
- dynamic: Uses another basic type's attributes
- property: Uses another basic type's attributes

Key Requirements:
- All field names must be capitalized in serialized output (e.g., "Name", "Value", "Type")
- Field values must be serialized as strings in the output
- Fields must have exactly one of: value, elements, or message
- Dynamic and Property fields must specify their Type Attribute

For serialization:
    - Always use model_dump(by_alias=True) to ensure proper OGx-1.txt compliance
    - Never use dict() as it won't respect the required field name capitalization
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField
from pydantic import field_validator

from ..constants.ogx_field_types import FieldType
from ..validation.ogx_validation_exceptions import ValidationError
from ..validation.validators.ogx_field_validator import OGxFieldValidator


class Element(BaseModel):
    """Element structure as defined in OGx-1.txt Section 5.

    Elements are indexed structures containing fields. In serialized form:
    - 'Index' must be capitalized
    - 'Fields' must be capitalized and contain a list of Field objects
    """

    index: int = PydanticField(alias="Index")
    fields: List["Field"] = PydanticField(alias="Fields")

    model_config = ConfigDict(frozen=True, populate_by_name=True)


class Message(BaseModel):
    """Message structure as defined in OGx-1.txt Section 5.

    Messages contain metadata and fields. In serialized form:
    - All field names must be capitalized ("Name", "SIN", "MIN", "IsForward", "Fields")
    - Field values maintain their types internally but serialize to strings
    """

    name: str = PydanticField(alias="Name")
    sin: int = PydanticField(alias="SIN")
    min: int = PydanticField(alias="MIN")
    is_forward: Optional[bool] = PydanticField(default=None, alias="IsForward")
    fields: List["Field"] = PydanticField(alias="Fields")

    model_config = ConfigDict(frozen=True, populate_by_name=True)


class Field(BaseModel):
    """Field structure as defined in OGx-1.txt Section 5 and Table 3.

    According to OGx-1.txt Table 3, a field must have:
    - A name (serialized as "Name")
    - A type (serialized as "Type") from Table 3 field types
    - Exactly one of: value, elements, or message (serialized as "Value", "Elements", or "Message")
    - For dynamic/property types: a type_attribute specifying the basic type to use
    """

    name: str = PydanticField(alias="Name")
    type: FieldType = PydanticField(alias="Type")
    value: Optional[Any] = PydanticField(default=None, alias="Value")
    elements: Optional[List[Element]] = PydanticField(default=None, alias="Elements")
    message: Optional[Message] = PydanticField(default=None, alias="Message")
    type_attribute: Optional[str] = PydanticField(default=None, alias="TypeAttribute")

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, populate_by_name=True)

    @field_validator("value")
    @classmethod
    def validate_value_type(cls, v: Any, info) -> Any:
        """Validate that the value matches the field type according to OGx-1.txt specification."""
        field_type = info.data.get("type")
        if v is not None:
            validator = OGxFieldValidator()
            try:
                validator.validate_field_type(field_type, v)
                if field_type == FieldType.BOOLEAN and isinstance(v, str):
                    return str(v).lower() in ("true", "1")
                return v
            except ValidationError as e:
                raise ValueError(str(e)) from e
        return v

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to handle value serialization according to OGx-1.txt."""
        data = super().model_dump(**kwargs)
        if "Value" in data and data["Value"] is not None:
            if isinstance(data["Value"], (bool, int, float)):
                data["Value"] = str(data["Value"])
        return data


# Handle forward references
Field.model_rebuild()
Element.model_rebuild()
Message.model_rebuild()

__all__ = ["Element", "Field", "Message"]
