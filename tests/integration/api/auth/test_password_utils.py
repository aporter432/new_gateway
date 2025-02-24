"""Integration tests for password utilities.

This module tests:
- Password hashing
- Password validation
- Password verification
"""

import pytest

from Protexis_Command.api_protexis.security.password import (
    get_password_hash,
    validate_password,
    verify_password,
)


def test_password_hashing():
    """Test password hashing functionality."""
    # Test basic hashing
    password = "TestPass123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > 0

    # Test different passwords produce different hashes
    other_hash = get_password_hash("DifferentPass123!")
    assert hashed != other_hash


def test_password_verification():
    """Test password verification functionality."""
    password = "TestPass123!"
    wrong_password = "WrongPass123!"
    hashed = get_password_hash(password)

    # Test correct password verifies
    assert verify_password(password, hashed) is True

    # Test wrong password fails
    assert verify_password(wrong_password, hashed) is False


@pytest.mark.parametrize(
    "password,is_valid",
    [
        ("Short1!", False),  # Too short
        ("a" * 101 + "A1!", False),  # Too long
        ("lowercase123!", False),  # No uppercase
        ("UPPERCASE123!", False),  # No lowercase
        ("NoNumbers!", False),  # No numbers
        ("NoSpecial123", False),  # No special characters
        ("ValidPass123!", True),  # Valid password
        ("Another@Valid2", True),  # Valid password
        ("Complex!Pass1", True),  # Valid password
    ],
)
def test_password_validation(password: str, is_valid: bool):
    """Test password validation rules.

    Args:
        password: Password to test
        is_valid: Whether password should be valid
    """
    validation_error = validate_password(password)
    if is_valid:
        assert validation_error is None, f"Password should be valid: {password}"
    else:
        assert validation_error is not None, f"Password should be invalid: {password}"


def test_password_validation_messages():
    """Test specific validation error messages."""
    # Test length requirements
    assert "must be at least 8 characters" in validate_password("Short1!")
    assert "must not exceed 100 characters" in validate_password("a" * 101 + "A1!")

    # Test character requirements
    assert "must contain at least one uppercase letter" in validate_password("lowercase123!")
    assert "must contain at least one lowercase letter" in validate_password("UPPERCASE123!")
    assert "must contain at least one number" in validate_password("NoNumbers!")
    assert "must contain at least one special character" in validate_password("NoSpecial123")
