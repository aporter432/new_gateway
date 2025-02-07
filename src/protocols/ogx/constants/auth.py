"""Authentication and authorization constants as defined in OGWS-1.txt.

This module defines:
- Authorization roles for access control
- API throttling groups for rate limiting
- Authentication grant types for token generation

These constants control:
- User permissions and access levels
- API rate limits and throttling
- Authentication methods and token handling

Usage:
    from protocols.ogx.constants import AuthRole, ThrottleGroup, GrantType

    # Check user permissions
    def validate_access(user: dict, operation: str) -> None:
        role_permissions = {
            AuthRole.USER: {"submit_message", "get_messages", "get_status"},
            AuthRole.SUPERUSER: {"submit_message", "get_messages", "get_status", 
                               "manage_subaccounts", "view_all_messages"}
        }
        required_role = AuthRole.SUPERUSER if "subaccount" in operation else AuthRole.USER
        if user["role"] != required_role:
            raise PermissionError(f"Operation requires {required_role} access")

    # Apply rate limiting
    def check_rate_limit(group: ThrottleGroup, account: str) -> None:
        limits = {
            ThrottleGroup.INFO: 10,   # 10 calls per minute
            ThrottleGroup.GET: 5,     # 5 calls per minute
            ThrottleGroup.SEND: 2     # 2 calls per minute
        }
        if is_rate_exceeded(account, group, limits[group]):
            raise RateLimitError(f"{group} rate limit exceeded")

Implementation Notes:
    - Roles determine operation access
    - Rate limits apply per account
    - Token required for all requests
    - Some operations need elevated roles
    - Rate limits vary by operation type
    - Tokens expire after configured time
"""

from enum import Enum


class AuthRole(str, Enum):
    """Authorization roles for access control.

    Defines user access levels:
    - USER: Standard access to basic operations
    - SUPERUSER: Extended access including subaccount operations

    Usage:
        # Check operation permission
        def can_perform_operation(role: AuthRole, operation: str) -> bool:
            if operation.startswith("subaccount"):
                return role == AuthRole.SUPERUSER
            return True  # Basic operations allowed for all roles

        # Get role capabilities
        def get_role_capabilities(role: AuthRole) -> set[str]:
            base_caps = {"submit_message", "get_messages", "get_status"}
            if role == AuthRole.SUPERUSER:
                return base_caps | {"manage_subaccounts", "view_all_messages"}
            return base_caps

        # Validate subaccount access
        def validate_subaccount_access(user_role: AuthRole,
                                     subaccount_id: str) -> None:
            if user_role != AuthRole.SUPERUSER:
                raise PermissionError("Subaccount access requires SUPERUSER role")

    Implementation Notes:
        - Roles are assigned during account creation
        - Role elevation requires admin approval
        - USER is the default role
        - SUPERUSER can access subaccounts
        - Roles affect API endpoint access
        - Some operations require specific roles
        - Role checks occur at API entry
        - Invalid role access raises error
    """

    USER = "User"  # Standard access level
    SUPERUSER = "Superuser"  # Extended access with subaccount operations


class ThrottleGroup(str, Enum):
    """API throttling groups for rate limiting.

    Defines operation categories for rate limiting:
    - INFO: Information/metadata retrieval (highest limit)
    - GET: Data retrieval operations (medium limit)
    - SEND: Message submission operations (lowest limit)

    Usage:
        # Get rate limit for group
        def get_rate_limit(group: ThrottleGroup) -> int:
            limits = {
                ThrottleGroup.INFO: 10,  # 10 per minute
                ThrottleGroup.GET: 5,    # 5 per minute
                ThrottleGroup.SEND: 2    # 2 per minute
            }
            return limits.get(group, 1)  # Default 1 per minute

        # Track request count
        def track_request(group: ThrottleGroup, account_id: str) -> None:
            window = 60  # 60 second sliding window
            increment_counter(f"{account_id}:{group}", window)

        # Check if operation allowed
        def can_process_request(operation: str, account_id: str) -> bool:
            group = get_throttle_group(operation)
            return not is_rate_exceeded(account_id, group)

    Implementation Notes:
        - Limits tracked per account and group
        - Sliding window of 60 seconds
        - Counters reset after window
        - Exceeding limits returns 429
        - Some operations affect multiple groups
        - Limits are strictly enforced
        - Higher limits need approval
        - Bursting not supported
    """

    INFO = "INFO"  # Information methods
    GET = "GET"  # Get/retrieve methods
    SEND = "SEND"  # Submit/send methods


class GrantType(str, Enum):
    """Authentication grant types for token generation.

    Defines supported authentication methods:
    - CLIENT_CREDENTIALS: Client ID and secret authentication

    Usage:
        # Generate authentication token
        def get_auth_token(request: dict) -> str:
            if request["grant_type"] != GrantType.CLIENT_CREDENTIALS:
                raise AuthError("Invalid grant type")

            return generate_token(
                client_id=request["client_id"],
                client_secret=request["client_secret"]
            )

        # Validate token request
        def validate_token_request(grant_type: str) -> None:
            if grant_type != GrantType.CLIENT_CREDENTIALS:
                raise AuthError("Only client_credentials supported")

        # Check token expiry
        def is_token_valid(token: str) -> bool:
            token_data = decode_token(token)
            return (
                token_data["grant_type"] == GrantType.CLIENT_CREDENTIALS
                and not is_token_expired(token_data)
            )

    Implementation Notes:
        - Only client_credentials supported
        - Tokens required for all API calls
        - Tokens expire after configured time
        - Invalid tokens return 401
        - Tokens can be revoked
        - Include token in Authorization header
        - Token format is JWT
        - Refresh tokens not supported
    """

    CLIENT_CREDENTIALS = "client_credentials"  # Client ID and secret auth
