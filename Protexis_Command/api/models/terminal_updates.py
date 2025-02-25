"""Terminal updates model for OGx API.

This module defines models for retrieving terminal updates from the OGx API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TerminalUpdate(BaseModel):
    """Model representing a terminal update notification."""

    terminal_id: str = Field(..., description="Terminal identifier")
    sub_account_id: Optional[str] = Field(None, description="Sub-account identifier")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    modification_type: str = Field(..., description="Type of modification")
    fields_modified: List[str] = Field(default_factory=list, description="List of modified fields")


class TerminalUpdatesRequest(BaseModel):
    """Request parameters for retrieving terminal updates."""

    from_utc: datetime = Field(..., description="Start time for updates query")
    sub_account_id: Optional[str] = Field(None, description="Sub-account identifier for filtering")
    max_count: Optional[int] = Field(None, description="Maximum number of updates to return")
    include_deleted: Optional[bool] = Field(
        False, description="Whether to include deleted terminals"
    )


class TerminalUpdatesResponse(BaseModel):
    """Response model for terminal updates endpoint."""

    updates: List[TerminalUpdate] = Field(
        default_factory=list, description="List of terminal updates"
    )
    more_available: bool = Field(False, description="Whether more updates are available")
    next_from_utc: Optional[datetime] = Field(None, description="Next start time for pagination")
