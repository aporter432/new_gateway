"""Unit tests for JWT token handling.

This module tests:
- Token creation
- Token validation
- Token expiration
- Error handling
- Claim validation
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from api.security.jwt import ALGORITHM, TokenData, create_access_token, verify_token
from fastapi import HTTPException
from jose import jwt


@pytest.fixture
def valid_token_data():
    """Sample valid token data."""
    return {
        "sub": "test@example.com",
        "email": "test@example.com",
    }


def test_create_access_token_success(valid_token_data):
    """Test successful token creation.

    Verifies:
    - Token is created
    - Token can be decoded
    - Claims are properly set
    - Expiration is set
    """
    with patch("api.security.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = ALGORITHM

        # Create token
        token = create_access_token(valid_token_data)

        # Verify token structure
        assert isinstance(token, str)

        # Decode and verify claims
        payload = jwt.decode(token, mock_settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])

        # Check claims
        assert payload["sub"] == valid_token_data["sub"]
        assert payload["email"] == valid_token_data["email"]
        assert "exp" in payload


def test_create_access_token_with_expiration(valid_token_data):
    """Test token creation with custom expiration.

    Verifies:
    - Custom expiration is set
    - Expiration time is correct
    """
    with patch("api.security.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = ALGORITHM

        expires_delta = timedelta(minutes=15)
        token = create_access_token(valid_token_data, expires_delta)

        # Decode and verify expiration
        payload = jwt.decode(token, mock_settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])

        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.now() + expires_delta

        # Allow 1 second tolerance for test execution time
        assert abs((exp_time - expected_exp).total_seconds()) < 1


def test_create_access_token_invalid_data():
    """Test token creation with invalid data.

    Verifies:
    - Error handling for invalid input
    - Validation of required fields
    """
    with pytest.raises(ValueError):
        create_access_token({})  # Empty dict instead of None

    with pytest.raises(ValueError):
        create_access_token({})


def test_verify_token_success(valid_token_data):
    """Test successful token verification.

    Verifies:
    - Valid token is verified
    - Token data is correctly extracted
    - Claims are properly validated
    """
    with patch("api.security.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = ALGORITHM

        # Create and verify token
        token = create_access_token(valid_token_data)
        token_data = verify_token(token)

        # Verify extracted data
        assert isinstance(token_data, TokenData)
        assert token_data.email == valid_token_data["email"]
        assert token_data.sub == valid_token_data["sub"]


def test_verify_token_expired(valid_token_data):
    """Test expired token verification.

    Verifies:
    - Expired tokens are rejected
    - Proper error is raised
    """
    with patch("api.security.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = ALGORITHM

        # Create token that's already expired
        expires_delta = timedelta(minutes=-1)
        token = create_access_token(valid_token_data, expires_delta)

        # Verify expired token raises error
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


def test_verify_token_invalid_signature(valid_token_data):
    """Test token with invalid signature.

    Verifies:
    - Tampered tokens are rejected
    - Proper error is raised
    """
    with patch("api.security.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = ALGORITHM

        # Create token
        token = create_access_token(valid_token_data)

        # Tamper with token
        tampered_token = token[:-1] + ("1" if token[-1] == "0" else "0")

        # Verify tampered token raises error
        with pytest.raises(HTTPException) as exc_info:
            verify_token(tampered_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


def test_verify_token_missing_claims():
    """Test token with missing required claims.

    Verifies:
    - Tokens without required claims are rejected
    - Proper error is raised
    """
    with patch("api.security.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = ALGORITHM

        # Create token without required claims
        token = create_access_token({"random": "data"})

        # Verify token with missing claims raises error
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


def test_verify_token_invalid_format():
    """Test invalid token format.

    Verifies:
    - Malformed tokens are rejected
    - Proper error is raised
    """
    invalid_tokens = [
        "",  # Empty token
        "not.a.jwt",  # Malformed JWT
        "invalid",  # Random string
        "eyJ0.invalid.token",  # Partial JWT
    ]

    for invalid_token in invalid_tokens:
        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


@pytest.mark.parametrize(
    "token_data,expected_error",
    [
        ({"sub": "", "email": "test@example.com"}, "Could not validate credentials"),
        ({"sub": "test@example.com", "email": ""}, "Could not validate credentials"),
        ({"sub": "test@example.com"}, "Could not validate credentials"),
    ],
)
def test_verify_token_invalid_claims(token_data, expected_error):
    """Test tokens with invalid claim values.

    Verifies:
    - Tokens with invalid claim values are rejected
    - Proper error messages are returned

    Args:
        token_data: Test token data
        expected_error: Expected error message
    """
    with patch("api.security.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = ALGORITHM

        token = create_access_token(token_data)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401
        assert expected_error in str(exc_info.value.detail)
