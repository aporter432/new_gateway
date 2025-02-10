"""Field models as defined in OGWS-1.txt Table 3."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, root_validator

from protocols.ogx.constants import FieldType
from protocols.ogx.validation.common.exceptions import ValidationError


class Element(BaseModel):
    """Element structure as defined in OGWS-1.txt Section 5."""

    index: int
    fields: List["Field"]

    class Config:
        frozen = True


class Message(BaseModel):
    """Message structure as defined in OGWS-1.txt Section 5."""

    name: str
    sin: int
    min: int
    is_forward: Optional[bool] = None
    fields: List["Field"]

    class Config:
        frozen = True


class Field(BaseModel):
    """Field structure as defined in OGWS-1.txt Section 5 and Table 3.

    According to Table 3, a field must have:
    - A name
    - A type (enum, boolean, unsignedint, signedint, string, data, array, or message)
    - Either a value, elements, or message (but not more than one)
    """

    name: str
    type: FieldType
    value: Optional[Any] = None
    elements: Optional[List[Element]] = None
    message: Optional[Message] = None

    class Config:
        frozen = True
        arbitrary_types_allowed = True

    @root_validator(pre=True)
    @classmethod
    def validate_field_structure(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate according to OGWS-1.txt Section 5 and Table 3 rules."""
        has_value = values.get("value") is not None
        has_elements = values.get("elements") is not None
        has_message = values.get("message") is not None
        field_type = values.get("type")

        # Check for multiple value types
        if sum([has_value, has_elements, has_message]) > 1:
            raise ValidationError("Field can only have one of: value, elements, or message")

        # Array type can only have elements
        if field_type == FieldType.ARRAY and has_value:
            raise ValidationError("Array type can only have elements, not value")

        # Message type can only have message
        if field_type == FieldType.MESSAGE and (has_value or has_elements):
            raise ValidationError("Message type can only have message, not value or elements")

        return values


# Handle forward references
Field.model_rebuild()
Element.model_rebuild()
Message.model_rebuild()
