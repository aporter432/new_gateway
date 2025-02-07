"""Authentication and authorization constants as defined in OGWS-1.txt.

This module defines:
- Authorization roles (section 3.2)
- Authentication grant types (section 4.1.1)

Usage Examples:

    # Example 1: Generate bearer token
    from protocols.ogx.constants import GrantType
    import httpx

    async def get_auth_token(
        client_id: str,
        client_secret: str,
        expires_in: int = 604800,  # 7 days in seconds
        base_url: str = "https://ogws.orbcomm.com/api/v1.0"
    ) -> dict:
        '''Get bearer token using client credentials.'''
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "expires_in": expires_in,
            "grant_type": GrantType.CLIENT_CREDENTIALS
        }
        url = f"{base_url}/auth/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                data=data
            )
            response.raise_for_status()
            return response.json()

    # Example 2: Check authorization role
    from protocols.ogx.constants import AuthRole, APIEndpoint

    def validate_endpoint_access(
        endpoint: APIEndpoint,
        role: AuthRole
    ) -> bool:
        '''Check if role can access endpoint.'''
        # Subaccount endpoints require SUPERUSER role
        if "subaccount" in endpoint:
            return role == AuthRole.SUPERUSER
        return True  # All other endpoints accessible to all roles
"""

from enum import Enum


class AuthRole(str, Enum):
    """Authorization roles as defined in OGWS-1.txt section 3.2.

    Attributes:
        USER: Default role, can access most customer interface endpoints
        SUPERUSER: Extended role, can access subaccount endpoints

    Notes:
        - USER role is default for all accounts
        - SUPERUSER required for subaccount operations
        - Invalid role access returns HTTP 403
    """

    USER = "User"  # Default role
    SUPERUSER = "Superuser"  # Required for subaccount access


class GrantType(str, Enum):
    """Authentication grant types as defined in OGWS-1.txt section 4.1.1.

    Attributes:
        CLIENT_CREDENTIALS: Client ID and secret authentication

    Notes:
        - Only client_credentials grant type supported
        - Default token expiry: 7 days
        - Maximum token expiry: 365 days
        - Content-Type must be application/x-www-form-urlencoded
        - Invalid tokens return HTTP 401
    """

    CLIENT_CREDENTIALS = "client_credentials"  # Only supported grant type
