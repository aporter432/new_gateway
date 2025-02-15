"""Test JWT token utilities.

This module tests:
- Token creation
- Token validation
- Token expiration
- Error handling
"""

import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import JWTError, jwt

from api.security.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    TokenData,
    create_access_token,
    verify_token,
)
from core.app_settings import get_settings

settings = get_settings()


def test_create_access_token():
    """Test access token creation."""
    # Test basic token creation
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    assert token is not None
    assert isinstance(token, str)

    # Decode and verify token contents
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "test@example.com"
    assert "exp" in payload


def test_create_access_token_with_expiry():
    """Test token creation with custom expiry."""
    data = {"sub": "test@example.com"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta)

    # Verify expiration time
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert (exp - now).total_seconds() <= expires_delta.total_seconds()


def test_verify_valid_token():
    """Test verification of valid token."""
    email = "test@example.com"
    token = create_access_token({"sub": email})
    token_data = verify_token(token)

    assert isinstance(token_data, TokenData)
    assert token_data.email == email
    assert token_data.sub == email
    assert isinstance(token_data.exp, datetime)


def test_verify_expired_token():
    """Test verification of expired token."""
    # Create token that expires immediately
    token = create_access_token(
        {"sub": "test@example.com"},
        expires_delta=timedelta(microseconds=1),
    )
    # Wait for token to expire
    time.sleep(0.1)

    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_verify_invalid_token():
    """Test verification of invalid token."""
    # Test with malformed token
    with pytest.raises(HTTPException) as exc_info:
        verify_token("invalid_token")
    assert exc_info.value.status_code == 401

    # Test with token signed with different key
    wrong_token = jwt.encode(
        {"sub": "test@example.com", "exp": datetime.utcnow() + timedelta(minutes=15)},
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
    # Create token with different algorithm
    wrong_alg_token = jwt.encode(
        {"sub": "test@example.com", "exp": datetime.utcnow() + timedelta(minutes=15)},
        settings.JWT_SECRET_KEY,
        algorithm="HS512",  # Different from ALGORITHM
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_token(wrong_alg_token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_token_with_invalid_expiry_format():
    """Test token with invalid expiry format."""
    # Create token with invalid expiry format
    token = jwt.encode(
        {"sub": "test@example.com", "exp": "invalid_timestamp"},
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_token_without_expiry():
    """Test token without expiry claim."""
    # Create token without expiry
    token = jwt.encode({"sub": "test@example.com"}, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_token_with_future_expiry():
    """Test token with future expiry (not yet valid)."""
    # Create token with nbf (not before) claim in the future
    token = jwt.encode(
        {
            "sub": "test@example.com",
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

        pass

    data = {"sub": NonSerializable()}
    with pytest.raises(ValueError) as exc_info:
        create_access_token(data)
    assert "Failed to create access token" in str(exc_info.value)
    assert "not JSON serializable" in str(exc_info.value)


def test_create_access_token_jwt_error(monkeypatch):
    """Test token creation failure due to JWT error."""

    def mock_encode(*args, **kwargs):
        raise JWTError("JWT Error")

    monkeypatch.setattr(jwt, "encode", mock_encode)
    data = {"sub": "test@example.com"}

    with pytest.raises(ValueError) as exc_info:
        create_access_token(data)
    assert "Failed to create access token: JWT Error" in str(exc_info.value)


def test_token_exact_expiry():
    """Test token that expires exactly at the current time."""
    # Create token that expires in the past to ensure it's expired
    # Use a fixed time in the past to avoid timing issues
    current_time = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    token = jwt.encode(
        {
            "sub": "test@example.com",
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
    # Create valid token first
    token = create_access_token({"sub": "test@example.com"})

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
