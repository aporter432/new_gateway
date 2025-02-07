# src/protocols/ogx/constants/endpoints.py

"""OGWS API endpoints as defined in OGWS-1.txt.

This module defines all available OGWS API endpoints for:
- Authentication
- Message submission
- Message retrieval
- Information retrieval
- Status updates

Usage:
    from protocols.ogx.constants import APIEndpoint

    def construct_url(endpoint: APIEndpoint, base_url: str) -> str:
        return f"{base_url}{endpoint.value}"
"""



from enum import Enum


class APIEndpoint(str, Enum):
    """OGWS API endpoints.
    
    All endpoints require:
    - Bearer token authentication
    - API version in path
    - Rate limit compliance
    """
    
    # Authentication endpoints
    AUTH_TOKEN = "/auth/token"
    AUTH_INVALIDATE = "/auth/invalidate_tokens"
    
    # Message submission endpoints
    SUBMIT_MESSAGE = "/submit/messages"
    SUBMIT_MULTIPLE = "/submit/to_multiple"
    SUBMIT_CANCEL = "/submit/cancellations"
    
    # Message retrieval endpoints
    GET_FW_MESSAGES = "/get/fw_messages"
    GET_FW_STATUSES = "/get/fw_statuses"
    GET_FW_STATUS_UPDATES = "/get/fw_status_updates"
    GET_RE_MESSAGES = "/get/re_messages"
    
    # Information endpoints
    GET_SERVICE_INFO = "/info/service"
    GET_TERMINALS = "/info/terminals"
    GET_TERMINAL = "/info/terminal"
    GET_BROADCAST = "/info/broadcast"
    
    # Subaccount endpoints
    GET_SUBACCOUNT_LIST = "/info/subaccount/list"
    GET_SUBACCOUNT_TERMINALS = "/info/subaccount/terminals"
    GET_SUBACCOUNT_BROADCAST = "/info/subaccount/broadcast"