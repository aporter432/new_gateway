from types import MappingProxyType

from Protexis_Command.infrastructure.database.models.user import UserRole


class RoleDescriptions:
    """Descriptions for user roles."""

    _descriptions = {
        UserRole.USER: "Basic user permissions",
        UserRole.ADMIN: "Full system administration permissions",
        UserRole.ACCOUNTING: "Accounting only permissions",
        UserRole.PROTEXIS_ADMINISTRATOR: "Allow normal administration functions",
        UserRole.PROTEXIS_VIEW: "Standard Protexis view role",
        UserRole.PROTEXIS_REQUEST_READ: "Send read commands",
        UserRole.PROTEXIS_REQUEST_WRITE: "Send write commands",
        UserRole.PROTEXIS_SITE_ADMIN: "Manage site administration",
        UserRole.PROTEXIS_TECH_ADMIN: "Manage site configurations",
        UserRole.PROTEXIS_ADMIN: "Site service admin and billing admin",
    }

    descriptions = MappingProxyType(_descriptions)

    @classmethod
    def get_description(cls, role: UserRole) -> str:
        """Get description for a role."""
        return cls.descriptions.get(role, "Unknown role")

    @classmethod
    def get_all_roles_with_descriptions(cls) -> list[dict]:
        """Get all roles with their descriptions."""
        return [{"role": role.value, "description": cls.get_description(role)} for role in UserRole]
