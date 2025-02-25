"""API field models for OGx Gateway as defined in OGx-1.txt.

This module implements the field types specified in OGx-1.txt Table 3,
providing type-specific implementations for each supported field type.
"""

from datetime import datetime
from typing import Any, Optional

from Protexis_Command.protocols.ogx.constants.ogx_field_types import FieldType
from Protexis_Command.protocols.ogx.models.fields import Field as ProtocolField


class APIField(ProtocolField):
    """Base API field that extends the protocol field."""

    description: Optional[str] = None
    required: bool = True


class StringField(APIField):
    """String field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.STRING
    value: Optional[str] = None


class UnsignedIntField(APIField):
    """Unsigned integer field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.UNSIGNED_INT
    value: Optional[int] = None


class SignedIntField(APIField):
    """Signed integer field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.SIGNED_INT
    value: Optional[int] = None


class BooleanField(APIField):
    """Boolean field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.BOOLEAN
    value: Optional[bool] = None


class DataField(APIField):
    """Base64 encoded data field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.DATA
    value: Optional[str] = None  # Base64 encoded string


class ArrayField(APIField):
    """Array field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.ARRAY
    elements: Optional[list] = None  # Array elements instead of value


class MessageField(APIField):
    """Message field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.MESSAGE
    message: Optional[dict] = None  # Message content instead of value


class EnumField(APIField):
    """Enum field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.ENUM
    value: Optional[str] = None


class DynamicField(APIField):
    """Dynamic field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.DYNAMIC
    value: Optional[Any] = None
    type_attribute: Optional[str] = None


class PropertyField(APIField):
    """Property field as defined in OGx-1.txt Table 3."""

    type: FieldType = FieldType.PROPERTY
    value: Optional[Any] = None
    type_attribute: Optional[str] = None


class TimestampField(APIField):
    """ISO format timestamp field as defined in OGx-1.txt."""

    type: FieldType = FieldType.STRING
    value: Optional[str] = None

    @classmethod
    def validate_timestamp(cls, v: Any) -> str:
        """Convert datetime to ISO format timestamp."""
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%dT%H:%M:%SZ")
        return v


__all__ = [
    "APIField",
    "StringField",
    "UnsignedIntField",
    "SignedIntField",
    "BooleanField",
    "DataField",
    "ArrayField",
    "MessageField",
    "EnumField",
    "DynamicField",
    "PropertyField",
    "TimestampField",
]
