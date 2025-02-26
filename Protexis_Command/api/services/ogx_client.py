"""OGx API client implementation."""

from typing import Any, Dict, List, Optional

from Protexis_Command.api.common.clients.base import BaseAPIClient
from Protexis_Command.api.config import APIEndpoint, TransportType


class OGxClient(BaseAPIClient):
    """Client for interacting with OGx API endpoints."""

    async def submit_message(
        self,
        destination_id: str,
        payload: Dict[str, Any],
        user_message_id: Optional[int] = None,
        transport_type: Optional[TransportType] = None,
    ) -> Dict[str, Any]:
        """Submit a message to a terminal.

        Args:
            destination_id: Terminal or broadcast ID
            payload: Message payload
            user_message_id: Optional client message ID
            transport_type: Optional transport type constraint

        Returns:
            Submission response data
        """
        data: Dict[str, Any] = {
            "DestinationID": destination_id,
            "Payload": payload,
        }
        if user_message_id is not None:
            data["UserMessageID"] = str(user_message_id)
        if transport_type is not None:
            data["TransportType"] = str(transport_type.value)

        response = await self.post(APIEndpoint.SUBMIT_MESSAGE, json_data=data)
        return await self.handle_response(response)

    async def get_messages(
        self,
        from_utc: str,
        include_types: bool = True,
        include_raw_payload: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve messages from terminals.

        Args:
            from_utc: High watermark timestamp
            include_types: Whether to include message types
            include_raw_payload: Whether to include raw payload

        Returns:
            Retrieved messages data
        """
        params = {
            "FromUTC": from_utc,
            "IncludeTypes": str(include_types).lower(),
            "IncludeRawPayload": str(include_raw_payload).lower(),
        }
        response = await self.get(APIEndpoint.GET_RE_MESSAGES, params=params)
        return await self.handle_response(response)

    async def get_message_status(self, message_ids: List[int]) -> Dict[str, Any]:
        """Get status of submitted messages.

        Args:
            message_ids: List of message IDs to check

        Returns:
            Message status data
        """
        params = {"IDList": ",".join(str(id) for id in message_ids)}
        response = await self.get(APIEndpoint.GET_FW_STATUSES, params=params)
        return await self.handle_response(response)

    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information and error codes.

        Returns:
            Service information data
        """
        response = await self.get(APIEndpoint.GET_SERVICE_INFO)
        return await self.handle_response(response)

    async def get_terminal_info(self, terminal_id: str) -> Dict[str, Any]:
        """Get information about a specific terminal.

        Args:
            terminal_id: Terminal ID to query

        Returns:
            Terminal information data
        """
        params = {"ID": terminal_id}
        response = await self.get(APIEndpoint.GET_TERMINAL, params=params)
        return await self.handle_response(response)
