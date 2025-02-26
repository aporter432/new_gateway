"""Terminal updates routes for OGx API.

This module implements endpoints for retrieving terminal updates information.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from Protexis_Command.api.common.auth.manager import OGxAuthManager, get_auth_manager
from Protexis_Command.api.protocols.ogx.models.terminal_updates import TerminalUpdatesResponse
from Protexis_Command.api.services.terminal.updates import TerminalUpdatesService

router = APIRouter(tags=["terminal-updates"])


@router.get("/info/terminal_updates", response_model=TerminalUpdatesResponse)
async def get_terminal_updates(
    from_utc: datetime = Query(..., description="Start time for updates query"),
    max_count: Optional[int] = Query(None, description="Maximum number of updates to return"),
    include_deleted: bool = Query(False, description="Whether to include deleted terminals"),
    auth_manager: OGxAuthManager = Depends(get_auth_manager),
) -> TerminalUpdatesResponse:
    """Get information about updated terminals.

    This endpoint returns information about terminals that have been updated since
    the specified time.

    Args:
        from_utc: Start time for updates query
        max_count: Maximum number of updates to return
        include_deleted: Whether to include deleted terminals
        auth_manager: Authentication manager for OGx API

    Returns:
        List of terminal updates with pagination information
    """
    updates_service = TerminalUpdatesService(auth_manager)
    return await updates_service.get_terminal_updates(
        from_utc=from_utc,
        max_count=max_count,
        include_deleted=include_deleted,
    )


@router.get("/info/subaccount/terminal_updates", response_model=TerminalUpdatesResponse)
async def get_subaccount_terminal_updates(
    sub_account_id: str = Query(..., description="Sub-account identifier"),
    from_utc: datetime = Query(..., description="Start time for updates query"),
    max_count: Optional[int] = Query(None, description="Maximum number of updates to return"),
    include_deleted: bool = Query(False, description="Whether to include deleted terminals"),
    auth_manager: OGxAuthManager = Depends(get_auth_manager),
) -> TerminalUpdatesResponse:
    """Get information about updated terminals for a specific subaccount.

    This endpoint returns information about terminals that have been updated since
    the specified time for a specific subaccount.

    Args:
        sub_account_id: Sub-account identifier
        from_utc: Start time for updates query
        max_count: Maximum number of updates to return
        include_deleted: Whether to include deleted terminals
        auth_manager: Authentication manager for OGx API

    Returns:
        List of terminal updates with pagination information
    """
    updates_service = TerminalUpdatesService(auth_manager)
    return await updates_service.get_terminal_updates(
        from_utc=from_utc,
        sub_account_id=sub_account_id,
        max_count=max_count,
        include_deleted=include_deleted,
    )
