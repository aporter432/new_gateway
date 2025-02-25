"""Information models for the OGx API.

This module defines the response models for information endpoints
as specified in OGx-1.txt Section 4.2.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    """Service information and error codes."""

    version: str = Field(..., description="OGx API version")
    status: str = Field(..., description="Service status")
    error_codes: Dict[str, str] = Field(..., description="Map of error codes to descriptions")
    features: List[str] = Field(..., description="Supported API features")


class SubaccountInfo(BaseModel):
    """Information about a subaccount."""

    id: int = Field(..., description="Subaccount ID")
    name: str = Field(..., description="Subaccount name")
    status: str = Field(..., description="Account status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    features: List[str] = Field(..., description="Enabled features")


class TerminalInfo(BaseModel):
    """Information about a terminal."""

    prime_id: str = Field(..., description="Terminal prime identifier")
    name: Optional[str] = Field(None, description="Terminal name")
    type: str = Field(..., description="Terminal type")
    status: str = Field(..., description="Terminal status")
    last_seen: Optional[datetime] = Field(None, description="Last communication timestamp")
    subaccount_id: Optional[int] = Field(None, description="Associated subaccount ID")
    features: List[str] = Field(..., description="Supported features")


class BroadcastInfo(BaseModel):
    """Information about broadcast capabilities."""

    id: str = Field(..., description="Broadcast region ID")
    name: str = Field(..., description="Region name")
    coverage: List[Dict[str, float]] = Field(..., description="Coverage area coordinates")
    status: str = Field(..., description="Broadcast status")
    terminal_count: int = Field(..., description="Number of terminals in region")
