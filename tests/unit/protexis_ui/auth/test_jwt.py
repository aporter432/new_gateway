"""Integration tests for JWT token handling.

This module tests:
- Token creation
- Token validation
- Token expiration
- Error handling
- Claim validation
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from jose import JWTError, jwt

from Protexis_Command.api_protexis.security.jwt import (
    ALGORITHM,
    TokenData,
    create_access_token,
    verify_token,
)
from Protexis_Command.core.app_settings import get_settings

settings = get_settings()


def test_create_access_token():
    """Test access token creation."""
    # Test basic token creation
    data: Dict[str, str] = {"sub": "test@example.com"}
    token = create_access_token(data)
    assert token is not None
    assert isinstance(token, str)

    # Decode and verify token contents
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "test@example.com"
    assert "exp" in payload


def test_create_access_token_with_expiry():
    """Test token creation with custom expiry."""
    data: Dict[str, str] = {"sub": "test@example.com"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta)

    # Verify expiration time
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert (exp - now).total_seconds() <= expires_delta.total_seconds()


def test_verify_valid_token():
    """Test verification of valid token."""
    test_email = "test@example.com"
    token = create_access_token({"sub": test_email})
    token_data = verify_token(token)

    assert isinstance(token_data, TokenData)
    assert token_data.email == test_email
    assert token_data.sub == test_email
    assert isinstance(token_data.exp, datetime)


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
    with patch("Protexis_Command.api_protexis.security.jwt.settings") as mock_settings:
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
    with patch("Protexis_Command.api_protexis.security.jwt.settings") as mock_settings:
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
    with patch("Protexis_Command.api_protexis.security.jwt.settings") as mock_settings:
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
    with patch("Protexis_Command.api_protexis.security.jwt.settings") as mock_settings:
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
    with patch("Protexis_Command.api_protexis.security.jwt.settings") as mock_settings:
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
    with patch("Protexis_Command.api_protexis.security.jwt.settings") as mock_settings:
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
    with patch("Protexis_Command.api_protexis.security.jwt.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.JWT_ALGORITHM = ALGORITHM

        token = create_access_token(token_data)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401
        assert expected_error in str(exc_info.value.detail)


def test_verify_expired_token():
    """Test verification of expired token."""
    # Create token that is already expired by setting expiration in the past
    past_time = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    test_email = "test@example.com"
    token = jwt.encode(
        {"sub": test_email, "exp": int(past_time.timestamp())},
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_verify_invalid_token():
    """Test verification of invalid token."""
    test_email = "test@example.com"
    # Test with malformed token
    with pytest.raises(HTTPException) as exc_info:
        verify_token("invalid_token")
    assert exc_info.value.status_code == 401

    # Test with token signed with different key
    wrong_token = jwt.encode(
        {"sub": test_email, "exp": datetime.utcnow() + timedelta(minutes=15)},
        "wrong_secret_key",
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_token(wrong_token)
    assert exc_info.value.status_code == 401


def test_token_without_email():
    """Test token without email claim."""
    # Create token without 'sub' claim but with valid expiry
    token = jwt.encode(
        {"exp": int((datetime.utcnow() + timedelta(minutes=15)).timestamp())},
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )

    # The token should be valid but result in None email
    token_data = verify_token(token)
    assert token_data.email is None
    assert isinstance(token_data.exp, datetime)


def test_token_with_invalid_algorithm():
    """Test token signed with invalid algorithm."""
    test_email = "test@example.com"
    # Create token with different algorithm
    wrong_alg_token = jwt.encode(
        {"sub": test_email, "exp": datetime.utcnow() + timedelta(minutes=15)},
        settings.JWT_SECRET_KEY,
        algorithm="HS512",  # Different from ALGORITHM
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_token(wrong_alg_token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_token_with_invalid_expiry_format():
    """Test token with invalid expiry format."""
    test_email = "test@example.com"
    # Create token with invalid expiry format
    token = jwt.encode(
        {"sub": test_email, "exp": "invalid_timestamp"},
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_token_without_expiry():
    """Test token without expiry claim."""
    test_email = "test@example.com"
    # Create token without expiry
    token = jwt.encode({"sub": test_email}, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_token_with_future_expiry():
    """Test token with future expiry (not yet valid)."""
    test_email = "test@example.com"
    # Create token with nbf (not before) claim in the future
    token = jwt.encode(
        {
            "sub": test_email,
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "nbf": datetime.utcnow() + timedelta(minutes=10),  # Token valid after 10 minutes
        },
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_create_access_token_failure():
    """Test token creation failure with non-JSON-serializable data."""

    class NonSerializable:
        """A class that cannot be JSON serialized."""

    data: Dict[str, Any] = {"sub": NonSerializable()}
    with pytest.raises(ValueError) as exc_info:
        create_access_token(data)
    assert "Failed to create access token" in str(exc_info.value)
    assert "not JSON serializable" in str(exc_info.value)


def test_create_access_token_jwt_error(monkeypatch):
    """Test token creation failure due to JWT error."""

    def mock_encode(*args, **kwargs):
        raise JWTError("JWT Error")

    monkeypatch.setattr(jwt, "encode", mock_encode)
    data: Dict[str, str] = {"sub": "test@example.com"}

    with pytest.raises(ValueError) as exc_info:
        create_access_token(data)
    assert "Failed to create access token: JWT Error" in str(exc_info.value)


def test_token_exact_expiry():
    """Test token that expires exactly at the current time."""
    test_email = "test@example.com"
    # Create token that expires in the past to ensure it's expired
    # Use a fixed time in the past to avoid timing issues
    current_time = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    token = jwt.encode(
        {
            "sub": test_email,
            "exp": int(current_time.timestamp()),
        },
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_verify_token_decode_error():
    """Test token verification with JWT decode error."""
    test_email = "test@example.com"
    # Create valid token first
    token = create_access_token({"sub": test_email})

    # Modify the token to make it invalid but still look like a JWT
    parts = token.split(".")
    if len(parts) == 3:
        # Modify the payload part (middle) to be invalid base64
        parts[1] = parts[1][:-1] + "$"
        invalid_token = ".".join(parts)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail


def test_create_access_token_none_data():
    """Test token creation with None data."""
    with pytest.raises(ValueError) as exc_info:
        create_access_token(None)  # type: ignore
    assert "Token data cannot be None or empty" in str(exc_info.value)


def test_create_access_token_empty_data():
    """Test token creation with empty data."""
    with pytest.raises(ValueError) as exc_info:
        create_access_token({})
    assert "Token data cannot be None or empty" in str(exc_info.value)


def test_create_access_token_missing_claims():
    """Test token creation with missing required claims."""
    with pytest.raises(ValueError) as exc_info:
        create_access_token({"other": "value"})
    assert "Token data must contain either 'sub' or 'email' claim" in str(exc_info.value)
