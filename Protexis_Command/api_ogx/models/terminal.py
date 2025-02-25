"""Terminal operation models for OGx API.

This module contains request and response models for terminal operation endpoints.
These models are based on OGx-1.txt and Swagger documentation.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TerminalMode(str, Enum):
    """Terminal operation modes."""

    ALWAYS_ON = "ALWAYS_ON"
    WAKE_UP = "WAKE_UP"
    ACTIVE = "ACTIVE"
    VIRTUAL = "VIRTUAL"


class WakeupInterval(str, Enum):
    """Terminal wakeup interval options."""

    NORMAL = "NORMAL"
    SLOW = "SLOW"
    ULTRA_SLOW = "ULTRA_SLOW"
    ACTIVE = "ACTIVE"


class TerminalResetRequest(BaseModel):
    """Request model for terminal reset operation."""

    terminal_id: str = Field(..., description="Terminal identifier")
    sub_account_id: Optional[str] = Field(None, description="Sub-account identifier")
    type: Optional[str] = Field(None, description="Reset type")
    delay: Optional[int] = Field(None, description="Delay in seconds before executing reset")
    priority: Optional[str] = Field(None, description="Message priority")


class SystemResetRequest(BaseModel):
    """Request model for terminal system reset operation."""

    terminal_id: str = Field(..., description="Terminal identifier")
    sub_account_id: Optional[str] = Field(None, description="Sub-account identifier")
    type: Optional[str] = Field("NORMAL", description="Reset type")
    delay: Optional[int] = Field(None, description="Delay in seconds before executing reset")
    priority: Optional[str] = Field(None, description="Message priority")
    preserve_config: Optional[bool] = Field(None, description="Whether to preserve configuration")
    reset_status: Optional[bool] = Field(None, description="Whether to reset status")
    clear_queue: Optional[bool] = Field(None, description="Whether to clear the message queue")


class TerminalModeRequest(BaseModel):
    """Request model for terminal mode change operation."""

    terminal_id: str = Field(..., description="Terminal identifier")
    sub_account_id: Optional[str] = Field(None, description="Sub-account identifier")
    mode: TerminalMode = Field(..., description="Terminal operation mode")
    wakeup_interval: Optional[WakeupInterval] = Field(None, description="Terminal wakeup interval")
    delay: Optional[int] = Field(None, description="Delay in seconds before executing mode change")
    priority: Optional[str] = Field(None, description="Message priority")


class TerminalMuteRequest(BaseModel):
    """Request model for terminal mute/unmute operation."""

    terminal_id: str = Field(..., description="Terminal identifier")
    sub_account_id: Optional[str] = Field(None, description="Sub-account identifier")
    mute: bool = Field(..., description="Whether to mute (true) or unmute (false)")
    delay: Optional[int] = Field(None, description="Delay in seconds before executing mute/unmute")
    priority: Optional[str] = Field(None, description="Message priority")


class TerminalOperationResponse(BaseModel):
    """Response model for terminal operations."""

    terminal_id: str = Field(..., description="Terminal identifier")
    message_id: Optional[str] = Field(None, description="Message identifier")
    status: str = Field(..., description="Operation status")
    error: Optional[str] = Field(None, description="Error message if operation failed")
