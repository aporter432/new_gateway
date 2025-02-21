"""Field models as defined in OGx-1.txt Table 3.

This module implements the field structures required by the OGx-1.txt specification.
Key requirements:
- All field names must be capitalized in serialized output (e.g., "Name", "Value", "Type")
- Field values must be serialized as strings in the output
- Fields must have exactly one of: value, elements, or message

For serialization:
    - Always use model_dump(by_alias=True) to ensure proper OGx-1.txt compliance
    - Never use dict() as it won't respect the required field name capitalization
"""

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField
from pydantic import field_validator

from Protexis_Command.api_ogx.constants import FieldType
from Protexis_Command.api_ogx.validation.message.ogx_field_validator import OGxFieldValidator
from Protexis_Command.api_ogx.validation.ogx_validation_exceptions import ValidationError


class Element(BaseModel):
    """Element structure as defined in OGx-1.txt Section 5.

    Elements are indexed structures containing fields. In serialized form:
    - 'Index' must be capitalized
    - 'Fields' must be capitalized and contain a list of Field objects

    Example:
        {
            "Index": 0,
            "Fields": [
                {"Name": "status", "Type": "enum", "Value": "ACTIVE"}
            ]
        }
    """

    index: int = PydanticField(alias="Index")
    fields: List["Field"] = PydanticField(alias="Fields")

    model_config = ConfigDict(frozen=True, populate_by_name=True)


class Message(BaseModel):
    """Message structure as defined in OGx-1.txt Section 5.

    Messages contain metadata and fields. In serialized form:
    - All field names must be capitalized ("Name", "SIN", "MIN", "IsForward", "Fields")
    - Field values maintain their types internally but serialize to strings

    Example:
        {
            "Name": "status_message",
            "SIN": 16,
            "MIN": 1,
            "IsForward": true,
            "Fields": [...]
        }
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
    - A type (serialized as "Type"): enum,bool, unsignedint, signedint, string, data, array, message
    - Exactly one of: value, elements, or message (serialized as "Value", "Elements", or "Message")

    Serialization Requirements:
    - Always use model_dump(by_alias=True) for OGx-1.txt compliant output
    - Field names must be capitalized in output ("Name", "Type", "Value", etc.)
    - Numeric and boolean values must be converted to strings in output

    Example:
        field = Field(name="status", type=FieldType.ENUM, value="ACTIVE")
        field.model_dump(by_alias=True)
        # Returns: {"Name": "status", "Type": "enum", "Value": "ACTIVE"}
    """

    name: str = PydanticField(alias="Name")
    type: FieldType = PydanticField(alias="Type")
    value: Optional[Any] = PydanticField(default=None, alias="Value")
    elements: Optional[List[Element]] = PydanticField(default=None, alias="Elements")
    message: Optional[Message] = PydanticField(default=None, alias="Message")

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, populate_by_name=True)

    @field_validator("value")
    @classmethod
    def validate_value_type(cls, v: Any, info):
        """Validate that the value matches the field type according to OGx-1.txt specification.

        Uses OGxFieldValidator to ensure compliance with OGx-1 requirements.

        Args:
            v: The value to validate
            info: Validation context information containing field type

        Returns:
            The validated value, possibly converted (e.g., string booleans to Python booleans)

        Raises:
            ValueError: If the value doesn't match the field type requirements
        """
        field_type = info.data.get("type")
        if v is not None:
            validator = OGxFieldValidator()
            try:
                validator.validate_field_type(field_type, v)  # Using public method instead
                # Convert valid string booleans to Python booleans
                if field_type == FieldType.BOOLEAN and isinstance(v, str):
                    return str(v).lower() in ("true", "1")
                return v
            except ValidationError as e:
                raise ValueError(str(e)) from e  # Properly chain the exception
        return v

    def model_dump(self, **kwargs):
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
