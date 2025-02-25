"""Message handling routes for OGx protocol.

This module implements the API endpoints for message operations as defined in OGx-1.txt.
"""

from fastapi import APIRouter, HTTPException

from Protexis_Command.protocols.ogx.models.fields import Message
from Protexis_Command.protocols.ogx.models.ogx_messages import OGxMessage

router = APIRouter()


@router.post("/messages", response_model=dict)
async def submit_message(message: Message):
    """Submit a message to the OGx network.

    Args:
        message: The message to submit

    Returns:
        dict: Submission result
    """
    try:
        # Convert API model to protocol message using proper serialization
        protocol_message = OGxMessage.from_dict(message.model_dump(by_alias=True))

        # TODO: Implement message submission logic
        # Use protocol_message in submission logic
        return {"status": "submitted", "message_id": protocol_message.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/messages/{message_id}", response_model=Message)
async def get_message(message_id: str):
    """Retrieve a message by ID.

    Args:
        message_id: ID of the message to retrieve

    Returns:
        Message: The retrieved message
    """
    try:
        # TODO: Implement message retrieval logic
        # For now, return dummy data that matches the protocol format
        protocol_message = OGxMessage.from_dict(
            {"Name": "dummy_message", "SIN": 16, "MIN": 1, "IsForward": True, "Fields": []}
        )

        # Convert back to API model using snake_case internally
        return Message.model_validate(protocol_message.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
