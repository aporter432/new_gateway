"""Unit tests for JWT token handling.

This module tests the JWT token handling logic with mocked JWT operations.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException, status
from jose import JWTError

from Protexis_Command.api.common.auth.jwt import (
    ALGORITHM,
    REVOKED_TOKENS,
    TokenData,
    create_access_token,
    revoke_token,
    verify_token,
)


@pytest.fixture
def mock_jwt():
    """Mock JWT encode/decode operations."""
    with patch("Protexis_Command.api.common.auth.jwt.jwt") as mock:
        yield mock


@pytest.fixture
def mock_settings():
    """Mock app settings."""
    with patch("Protexis_Command.api.common.auth.jwt.settings") as mock:
        mock.JWT_SECRET_KEY = "test_key"
        mock.JWT_ALGORITHM = ALGORITHM
        yield mock


@pytest.fixture
def valid_token_data():
    """Sample valid token data."""
    return {
        "sub": "test@example.com",
        "email": "test@example.com",
    }


def test_create_access_token_success(mock_jwt, mock_settings, valid_token_data):
    """Test successful token creation with mocked JWT."""
    # Setup mock
    mock_jwt.encode.return_value = "mock.jwt.token"

    # Create token
    token = create_access_token(valid_token_data)

    # Verify mock was called correctly
    assert token == "mock.jwt.token"
    mock_jwt.encode.assert_called_once()
    call_args = mock_jwt.encode.call_args
    encoded_data = call_args[0][0]  # First positional arg is data
    assert "exp" in encoded_data  # Verify expiration was added
    assert isinstance(encoded_data["exp"], int)  # Verify exp is timestamp
    assert call_args[0][1] == mock_settings.JWT_SECRET_KEY  # Second positional arg is secret
    assert call_args[0][2] == ALGORITHM  # Third positional arg is algorithm


def test_create_access_token_with_expiry(mock_jwt):
    """Test token creation with custom expiry."""
    # Setup
    data = {"sub": "test@example.com"}
    expires_delta = timedelta(minutes=15)
    expected_exp = int((datetime.now(timezone.utc) + expires_delta).timestamp())

    # Create token - we don't use the token directly but it must be created
    create_access_token(data, expires_delta)

    # Verify expiration was set correctly
    call_args = mock_jwt.encode.call_args
    token_exp = call_args[0][0]["exp"]  # exp is in the data dict
    assert abs(token_exp - expected_exp) <= 1  # Allow 1 second difference


def test_verify_valid_token(mock_jwt, valid_token_data, mock_settings):
    """Test verification of valid token with mocked JWT."""
    # Setup mock with exp claim
    mock_data = valid_token_data.copy()
    mock_data["exp"] = int(datetime.now(timezone.utc).timestamp()) + 300
    mock_jwt.decode.return_value = mock_data

    # Verify token
    token_data = verify_token("mock.token")

    # Verify results
    assert isinstance(token_data, TokenData)
    assert token_data.email == valid_token_data["email"]
    assert token_data.sub == valid_token_data["sub"]
    mock_jwt.decode.assert_called_once_with(
        "mock.token",
        mock_settings.JWT_SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"verify_exp": True},  # key is positional
    )


def test_verify_token_expired(mock_jwt):
    """Test expired token verification with mocked JWT."""
    # Setup mock to raise JWTError
    mock_jwt.decode.side_effect = JWTError("Token expired")

    # Verify expired token raises error
    with pytest.raises(HTTPException) as exc_info:
        verify_token("mock.token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in str(exc_info.value.detail)


def test_verify_token_invalid_signature(mock_jwt):
    """Test token with invalid signature using mocked JWT."""
    # Setup mock to raise JWTError
    mock_jwt.decode.side_effect = JWTError("Invalid signature")

    # Verify tampered token raises error
    with pytest.raises(HTTPException) as exc_info:
        verify_token("mock.token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in str(exc_info.value.detail)


def test_verify_token_missing_claims(mock_jwt):
    """Test token with missing required claims."""
    # Setup mock to return token with only exp claim
    mock_jwt.decode.return_value = {
        "exp": int(datetime.now(timezone.utc).timestamp()) + 300,
        # Missing both email and sub claims
    }

    # Verify token with missing claims raises error
    with pytest.raises(HTTPException) as exc_info:
        verify_token("mock.token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in str(exc_info.value.detail)


def test_verify_token_invalid_format(mock_jwt):
    """Test invalid token format with mocked JWT."""
    # Setup mock to raise JWTError for invalid format
    mock_jwt.decode.side_effect = JWTError("Invalid token format")

    invalid_tokens = [
        "",  # Empty token
        "not.a.jwt",  # Malformed JWT
        "invalid",  # Random string
        "eyJ0.invalid.token",  # Partial JWT
    ]

    for invalid_token in invalid_tokens:
        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in str(exc_info.value.detail)


def test_create_access_token_invalid_data(mock_settings):
    """Test token creation with invalid data."""
    with pytest.raises(ValueError):
        create_access_token({"invalid": object()})


def test_create_access_token_non_serializable_data(mock_jwt):
    """Test token creation with non-JSON-serializable data."""

    # Create a non-serializable object
    class NonSerializable:
        """A class that cannot be serialized to JSON."""

        def __str__(self):
            """String representation."""
            return "NonSerializable"

        def to_dict(self):
            """Attempt to convert to dict (will fail)."""
            return {"type": "non-serializable"}

    data = {"test": NonSerializable(), "sub": "test@example.com"}

    # Setup mock to raise TypeError when trying to encode
    mock_jwt.encode.side_effect = TypeError(
        "Object of type NonSerializable is not JSON serializable"
    )

    # Test that non-serializable data raises ValueError
    with pytest.raises(ValueError) as exc_info:
        create_access_token(data)

    assert "Data is not JSON serializable" in str(exc_info.value)


def test_create_access_token_encode_error(mock_settings, mocker):
    """Test token creation when encode fails."""
    # Mock jwt.encode to raise an error
    mocker.patch("jose.jwt.encode", side_effect=JWTError("Encoding failed"))

    with pytest.raises(ValueError) as exc_info:
        create_access_token({"sub": "test"})

    assert str(exc_info.value) == "Failed to create access token: Encoding failed"


def test_verify_token_revoked(mock_settings):
    """Test verification of revoked token."""
    # Mock REVOKED_TOKENS to include our test token
    test_token = "revoked.token"
    with patch("Protexis_Command.api.common.auth.jwt.REVOKED_TOKENS", {test_token}):
        with pytest.raises(HTTPException) as exc_info:
            verify_token(test_token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


def test_verify_token_invalid_exp_format(mock_jwt):
    """Test token with invalid expiration format."""
    # Setup mock to return invalid exp format
    mock_jwt.decode.return_value = {
        "exp": "not_a_timestamp",
        "email": "test@example.com",
    }

    # Verify token with invalid exp format raises error
    with pytest.raises(HTTPException) as exc_info:
        verify_token("mock.token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in str(exc_info.value.detail)


def test_verify_token_empty_claims(mock_jwt):
    """Test token with empty string claims."""
    # Setup mock to return empty string claims
    mock_jwt.decode.return_value = {
        "exp": int(datetime.now(timezone.utc).timestamp()) + 300,
        "email": "",  # Empty string
        "sub": "   ",  # Whitespace string
    }

    # Verify token with empty claims raises error
    with pytest.raises(HTTPException) as exc_info:
        verify_token("mock.token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in str(exc_info.value.detail)


def test_verify_token_unexpected_error(mock_jwt):
    """Test token verification with unexpected error."""
    # Setup mock to raise unexpected error
    mock_jwt.decode.side_effect = Exception("Unexpected error")

    # Verify unexpected error is wrapped in HTTPException
    with pytest.raises(HTTPException) as exc_info:
        verify_token("mock.token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in str(exc_info.value.detail)


def test_verify_token_missing_email_claim(mock_jwt):
    """Test token with missing email claim but valid sub claim."""
    # Setup mock to return token with only sub claim and exp
    mock_jwt.decode.return_value = {
        "sub": "test@example.com",
        "exp": int(datetime.now(timezone.utc).timestamp()),
    }  # Completely omit email field

    # Call verify_token
    token_data = verify_token("dummy_token")

    # Verify that email was copied from sub
    assert token_data.email == "test@example.com"
    assert token_data.sub == "test@example.com"


def test_verify_token_missing_sub_claim(mock_jwt):
    """Test token with missing sub claim but valid email claim."""
    # Setup mock to return token with only email claim
    mock_jwt.decode.return_value = {
        "exp": int(datetime.now(timezone.utc).timestamp()) + 300,
        "email": "test@example.com",  # Only email claim
    }

    # Verify token
    token_data = verify_token("mock.token")

    # Verify sub was copied from email
    assert token_data.email == "test@example.com"
    assert token_data.sub == "test@example.com"


@pytest.mark.asyncio
async def test_revoke_token():
    """Test token revocation."""
    test_token = "test.token"
    initial_size = len(REVOKED_TOKENS)

    # Revoke token
    await revoke_token(test_token)

    try:
        # Verify token was added to revoked set
        assert test_token in REVOKED_TOKENS
        assert len(REVOKED_TOKENS) == initial_size + 1

        # Verify revoked token is rejected
        with pytest.raises(HTTPException) as exc_info:
            verify_token(test_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in str(exc_info.value.detail)
    finally:
        # Cleanup
        REVOKED_TOKENS.remove(test_token)
