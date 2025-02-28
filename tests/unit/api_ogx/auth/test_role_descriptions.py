from collections.abc import Mapping

import pytest

from Protexis_Command.api.common.auth.RBA.role_descriptions import RoleDescriptions
from Protexis_Command.infrastructure.database.models.user import UserRole


def test_descriptions_exist():
    """Test that role descriptions dictionary exists and is properly structured."""
    assert RoleDescriptions.descriptions is not None
    assert isinstance(RoleDescriptions.descriptions, Mapping)
    assert len(RoleDescriptions.descriptions) > 0


def test_all_user_roles_have_descriptions():
    """Test that all UserRole enum values have corresponding descriptions."""
    for role in UserRole:
        assert role in RoleDescriptions.descriptions
        assert isinstance(RoleDescriptions.descriptions[role], str)
        assert len(RoleDescriptions.descriptions[role]) > 0


@pytest.mark.parametrize(
    "role,expected_description",
    [
        (UserRole.USER, "Basic user permissions"),
        (UserRole.ADMIN, "Full system administration permissions"),
        (UserRole.ACCOUNTING, "Accounting only permissions"),
        (UserRole.PROTEXIS_ADMINISTRATOR, "Allow normal administration functions"),
        (UserRole.PROTEXIS_VIEW, "Standard Protexis view role"),
        (UserRole.PROTEXIS_REQUEST_READ, "Send read commands"),
        (UserRole.PROTEXIS_REQUEST_WRITE, "Send write commands"),
        (UserRole.PROTEXIS_SITE_ADMIN, "Manage site administration"),
        (UserRole.PROTEXIS_TECH_ADMIN, "Manage site configurations"),
        (UserRole.PROTEXIS_ADMIN, "Site service admin and billing admin"),
    ],
)
def test_specific_role_descriptions(role, expected_description):
    """Test that each role has the correct description."""
    assert RoleDescriptions.get_description(role) == expected_description


def test_get_description_with_invalid_role():
    """Test get_description method with an invalid role."""

    # Create a mock role that doesn't exist in the descriptions
    class MockRole:
        def __str__(self):
            return "INVALID_ROLE"

    assert RoleDescriptions.get_description(MockRole()) == "Unknown role"


def test_get_all_roles_with_descriptions():
    """Test get_all_roles_with_descriptions method returns correct format and content."""
    result = RoleDescriptions.get_all_roles_with_descriptions()

    # Test the structure
    assert isinstance(result, list)
    assert len(result) == len(UserRole)

    # Test each item in the result
    for item in result:
        assert isinstance(item, dict)
        assert "role" in item
        assert "description" in item
        assert isinstance(item["role"], str)
        assert isinstance(item["description"], str)


def test_get_all_roles_with_descriptions_content():
    """Test the actual content of get_all_roles_with_descriptions."""
    result = RoleDescriptions.get_all_roles_with_descriptions()

    # Create a dictionary from the result for easy lookup
    result_dict = {item["role"]: item["description"] for item in result}

    # Verify each UserRole is present with correct description
    for role in UserRole:
        assert role.value in result_dict
        assert result_dict[role.value] == RoleDescriptions.get_description(role)


def test_descriptions_immutability():
    """Test that the descriptions dictionary cannot be modified at runtime."""
    original_descriptions = RoleDescriptions.descriptions.copy()

    # Attempt to modify the descriptions (this should not affect the original)
    try:
        RoleDescriptions.descriptions[UserRole.USER] = "Modified description"
    except (
        TypeError,
        AttributeError,
    ):  # MappingProxyType raises TypeError, some implementations might raise AttributeError
        pass  # Expected - descriptions should be immutable

    # Verify the original descriptions remain unchanged
    assert RoleDescriptions.descriptions == original_descriptions


def test_role_description_consistency():
    """Test that role descriptions are consistent across different access methods."""
    for role in UserRole:
        # Get description directly from dictionary
        direct_description = RoleDescriptions.descriptions[role]

        # Get description using get_description method
        method_description = RoleDescriptions.get_description(role)

        # Get description from all_roles_with_descriptions
        all_descriptions = RoleDescriptions.get_all_roles_with_descriptions()
        list_description = next(
            item["description"] for item in all_descriptions if item["role"] == role.value
        )

        # All three methods should return the same description
        assert direct_description == method_description == list_description


def test_role_values_in_get_all_roles():
    """Test that role values in get_all_roles_with_descriptions match UserRole values."""
    result = RoleDescriptions.get_all_roles_with_descriptions()
    role_values = {item["role"] for item in result}
    enum_values = {role.value for role in UserRole}

    assert role_values == enum_values
