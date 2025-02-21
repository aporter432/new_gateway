"""
Routes for OGx message handling.

This module implements message handling as defined in OGx-1.txt:
- Message submission (To-Mobile/FW)
- Message retrieval (From-Mobile/RE)
- Message status tracking
- Transport-aware message routing

State Transitions (OGx-1.txt Section 4.3):
- Forward (FW) Messages:
    ACCEPTED -> SENDING_IN_PROGRESS -> RECEIVED/ERROR/DELIVERY_FAILED
    - SATELLITE: May timeout after 10 days
    - CELLULAR: May timeout after 120 minutes
    - Delayed send (IDP only): ACCEPTED -> WAITING -> SENDING_IN_PROGRESS

- Return (RE) Messages:
    Always in RECEIVED state when retrieved

Transport Types (OGx-1.txt Section 4.3.1):
- ANY (0): Use any available transport
- SATELLITE (1): Use satellite network only
- CELLULAR (2): Use cellular network only
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from httpx import HTTPError
from pydantic import BaseModel, Field

from Protexis_Command.api_ogx.config import APIEndpoint, TransportType
from Protexis_Command.api_ogx.services.auth.manager import OGxAuthManager, get_auth_manager
from Protexis_Command.api_protexis.clients.factory import get_OGx_client
from Protexis_Command.core.app_settings import Settings, get_settings
from Protexis_Command.protocol.ogx.constants.ogx_message_states import MessageState
from Protexis_Command.protocol.ogx.constants.ogx_message_types import MessageType
from Protexis_Command.protocol.ogx.validation.ogx_validation_exceptions import (
    OGxProtocolError,
    ValidationError,
)

router = APIRouter()


# Enhanced Pydantic models based on OGx spec
class OGxMessagePayload(BaseModel):
    """OGx message payload structure as defined in OGx-1.txt Section 5.1."""

    Name: str
    SIN: int
    MIN: int
    Fields: List[Dict[str, Any]]


class MessageRequest(BaseModel):
    """Enhanced message request matching OGx format (OGx-1.txt Section 5.2)."""

    DestinationID: str = Field(..., description="Terminal or broadcast ID")
    UserMessageID: Optional[int] = Field(None, description="Client's message ID")
    Payload: OGxMessagePayload
    TransportType: Optional[int] = Field(
        None, description="0=Any, 1=Satellite, 2=Cellular (OGx-1.txt Section 4.3.1)", ge=0, le=2
    )


class MessageResponse(BaseModel):
    """Enhanced response matching OGx format (OGx-1.txt Section 5.3)."""

    ID: Optional[int] = None
    ErrorID: Optional[int] = None
    State: MessageState = Field(
        ..., description="Message state from MessageState enum (OGx-1.txt Section 4.3)"
    )
    Type: MessageType = Field(..., description="Message type (FW_ACCEPTED, FW_RECEIVED, etc.)")
    DestinationID: str
    UserMessageID: Optional[int] = None
    OTAMessageSize: Optional[int] = None
    MessageUTC: Optional[str] = None


@router.post(APIEndpoint.SUBMIT_MESSAGE, response_model=MessageResponse)
async def submit_message(
    request: MessageRequest,
    _auth: OGxAuthManager = Depends(get_auth_manager),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Submit To-mobile message via OGx (OGx-1.txt Section 5.2)."""
    try:
        client = await get_OGx_client(settings)

        transport_type: Optional[TransportType] = None
        if request.TransportType is not None:
            try:
                transport_type = TransportType(request.TransportType)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid transport type: {str(e)}"
                ) from e

        try:
            response = await client.submit_message(
                destination_id=request.DestinationID,
                payload=request.Payload.dict(),
                user_message_id=request.UserMessageID,
                transport_type=transport_type,
            )

            return MessageResponse(
                Type=MessageType.FORWARD,  # Initial state for forward messages
                State=MessageState.ACCEPTED,
                **response,
            )
        except (HTTPError, OGxProtocolError) as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to submit message: {str(e)}"
            ) from e

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (HTTPError, OGxProtocolError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(APIEndpoint.GET_RE_MESSAGES, response_model=List[MessageResponse])
async def retrieve_messages(
    from_utc: str,
    _auth: OGxAuthManager = Depends(get_auth_manager),
    settings: Settings = Depends(get_settings),
) -> List[MessageResponse]:
    """Retrieve From-Mobile messages from OGx (OGx-1.txt Section 5.4)."""
    try:
        client = await get_OGx_client(settings)
        try:
            messages = await client.get_messages(from_utc=from_utc)
            return [
                MessageResponse(
                    Type=MessageType.RETURN,  # Return messages are always RECEIVED
                    State=MessageState.RECEIVED,
                    DestinationID=msg.get("SourceID", ""),
                    MessageUTC=msg.get("MessageUTC"),
                    **msg,
                )
                for msg in messages.get("Messages", [])
            ]
        except (HTTPError, OGxProtocolError) as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve messages: {str(e)}"
            ) from e

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (HTTPError, OGxProtocolError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(APIEndpoint.GET_FW_STATUSES + "/{message_id}", response_model=MessageResponse)
async def get_message_status(
    message_id: int,
    _auth: OGxAuthManager = Depends(get_auth_manager),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Get status of a specific message (OGx-1.txt Section 5.5).

    Message States (OGx-1.txt Section 4.3):
    - FW_ACCEPTED: Message accepted by OGx
    - FW_SENDING: Message sending in progress
    - FW_RECEIVED: Message acknowledged by destination
    - FW_ERROR: Submission error
    - FW_DELIVERY_FAILED: Message failed to deliver
    - FW_TIMED_OUT: Message timed out
    - FW_CANCELLED: Message cancelled
    - FW_WAITING: Queued for delayed send (IDP only)
    - FW_BROADCAST_SUBMITTED: Broadcast message transmitted
    """
    try:
        # Get OGx client
        client = await get_OGx_client(settings)

        # Get message status
        try:
            status = await client.get_message_status([message_id])
            return MessageResponse(**status)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get message status: {str(e)}"
            ) from e

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get message status: {str(e)}"
        ) from e
