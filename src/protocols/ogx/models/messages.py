"""OGx Message Models according to OGWS-1.txt Section 4.3.

Message directions (Section 4.3):
- To-mobile (forward/FW): Messages sent to terminals from gateway
- From-mobile (return/RE): Messages sent from terminals to gateway
"""

from typing import Any, Dict, List, Optional, Sequence, cast

from pydantic import BaseModel, Field, root_validator

from protocols.ogx.constants import FieldType
from protocols.ogx.constants.message_types import MessageType
from protocols.ogx.validation.common.exceptions import ValidationError
from protocols.ogx.models.fields import Element, Field as OGxField, Message


class OGxMessage(Message):
    """Message structure as defined in OGWS-1.txt Section 4.3.

    According to Section 4.3, every message MUST have:
    - name: Message name
    - sin: Service ID (0-255)
    - min: Message ID
    - message_type: FORWARD (FW) or RETURN (RE) - Required
    - fields: Array of fields
    """

    name: str = Field(..., description="Message name")
    sin: int = Field(..., description="Service identification number (0-255)", ge=0, le=255)
    min: int = Field(..., description="Message identification number")
    message_type: MessageType = Field(
        ..., description="Message direction: FW (to-mobile) or RE (from-mobile)"
    )
    fields: Sequence[OGxField] = Field(
        default_factory=list, description="Array of Field instances per Section 5"
    )

    class Config:
        """Message model configuration."""

        frozen = True
        arbitrary_types_allowed = True

    @root_validator(pre=True)
    @classmethod
    def validate_message_structure(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate message according to OGWS-1.txt Section 5 rules."""
        sin = values.get("sin")
        fields = values.get("fields", [])
        message_type = values.get("message_type")

        # Validate SIN range per Section 5
        if sin is not None and not (0 <= sin <= 255):
            raise ValidationError("SIN must be between 0 and 255")

        # Validate field directions per Section 5
        for field in fields:
            if hasattr(field, "message") and field.message:
                if field.message.message_type != message_type:
                    raise ValidationError("Cannot mix to-mobile and from-mobile messages")

        return values

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary format per OGWS-1.txt Section 5.1.1."""
        data = {
            "Name": self.name,
            "SIN": self.sin,
            "MIN": self.min,
        }
        if self.message_type is not None:
            data["MessageType"] = str(self.message_type)
        if self.fields:
            data["Fields"] = [field.dict() for field in self.fields]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OGxMessage":
        """Create message from dictionary per OGWS-1.txt Section 5.1.1."""
        fields = []
        for f in data.get("Fields", []):
            field_args = {
                "name": f["Name"],
                "type": FieldType(f["Type"]),
            }

            if "Value" in f:
                field_args["value"] = f["Value"]

            if "Elements" in f:
                field_args["elements"] = [
                    Element(index=e["Index"], fields=e["Fields"]) for e in f["Elements"]
                ]

            if "Message" in f:
                # Properly cast the nested message to Message type
                field_args["message"] = cast(Message, cls.from_dict(f["Message"]))

            fields.append(OGxField(**field_args))

        return cls(
            name=data["Name"],
            sin=data["SIN"],
            min=data["MIN"],
            message_type=MessageType(data["MessageType"]),  # Required - no None check
            fields=fields,
        )
