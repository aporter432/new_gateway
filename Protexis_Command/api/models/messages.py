"""Message models for the OGx API.

This module defines the request and response models for message endpoints
as specified in OGx-1.txt Section 4.3 and 4.4.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from Protexis_Command.api.models.fields import MessageField


class MessagePriority(str, Enum):
    """Message priority levels."""

    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class MessageStatus(str, Enum):
    """Message delivery status codes."""

    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class MessageRequest(BaseModel):
    """Request model for submitting messages."""

    terminal_id: str = Field(..., description="Target terminal ID")
    payload: Union[str, Dict[str, MessageField]] = Field(
        ..., description="Message payload or field dictionary"
    )
    priority: MessagePriority = Field(MessagePriority.NORMAL, description="Message priority")
    expires_at: Optional[datetime] = Field(None, description="Message expiration timestamp")
    callback_url: Optional[str] = Field(None, description="Webhook URL for status updates")

    @field_validator("payload")
    def validate_payload(cls, v):
        """Ensure payload is either a string or valid field dictionary."""
        if isinstance(v, str):
            return v
        if not all(isinstance(f, MessageField) for f in v.values()):
            raise ValueError("All fields must be MessageField instances")
        return v


class MultiDestinationRequest(MessageRequest):
    """Request model for sending to multiple terminals."""

    terminal_ids: List[str] = Field(..., description="List of target terminal IDs")


class MessageResponse(BaseModel):
    """Response model for message operations."""

    message_id: str = Field(..., description="Unique message identifier")
    terminal_id: str = Field(..., description="Target terminal ID")
    status: MessageStatus = Field(..., description="Current message status")
    created_at: datetime = Field(..., description="Message creation timestamp")
    updated_at: datetime = Field(..., description="Last status update timestamp")
    payload: Union[str, Dict[str, MessageField]] = Field(
        ..., description="Original message payload"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, str] = Field(
        default_factory=dict, description="Additional message metadata"
    )
