"""Message models for OGx protocol.

This module provides message models and conversion utilities for the OGx protocol.
"""

from typing import Any, Dict, Optional, ClassVar


class OGxMessage:
    """Base class for OGx protocol messages."""

    # Message field names
    NAME_FIELD: ClassVar[str] = "Name"
    SIN_FIELD: ClassVar[str] = "SIN"
    MIN_FIELD: ClassVar[str] = "MIN"
    IS_FORWARD_FIELD: ClassVar[str] = "IsForward"
    FIELDS_FIELD: ClassVar[str] = "Fields"

    def __init__(
        self,
        name: str,
        sin: int,
        min_value: int,
        is_forward: Optional[bool] = None,
        fields: Optional[list] = None,
    ):
        """Initialize an OGxMessage.

        Args:
            name: Message name
            sin: Service Identification Number
            min_value: Message Identification Number
            is_forward: Whether message is forward direction
            fields: List of message fields
        """
        self.name = name
        self.sin = sin
        self.min = min_value
        self.is_forward = is_forward
        self.fields = fields or []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OGxMessage":
        """Create an OGxMessage from a dictionary.

        Args:
            data: Dictionary containing message data

        Returns:
            OGxMessage instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        required_fields = {cls.NAME_FIELD, cls.SIN_FIELD, cls.MIN_FIELD}
        if not all(field in data for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields - data.keys()}")

        return cls(
            name=data[cls.NAME_FIELD],
            sin=int(data[cls.SIN_FIELD]),
            min_value=int(data[cls.MIN_FIELD]),
            is_forward=data.get(cls.IS_FORWARD_FIELD),
            fields=data.get(cls.FIELDS_FIELD, []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format.

        Returns:
            Dictionary representation of the message
        """
        data = {
            self.NAME_FIELD: self.name,
            self.SIN_FIELD: self.sin,
            self.MIN_FIELD: self.min,
        }

        if self.is_forward is not None:
            data[self.IS_FORWARD_FIELD] = self.is_forward

        if self.fields:
            data[self.FIELDS_FIELD] = self.fields

        return data

    def __repr__(self) -> str:
        """Get string representation of the message.

        Returns:
            String representation
        """
        return f"OGxMessage(name={self.name}, sin={self.sin}, min={self.min})"
