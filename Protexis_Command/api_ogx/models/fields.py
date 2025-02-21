"""API field models for OGx Gateway as defined in OGx-1.txt.

This module defines the Pydantic models for field serialization in the OGx API.
These models wrap the protocol fields with API-specific validation and serialization.

Implementation Notes from OGx-1.txt:
    - API models must validate all constraints from protocol fields
    - Models should provide clean serialization to/from JSON
    - Additional API-specific validation may be added
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

from Protexis_Command.protocol.ogx.ogx_fields import FieldConstraints, FieldType, ProtocolField


class APIField(BaseModel):
    """Base model for all OGx API fields."""

    name: str = Field(..., description="Field name")
    type: FieldType = Field(..., description="Field type")
    value: Any = Field(None, description="Field value")
    description: Optional[str] = Field(None, description="Field description")
    required: bool = Field(True, description="Whether field is required")
    constraints: Optional[FieldConstraints] = Field(None, description="Field constraints")

    @validator("value")
    def validate_value(self, v, values):
        """Validate field value against constraints."""
        if "constraints" not in values or values["constraints"] is None:
            return v

        field = ProtocolField(
            name=values["name"],
            field_type=values["type"],
            constraints=values["constraints"],
            description=values.get("description", ""),
        )

        if not field.validate(v):
            raise ValueError(f"Invalid value for field {values['name']}")

        return v


class StringField(APIField):
    """String field for OGx API."""

    type: FieldType = Field(default=FieldType.STRING)
    value: Optional[str] = None


class IntegerField(APIField):
    """Integer field for OGx API."""

    type: FieldType = Field(default=FieldType.INTEGER)
    value: Optional[int] = None


class FloatField(APIField):
    """Float field for OGx API."""

    type: FieldType = Field(default=FieldType.FLOAT)
    value: Optional[float] = None


class BooleanField(APIField):
    """Boolean field for OGx API."""

    type: FieldType = Field(default=FieldType.BOOLEAN)
    value: Optional[bool] = None


class BinaryField(APIField):
    """Binary field for OGx API."""

    type: FieldType = Field(default=FieldType.BINARY)
    value: Optional[bytes] = None


class TimestampField(APIField):
    """Timestamp field for OGx API."""

    type: FieldType = Field(default=FieldType.TIMESTAMP)
    value: Optional[int] = None

    @validator("value")
    def validate_timestamp(self, v):
        """Convert datetime to timestamp if needed."""
        if isinstance(v, datetime):
            return int(v.timestamp())
        return v


class EnumField(APIField):
    """Enum field for OGx API."""

    type: FieldType = Field(default=FieldType.ENUM)
    value: Optional[Any] = None
