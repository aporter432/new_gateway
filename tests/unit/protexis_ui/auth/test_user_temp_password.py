"""Unit tests for temporary password functionality in user authentication."""

from unittest.mock import Mock

import pytest
from pydantic import BaseModel

from Protexis_Command.api.common.auth.password import (
    generate_secure_password,
    get_password_hash,
    validate_password,
    verify_password,
)


# Test schema classes to avoid circular imports
class UserCreateWithGeneratedPassword(BaseModel):
    email: str
    name: str
    role: str
    generated_password: str


@pytest.fixture
def mock_email_service():
    """Provide a mock email service."""
    mock_service = Mock()
    mock_service.send_email.return_value = True
    return mock_service


@pytest.fixture
def mock_user_data():
    """Provide mock user data for testing."""
    return {
        "email": "tempuser@example.com",
        "name": "Temp User",
        "role": "protexis_view",
        "generated_password": generate_secure_password(),
    }


@pytest.mark.unit
def test_temporary_password_login(mock_user_data, mock_email_service):
    """Test the temporary password login workflow."""
    # Simulate user creation with generated_password
    user = UserCreateWithGeneratedPassword(**mock_user_data)
    assert user.email == mock_user_data["email"]
    assert user.name == mock_user_data["name"]
    assert user.role == mock_user_data["role"]

    # Simulate sending email with generated password
    email_sent = mock_email_service.send_email(
        recipient=user.email,
        subject="Your Temporary Password",
        body=f"Your temporary password is: {mock_user_data['generated_password']}",
    )
    assert email_sent

    # Simulate user login with temporary password
    hashed_password = get_password_hash(mock_user_data["generated_password"])
    assert verify_password(mock_user_data["generated_password"], hashed_password)


@pytest.mark.unit
def test_temporary_password_expiration(mock_user_data):
    """Test temporary password expiration behavior."""
    # Create an invalid password to simulate expiration
    expired_password = "ExpiredPass123!"
    hashed_password = get_password_hash(mock_user_data["generated_password"])

    # Verify that the expired/invalid password fails
    assert not verify_password(expired_password, hashed_password)


@pytest.mark.unit
def test_user_sets_new_password(mock_user_data):
    """Test the process of users setting their permanent password."""
    # Simulate user changing password before expiration
    new_password = "NewPass123!"
    assert validate_password(new_password) is None

    # Simulate updating password in the system
    hashed_new_password = get_password_hash(new_password)
    assert verify_password(new_password, hashed_new_password)

    # Verify old password no longer works
    assert not verify_password(mock_user_data["generated_password"], hashed_new_password)
