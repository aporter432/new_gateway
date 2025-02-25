"""Integration tests for OGx session handler.

These tests verify the complete session management flow using:
- Real Redis instance for session storage
- Actual OGx proxy for authentication
- Real session creation and validation

Note: These tests require the full Docker environment to be running:
- Redis service
- OGx proxy service
- Proper network connectivity
"""

import pytest
from redis.asyncio import Redis

from Protexis_Command.api.services.session.ogx_session_handler import SessionHandler
from Protexis_Command.protocol.ogx.validation.ogx_validation_exceptions import (
    AuthenticationError,
    OGxProtocolError,
    ValidationError,
)

# Test data
TEST_CLIENT_ID = "70000934"  # Valid test client ID
TEST_CLIENT_SECRET = "test_secret"  # Valid test secret
TEST_CUSTOMER = "test_customer"


@pytest.fixture
async def session_handler(redis_client: Redis) -> SessionHandler:
    """Create and initialize a session handler using real Redis.

    This fixture uses the Redis client from conftest.py which connects
    to the actual Redis instance in the test environment.
    """
    handler = SessionHandler()
    await handler.initialize()
    return handler


@pytest.mark.asyncio
class TestSessionHandlerIntegration:
    """Integration tests for complete session management flows."""

    async def test_complete_session_lifecycle(self, session_handler: SessionHandler):
        """Test complete session lifecycle from creation to cleanup.

        This test verifies:
        1. Session creation with real OGx authentication
        2. Session validation using stored token
        3. Session refresh with new token
        4. Session cleanup and removal
        """
        # Create session with valid credentials
        credentials = {
            "client_id": TEST_CLIENT_ID,
            "client_secret": TEST_CLIENT_SECRET,
        }
        session_id = await session_handler.create_session(credentials)

        # Verify session was created
        assert isinstance(session_id, str)
        assert len(session_id) > 0

        # Validate session is active
        is_valid = await session_handler.validate_session(session_id)
        assert is_valid, "Session should be valid after creation"

        # Refresh session
        await session_handler.refresh_session(session_id)

        # Verify session is still valid after refresh
        is_valid = await session_handler.validate_session(session_id)
        assert is_valid, "Session should be valid after refresh"

        # End session
        await session_handler.end_session(session_id)

        # Verify session is no longer valid
        is_valid = await session_handler.validate_session(session_id)
        assert not is_valid, "Session should be invalid after ending"

    async def test_session_limit_enforcement(self, session_handler: SessionHandler):
        """Test session limit enforcement with real Redis tracking.

        This test verifies:
        1. Can create up to max allowed sessions
        2. Additional session creation fails
        3. After ending a session, can create new one
        """
        active_sessions = []
        try:
            # Create sessions up to limit
            for _ in range(3):  # Assuming limit is 3 for test environment
                credentials = {
                    "client_id": TEST_CLIENT_ID,
                    "client_secret": TEST_CLIENT_SECRET,
                }
                session_id = await session_handler.create_session(credentials)
                active_sessions.append(session_id)

            # Verify cannot create additional session
            with pytest.raises(OGxProtocolError) as exc:
                await session_handler.create_session(credentials)
            assert "Maximum concurrent sessions" in str(exc.value)

            # End one session
            session_to_end = active_sessions.pop()
            await session_handler.end_session(session_to_end)

            # Verify can create new session
            new_session_id = await session_handler.create_session(credentials)
            active_sessions.append(new_session_id)
            assert isinstance(new_session_id, str)

        finally:
            # Cleanup all sessions
            for session_id in active_sessions:
                try:
                    await session_handler.end_session(session_id)
                except Exception:
                    pass  # Ignore cleanup errors

    async def test_invalid_credentials(self, session_handler: SessionHandler):
        """Test authentication with invalid credentials.

        This test verifies:
        1. Invalid credentials are rejected by real OGx auth
        2. Proper error is returned
        """
        invalid_credentials = {
            "client_id": "invalid_id",
            "client_secret": "invalid_secret",
        }
        with pytest.raises(AuthenticationError) as exc:
            await session_handler.create_session(invalid_credentials)
        assert "Invalid credentials" in str(exc.value)

    async def test_missing_credentials(self, session_handler: SessionHandler):
        """Test validation of missing credentials.

        This test verifies proper validation before auth attempt.
        """
        with pytest.raises(ValidationError) as exc:
            await session_handler.create_session({"client_secret": TEST_CLIENT_SECRET})
        assert "client_id is required" in str(exc.value)

        with pytest.raises(ValidationError) as exc:
            await session_handler.create_session({"client_id": TEST_CLIENT_ID})
        assert "client_secret is required" in str(exc.value)

    async def test_concurrent_session_operations(self, session_handler: SessionHandler):
        """Test concurrent session operations.

        This test verifies:
        1. Can handle multiple concurrent sessions
        2. Operations on one session don't affect others
        3. Redis handles concurrent access properly
        """
        # Create multiple sessions
        credentials = {
            "client_id": TEST_CLIENT_ID,
            "client_secret": TEST_CLIENT_SECRET,
        }
        session_ids = []
        try:
            # Create two concurrent sessions
            for _ in range(2):
                session_id = await session_handler.create_session(credentials)
                session_ids.append(session_id)

            # Verify all sessions are valid
            for session_id in session_ids:
                is_valid = await session_handler.validate_session(session_id)
                assert is_valid, f"Session {session_id} should be valid"

            # End one session
            await session_handler.end_session(session_ids[0])

            # Verify first session invalid but second still valid
            assert not await session_handler.validate_session(session_ids[0])
            assert await session_handler.validate_session(session_ids[1])

        finally:
            # Cleanup
            for session_id in session_ids:
                try:
                    await session_handler.end_session(session_id)
                except Exception:
                    pass  # Ignore cleanup errors
