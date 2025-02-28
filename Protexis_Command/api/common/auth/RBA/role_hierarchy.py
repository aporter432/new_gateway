"""
This module defines the role hierarchy for the Protexis system.
It provides a way to check if a user with a given role can manage another role.
"""


class RoleHierarchy:
    """Manages role hierarchy and permission level checks for the Protexis system."""

    ROLE_LEVELS = {
        "protexis_administrator": 1,  # Highest permissions
        "accounting": 2,
        "protexis_site_admin": 3,
        "protexis_tech_admin": 4,
        "protexis_request_read": 5,
        "protexis_request_write": 6,
        "protexis_view": 7,  # Lowest permissions
    }

    @classmethod
    def can_manage_role(cls, current_role: str, target_role: str) -> bool:
        """Check if a user with current_role can manage users with target_role."""
        current_level = cls.ROLE_LEVELS.get(current_role)
        target_level = cls.ROLE_LEVELS.get(target_role)

        if current_level is None or target_level is None:
            return False

        # Can only manage roles with higher level numbers (lower permissions)
        return current_level < target_level
