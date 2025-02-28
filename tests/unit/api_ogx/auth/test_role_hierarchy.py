import pytest

from Protexis_Command.api.common.auth.RBA.role_hierarchy import RoleHierarchy


def test_role_hierarchy_levels_exist():
    """Test that role hierarchy levels are properly defined."""
    assert RoleHierarchy.ROLE_LEVELS is not None
    assert isinstance(RoleHierarchy.ROLE_LEVELS, dict)
    assert len(RoleHierarchy.ROLE_LEVELS) > 0


def test_protexis_administrator_highest_permission():
    """Test that protexis_administrator has the highest permission level (lowest number)."""
    admin_level = RoleHierarchy.ROLE_LEVELS["protexis_administrator"]
    assert admin_level == 1
    for role, level in RoleHierarchy.ROLE_LEVELS.items():
        if role != "protexis_administrator":
            assert level > admin_level


def test_protexis_view_lowest_permission():
    """Test that protexis_view has the lowest permission level (highest number)."""
    view_level = RoleHierarchy.ROLE_LEVELS["protexis_view"]
    assert view_level == 7
    for role, level in RoleHierarchy.ROLE_LEVELS.items():
        if role != "protexis_view":
            assert level < view_level


@pytest.mark.parametrize(
    "current_role,target_role,expected",
    [
        ("protexis_administrator", "accounting", True),
        ("protexis_administrator", "protexis_view", True),
        ("accounting", "protexis_site_admin", True),
        ("protexis_site_admin", "protexis_tech_admin", True),
        ("protexis_tech_admin", "protexis_request_read", True),
        ("protexis_request_read", "protexis_request_write", True),
        ("protexis_request_write", "protexis_view", True),
        # Test cases where management should not be allowed
        ("protexis_view", "protexis_administrator", False),
        ("protexis_request_write", "protexis_request_read", False),
        ("protexis_tech_admin", "protexis_site_admin", False),
        ("accounting", "protexis_administrator", False),
        ("protexis_view", "protexis_view", False),
    ],
)
def test_can_manage_role_valid_roles(current_role, target_role, expected):
    """Test can_manage_role with various valid role combinations."""
    assert RoleHierarchy.can_manage_role(current_role, target_role) == expected


def test_can_manage_role_invalid_current_role():
    """Test can_manage_role with invalid current role."""
    assert not RoleHierarchy.can_manage_role("invalid_role", "protexis_view")


def test_can_manage_role_invalid_target_role():
    """Test can_manage_role with invalid target role."""
    assert not RoleHierarchy.can_manage_role("protexis_administrator", "invalid_role")


def test_can_manage_role_both_invalid_roles():
    """Test can_manage_role with both roles invalid."""
    assert not RoleHierarchy.can_manage_role("invalid_role1", "invalid_role2")


def test_role_hierarchy_order():
    """Test that the role hierarchy is properly ordered."""
    expected_order = [
        "protexis_administrator",  # Level 1
        "accounting",  # Level 2
        "protexis_site_admin",  # Level 3
        "protexis_tech_admin",  # Level 4
        "protexis_request_read",  # Level 5
        "protexis_request_write",  # Level 6
        "protexis_view",  # Level 7
    ]

    # Verify that each role has a higher level number than the previous one
    for i in range(len(expected_order) - 1):
        current_role = expected_order[i]
        next_role = expected_order[i + 1]
        assert RoleHierarchy.ROLE_LEVELS[current_role] < RoleHierarchy.ROLE_LEVELS[next_role]


@pytest.mark.parametrize(
    "role,expected_level",
    [
        ("protexis_administrator", 1),
        ("accounting", 2),
        ("protexis_site_admin", 3),
        ("protexis_tech_admin", 4),
        ("protexis_request_read", 5),
        ("protexis_request_write", 6),
        ("protexis_view", 7),
    ],
)
def test_role_specific_levels(role, expected_level):
    """Test that each role has the correct permission level."""
    assert RoleHierarchy.ROLE_LEVELS[role] == expected_level
