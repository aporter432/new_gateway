"""Test JWT token utilities.

This module tests:
- Token creation
- Token validation
- Token expiration
- Error handling
"""

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from api.security.jwt import (
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
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
    import time

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
    # Create token without 'sub' claim
    token = jwt.encode(
        {"exp": datetime.utcnow() + timedelta(minutes=15)},
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail
