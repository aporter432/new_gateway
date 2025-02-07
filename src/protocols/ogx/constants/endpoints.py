# src/protocols/ogx/constants/endpoints.py

"""OGWS API endpoints as defined in OGWS-1.txt.

This module defines all available OGWS API endpoints for:
- Authentication
- Message submission
- Message retrieval
- Information retrieval
- Status updates

Usage Examples:

    # Example 1: GET request to retrieve messages
    from protocols.ogx.constants import APIEndpoint, DEFAULT_CALLS_PER_MINUTE
    import httpx

    async def get_from_mobile_messages(
        access_token: str,
        from_utc: str,
        base_url: str = "https://ogws.orbcomm.com/api/v1.0"
    ) -> dict:
        '''Retrieve from-mobile messages after specified time.'''
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "FromUTC": from_utc,
            "IncludeTypes": True
        }
        url = f"{base_url}{APIEndpoint.GET_RE_MESSAGES}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    # Example 2: POST request to submit message
    async def submit_message(
        access_token: str,
        destination_id: str,
        payload: dict,
        base_url: str = "https://ogws.orbcomm.com/api/v1.0"
    ) -> dict:
        '''Submit to-mobile message to terminal.'''
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "DestinationID": destination_id,
            "Payload": payload
        }
        url = f"{base_url}{APIEndpoint.SUBMIT_MESSAGE}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()

Rate Limits (from OGWS-1.txt):
    - Default: 5 calls per 60 seconds per throttle group
    - Concurrent requests: Maximum 3 per account
    - Some limits configurable via Partner Support
    - HTTP 429 returned when exceeded
"""

from enum import Enum


class APIEndpoint(str, Enum):
    """OGWS API endpoints as defined in OGWS-1.txt.

    All endpoints require:
    - Bearer token authentication
    - API version in path (/api/v1.0)
    - Rate limit compliance (see limits.py for details)

    Authentication:
        - All endpoints except /auth/token require bearer token
        - Token format: "Bearer <access_token>"
    """

    # Authentication endpoints
    AUTH_TOKEN = "/auth/token"  # POST - Get bearer token
    AUTH_INVALIDATE = "/auth/invalidate_tokens"  # POST - Revoke all tokens

    # Message submission endpoints
    SUBMIT_MESSAGE = "/submit/messages"  # POST - Submit to-mobile message
    SUBMIT_MULTIPLE = "/submit/to_multiple"  # POST - Submit to multiple destinations
    SUBMIT_CANCEL = "/submit/cancellations"  # POST - Cancel pending messages

    # Message retrieval endpoints
    GET_FW_MESSAGES = "/get/fw_messages"  # GET - Get to-mobile messages
    GET_FW_STATUSES = "/get/fw_statuses"  # GET - Get message statuses
    GET_FW_STATUS_UPDATES = "/get/fw_status_updates"  # GET - Get status updates
    GET_RE_MESSAGES = "/get/re_messages"  # GET - Get from-mobile messages

    # Information endpoints
    GET_SERVICE_INFO = "/info/service"  # GET - Get service info and error codes
    GET_TERMINALS = "/info/terminals"  # GET - List all terminals
    GET_TERMINAL = "/info/terminal"  # GET - Get single terminal info
    GET_BROADCAST = "/info/broadcast"  # GET - List broadcast IDs

    # Subaccount endpoints
    GET_SUBACCOUNT_LIST = "/info/subaccount/list"  # GET - List subaccounts
    GET_SUBACCOUNT_TERMINALS = "/info/subaccount/terminals"  # GET - List subaccount terminals
    GET_SUBACCOUNT_BROADCAST = "/info/subaccount/broadcast"  # GET - List subaccount broadcasts

    # Subaccount status endpoints (added from OGWS-1.txt section 4.4.4-4.4.5)
    GET_SUBACCOUNT_FW_STATUS = "/get/subaccount/fw_status_updates"  # GET - Single subaccount status
    GET_ALL_SUBACCOUNT_FW_STATUS = (
        "/get/subaccount/all/fw_status_updates"  # GET - All subaccounts status
    )

    # Subaccount message endpoints (added from OGWS-1.txt section 4.4.7-4.4.8)
    GET_SUBACCOUNT_RE_MESSAGES = "/get/subaccount/re_messages"  # GET - Single subaccount messages
    GET_ALL_SUBACCOUNT_RE_MESSAGES = (
        "/get/subaccount/all/re_messages"  # GET - All subaccounts messages
    )
