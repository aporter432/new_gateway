"""Terminal operation services for OGx API.

This module provides service-layer functionality for terminal operation endpoints.
"""

import logging
from typing import List

from Protexis_Command.api_ogx.config.ogx_endpoints import APIEndpoint
from Protexis_Command.api_ogx.models.terminal import (
    SystemResetRequest,
    TerminalModeRequest,
    TerminalMuteRequest,
    TerminalOperationResponse,
    TerminalResetRequest,
)
from Protexis_Command.api_ogx.services.auth.manager import OGxAuthManager
from Protexis_Command.api_ogx.services.common.ogx_requester import OGxRequester

logger = logging.getLogger(__name__)


class TerminalOperationService:
    """Service for handling terminal operation requests."""

    def __init__(self, auth_manager: OGxAuthManager):
        """Initialize the terminal operation service.

        Args:
            auth_manager: Authentication manager for OGx API
        """
        self.auth_manager = auth_manager
        self.requester = OGxRequester(auth_manager)

    async def process_reset_requests(
        self, requests: List[TerminalResetRequest]
    ) -> List[TerminalOperationResponse]:
        """Process terminal reset requests.

        Args:
            requests: List of terminal reset requests

        Returns:
            List of operation responses with message IDs and status
        """
        logger.info(f"Processing {len(requests)} terminal reset requests")
        responses = []

        for request in requests:
            try:
                # Convert request to OGx API format
                ogx_request = request.dict(exclude_none=True)

                # Send request to OGx API
                response = await self.requester.post(APIEndpoint.TERMINAL_RESET, json=ogx_request)

                # Process response
                if response.status_code == 200:
                    data = response.json()
                    responses.append(
                        TerminalOperationResponse(
                            terminal_id=request.terminal_id,
                            message_id=data.get("messageId", ""),
                            status="SUBMITTED",
                            error=None,
                        )
                    )
                else:
                    responses.append(
                        TerminalOperationResponse(
                            terminal_id=request.terminal_id,
                            message_id=None,
                            status="FAILED",
                            error=f"Request failed with status {response.status_code}",
                        )
                    )
            except Exception as e:
                logger.error(f"Error processing reset request: {e}")
                responses.append(
                    TerminalOperationResponse(
                        terminal_id=request.terminal_id,
                        message_id=None,
                        status="FAILED",
                        error=str(e),
                    )
                )

        return responses

    async def process_system_reset_requests(
        self, requests: List[SystemResetRequest]
    ) -> List[TerminalOperationResponse]:
        """Process terminal system reset requests.

        Args:
            requests: List of terminal system reset requests

        Returns:
            List of operation responses with message IDs and status
        """
        logger.info(f"Processing {len(requests)} terminal system reset requests")
        responses = []

        for request in requests:
            try:
                # Convert request to OGx API format
                ogx_request = request.dict(exclude_none=True)

                # Send request to OGx API
                response = await self.requester.post(
                    APIEndpoint.TERMINAL_SYSRESET, json=ogx_request
                )

                # Process response
                if response.status_code == 200:
                    data = response.json()
                    responses.append(
                        TerminalOperationResponse(
                            terminal_id=request.terminal_id,
                            message_id=data.get("messageId", ""),
                            status="SUBMITTED",
                            error=None,
                        )
                    )
                else:
                    responses.append(
                        TerminalOperationResponse(
                            terminal_id=request.terminal_id,
                            message_id=None,
                            status="FAILED",
                            error=f"Request failed with status {response.status_code}",
                        )
                    )
            except Exception as e:
                logger.error(f"Error processing system reset request: {e}")
                responses.append(
                    TerminalOperationResponse(
                        terminal_id=request.terminal_id,
                        message_id=None,
                        status="FAILED",
                        error=str(e),
                    )
                )

        return responses

    async def process_mode_requests(
        self, requests: List[TerminalModeRequest]
    ) -> List[TerminalOperationResponse]:
        """Process terminal mode change requests.

        Args:
            requests: List of terminal mode change requests

        Returns:
            List of operation responses with message IDs and status
        """
        logger.info(f"Processing {len(requests)} terminal mode requests")
        responses = []

        for request in requests:
            try:
                # Convert request to OGx API format
                ogx_request = request.dict(exclude_none=True)

                # Send request to OGx API
                response = await self.requester.post(APIEndpoint.TERMINAL_MODE, json=ogx_request)

                # Process response
                if response.status_code == 200:
                    data = response.json()
                    responses.append(
                        TerminalOperationResponse(
                            terminal_id=request.terminal_id,
                            message_id=data.get("messageId", ""),
                            status="SUBMITTED",
                            error=None,
                        )
                    )
                else:
                    responses.append(
                        TerminalOperationResponse(
                            terminal_id=request.terminal_id,
                            message_id=None,
                            status="FAILED",
                            error=f"Request failed with status {response.status_code}",
                        )
                    )
            except Exception as e:
                logger.error(f"Error processing mode request: {e}")
                responses.append(
                    TerminalOperationResponse(
                        terminal_id=request.terminal_id,
                        message_id=None,
                        status="FAILED",
                        error=str(e),
                    )
                )

        return responses

    async def process_mute_requests(
        self, requests: List[TerminalMuteRequest]
    ) -> List[TerminalOperationResponse]:
        """Process terminal mute/unmute requests.

        Args:
            requests: List of terminal mute/unmute requests

        Returns:
            List of operation responses with message IDs and status
        """
        logger.info(f"Processing {len(requests)} terminal mute requests")
        responses = []

        for request in requests:
            try:
                # Convert request to OGx API format
                ogx_request = request.dict(exclude_none=True)

                # Send request to OGx API
                response = await self.requester.post(APIEndpoint.TERMINAL_MUTE, json=ogx_request)

                # Process response
                if response.status_code == 200:
                    data = response.json()
                    responses.append(
                        TerminalOperationResponse(
                            terminal_id=request.terminal_id,
                            message_id=data.get("messageId", ""),
                            status="SUBMITTED",
                            error=None,
                        )
                    )
                else:
                    responses.append(
                        TerminalOperationResponse(
                            terminal_id=request.terminal_id,
                            message_id=None,
                            status="FAILED",
                            error=f"Request failed with status {response.status_code}",
                        )
                    )
            except Exception as e:
                logger.error(f"Error processing mute request: {e}")
                responses.append(
                    TerminalOperationResponse(
                        terminal_id=request.terminal_id,
                        message_id=None,
                        status="FAILED",
                        error=str(e),
                    )
                )

        return responses
