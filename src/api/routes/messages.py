"""
This module contains the routes for the messages API.
It handles the sending and receiving of messages to and from devices.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel


# Placeholder for dependency injection (Auth, DB, etc.)
def get_current_user():
    return {"user": "placeholder_user"}


router = APIRouter()


# Pydantic models for request validation
class MessageRequest(BaseModel):
    device_id: str
    payload: Dict[str, Any]


class MessageResponse(BaseModel):
    success: bool
    message: str


# Placeholder functions to delegate logic
def determine_protocol(device_id: str) -> str:
    """Determine if the device is MTWS (cellular) or IGWS (satellite)."""
    return "MTWS" if device_id.startswith("91") else "IGWS"


def send_message_via_protocol(device_id: str, payload: Dict[str, Any]) -> bool:
    """Placeholder for actual message sending logic."""
    protocol = determine_protocol(device_id)
    print(f"Sending message via {protocol}: {payload}")
    return True


def get_pending_messages(device_id: str) -> list:
    """Placeholder for retrieving pending messages."""
    return [{"id": "msg_123", "content": "Test message"}]


@router.post("/messages/send", response_model=MessageResponse)
def send_message(request: MessageRequest, user=Depends(get_current_user)):
    """Handles sending messages and routes them based on protocol."""
    success = send_message_via_protocol(request.device_id, request.payload)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message.")
    return {"success": True, "message": "Message sent successfully."}


@router.get("/messages/pending/{device_id}", response_model=Dict[str, Any])
def get_messages(device_id: str, user=Depends(get_current_user)):
    """Retrieves pending messages for a given device."""
    messages = get_pending_messages(device_id)
    return {"device_id": device_id, "messages": messages}


@router.post("/messages/from-device", response_model=MessageResponse)
def receive_message_from_device(request: MessageRequest, user=Depends(get_current_user)):
    """Handles messages submitted by a device."""
    print(f"Received message from device {request.device_id}: {request.payload}")
    return {"success": True, "message": "Message received."}
