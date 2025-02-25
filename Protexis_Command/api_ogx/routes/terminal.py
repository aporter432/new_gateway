"""Terminal operation routes for OGx API.

This module implements terminal operation endpoints as defined in the OGx-1.txt specification:
- Terminal reset
- Terminal system reset
- Terminal mode change
- Terminal mute/unmute
"""

from typing import List

from fastapi import APIRouter, Depends

from Protexis_Command.api_ogx.models.terminal import (
    SystemResetRequest,
    TerminalModeRequest,
    TerminalMuteRequest,
    TerminalOperationResponse,
    TerminalResetRequest,
)
from Protexis_Command.api_ogx.services.auth.manager import OGxAuthManager, get_auth_manager
from Protexis_Command.api_ogx.services.terminal.operations import TerminalOperationService

router = APIRouter(tags=["terminal"])


@router.post("/terminal/reset", response_model=List[TerminalOperationResponse])
async def reset_terminal(
    requests: List[TerminalResetRequest],
    auth_manager: OGxAuthManager = Depends(get_auth_manager),
) -> List[TerminalOperationResponse]:
    """Submit a 'reset' message to destination terminals.

    This endpoint allows resetting of terminal hardware or application software.

    Args:
        requests: List of terminal reset requests
        auth_manager: Authentication manager for OGx API

    Returns:
        List of operation responses with message IDs and status
    """
    terminal_service = TerminalOperationService(auth_manager)
    return await terminal_service.process_reset_requests(requests)


@router.post("/terminal/sysreset", response_model=List[TerminalOperationResponse])
async def system_reset_terminal(
    requests: List[SystemResetRequest],
    auth_manager: OGxAuthManager = Depends(get_auth_manager),
) -> List[TerminalOperationResponse]:
    """Submit a system 'reset' message to destination terminals.

    This endpoint allows advanced system reset operations with various parameters.
    Requires special provisioning permissions.

    Args:
        requests: List of terminal system reset requests
        auth_manager: Authentication manager for OGx API

    Returns:
        List of operation responses with message IDs and status
    """
    # TODO: Add role-based access control for provisioning
    terminal_service = TerminalOperationService(auth_manager)
    return await terminal_service.process_system_reset_requests(requests)


@router.post("/terminal/mode", response_model=List[TerminalOperationResponse])
async def set_terminal_mode(
    requests: List[TerminalModeRequest],
    auth_manager: OGxAuthManager = Depends(get_auth_manager),
) -> List[TerminalOperationResponse]:
    """Submit a 'mode' message to destination terminals.

    This endpoint allows changing terminal operation mode and wakeup intervals.

    Args:
        requests: List of terminal mode change requests
        auth_manager: Authentication manager for OGx API

    Returns:
        List of operation responses with message IDs and status
    """
    terminal_service = TerminalOperationService(auth_manager)
    return await terminal_service.process_mode_requests(requests)


@router.post("/terminal/mute", response_model=List[TerminalOperationResponse])
async def mute_terminal(
    requests: List[TerminalMuteRequest],
    auth_manager: OGxAuthManager = Depends(get_auth_manager),
) -> List[TerminalOperationResponse]:
    """Submit a 'mute' message to destination terminals.

    This endpoint allows muting or unmuting terminals to control message transmission.

    Args:
        requests: List of terminal mute/unmute requests
        auth_manager: Authentication manager for OGx API

    Returns:
        List of operation responses with message IDs and status
    """
    terminal_service = TerminalOperationService(auth_manager)
    return await terminal_service.process_mute_requests(requests)
