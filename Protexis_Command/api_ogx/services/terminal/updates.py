"""Terminal updates service for OGx API.

This module provides the service layer for retrieving terminal updates information.
"""

import logging
from datetime import datetime
from typing import Optional

from Protexis_Command.api_ogx.config.ogx_endpoints import (
    GET_SUBACCOUNT_TERMINAL_UPDATES,
    GET_TERMINAL_UPDATES,
)
from Protexis_Command.api_ogx.models.terminal_updates import TerminalUpdate, TerminalUpdatesResponse
from Protexis_Command.api_ogx.services.auth.manager import OGxAuthManager
from Protexis_Command.api_ogx.services.common.ogx_requester import OGxRequester

logger = logging.getLogger(__name__)


class TerminalUpdatesService:
    """Service for retrieving terminal updates information."""

    def __init__(self, auth_manager: OGxAuthManager):
        """Initialize the terminal updates service.

        Args:
            auth_manager: Authentication manager for OGx API
        """
        self.auth_manager = auth_manager
        self.requester = OGxRequester(auth_manager)

    async def get_terminal_updates(
        self,
        from_utc: datetime,
        sub_account_id: Optional[str] = None,
        max_count: Optional[int] = None,
        include_deleted: bool = False,
    ) -> TerminalUpdatesResponse:
        """Get information about updated terminals.

        Args:
            from_utc: Start time for updates query
            sub_account_id: Sub-account identifier for filtering (optional)
            max_count: Maximum number of updates to return (optional)
            include_deleted: Whether to include deleted terminals

        Returns:
            List of terminal updates with pagination information
        """
        params = {
            "FromUTC": from_utc.isoformat(),
            "IncludeDeleted": include_deleted,
        }

        if max_count is not None:
            params["MaxCount"] = max_count

        if sub_account_id:
            params["SubAccountID"] = sub_account_id
            endpoint = GET_SUBACCOUNT_TERMINAL_UPDATES
            logger.info(
                f"Retrieving terminal updates for subaccount {sub_account_id} from {from_utc}"
            )
        else:
            endpoint = GET_TERMINAL_UPDATES
            logger.info(f"Retrieving terminal updates from {from_utc}")

        try:
            response = await self.requester.get(endpoint, params=params)

            if response.status_code == 200:
                data = response.json()

                # Transform the raw data into our response model
                updates = [
                    TerminalUpdate(
                        terminal_id=item.get("terminalID", ""),
                        sub_account_id=item.get("subAccountID"),
                        last_modified=item.get("lastModified"),
                        modification_type=item.get("modificationType", ""),
                        fields_modified=item.get("fieldsModified", []),
                    )
                    for item in data.get("updates", [])
                ]

                return TerminalUpdatesResponse(
                    updates=updates,
                    more_available=data.get("moreAvailable", False),
                    next_from_utc=data.get("nextFromUTC"),
                )
            else:
                logger.error(f"Failed to retrieve terminal updates: {response.status_code}")
                # Return empty response with error logging
                return TerminalUpdatesResponse(
                    updates=[],
                    more_available=False,
                    next_from_utc=None,
                )

        except Exception as e:
            logger.error(f"Error retrieving terminal updates: {e}")
            # Return empty response with error logging
            return TerminalUpdatesResponse(
                updates=[],
                more_available=False,
                next_from_utc=None,
            )
