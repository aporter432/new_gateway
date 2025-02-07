"""
Routes for OGWS message handling.

This module implements:
- Message submission (To-Mobile)
- Message retrieval (From-Mobile)
- Message status tracking
- Transport-aware message routing
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.config import Settings
from core.security import OGWSAuthManager, get_auth_manager
from protocols.ogx.constants.auth import AuthRole, ThrottleGroup
from protocols.ogx.constants.message_states import TransportType

router = APIRouter()


# Enhanced Pydantic models based on OGWS spec
class OGWSMessagePayload(BaseModel):
    """OGWS message payload structure."""

    Name: str
    SIN: int
    MIN: int
    Fields: List[Dict[str, Any]]
    IsForward: Optional[bool] = None


class MessageRequest(BaseModel):
    """Enhanced message request matching OGWS format."""

    DestinationID: str = Field(..., description="Terminal or broadcast ID")
    UserMessageID: Optional[int] = Field(None, description="Client's message ID")
    Payload: OGWSMessagePayload
    TransportType: Optional[int] = Field(None, description="0=Any, 1=Satellite, 2=Cellular")


class MessageResponse(BaseModel):
    """Enhanced response matching OGWS format."""

    ID: Optional[int] = None
    ErrorID: Optional[int] = None
    DestinationID: str
    UserMessageID: Optional[int] = None
    OTAMessageSize: Optional[int] = None


@router.post("/messages/submit", response_model=MessageResponse)
async def submit_message(
    request: MessageRequest,
    auth: OGWSAuthManager = Depends(get_auth_manager),
    settings: Settings = Depends(get_settings),
):
    """Submit To-Mobile message via OGWS."""
    try:
        headers = await auth.get_auth_header()

        # Construct the OGWS endpoint URL
        ogws_endpoint = f"{settings.OGWS_BASE_URL}/submit/messages"

        # Transform our request to match OGWS format
        ogws_request = {
            "DestinationID": request.DestinationID,
            "UserMessageID": request.UserMessageID,
            "Payload": request.Payload.dict(),
            "TransportType": request.TransportType,
        }

        # Make the actual OGWS API call
        async with httpx.AsyncClient() as client:
            response = await client.post(ogws_endpoint, headers=headers, json=ogws_request)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail=f"OGWS error: {response.text}"
            )

        return MessageResponse(**response.json())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit message: {str(e)}")


@router.get("/messages/from-mobile")
async def get_from_mobile_messages(
    from_utc: str,
    include_types: bool = False,
    include_raw_payload: bool = False,
    auth: OGWSAuthManager = Depends(get_auth_manager),
    settings: Settings = Depends(get_settings),
):
    """Retrieve From-Mobile messages from OGWS.

    Implements:
    - High-watermark tracking
    - Automatic message decoding
    - Transport type handling
    """
    try:
        headers = await auth.get_auth_header()
        # Call OGWS get messages endpoint
        messages = await get_ogws_messages(
            headers=headers,
            from_utc=from_utc,
            include_types=include_types,
            include_raw_payload=include_raw_payload,
            base_url=settings.OGWS_BASE_URL,
        )
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@router.get("/messages/status/{message_id}")
async def get_message_status(
    message_id: int,
    auth: OGWSAuthManager = Depends(get_auth_manager),
    settings: Settings = Depends(get_settings),
):
    """Get status of submitted To-Mobile message.

    Tracks:
    - Message delivery state
    - Transport information
    - Error conditions
    """
    try:
        headers = await auth.get_auth_header()
        # Call OGWS status endpoint
        status = await get_ogws_message_status(
            headers=headers, message_id=message_id, base_url=settings.OGWS_BASE_URL
        )
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get message status: {str(e)}")
