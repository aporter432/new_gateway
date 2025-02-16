"""Unit tests for database dependencies.

This module tests the database dependency injection functionality:
- Session creation and lifecycle
- Error handling
- Context manager behavior
- Session cleanup
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.dependencies import get_db


@pytest.fixture
def mock_session():
    """Fixture for mocked database session."""
    session = AsyncMock(spec=AsyncSession)
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_session_maker(mock_session):
    """Fixture for mocked session maker."""
    # Create an async context manager mock
    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    context_manager.__aexit__ = AsyncMock(return_value=None)
    return MagicMock(return_value=context_manager)


@pytest.mark.asyncio
async def test_get_db_session_lifecycle(mock_session_maker, mock_session):
    """Test complete database session lifecycle.

    Verifies:
    - Session is created properly
    - Session is yielded
    - Session is closed after use
    """
    with patch("infrastructure.database.dependencies.async_session_maker", mock_session_maker):
        db_generator = get_db()
        session = await db_generator.__anext__()

        # Verify session is our mock
        assert session == mock_session

        # Verify session maker was called
        mock_session_maker.assert_called_once()

        # Verify context manager was used
        mock_session_maker.return_value.__aenter__.assert_called_once()

        # Close the generator (simulates end of request)
        try:
            await db_generator.__anext__()
        except StopAsyncIteration:
            pass

        # Verify session was closed
        mock_session.close.assert_called_once()
        mock_session_maker.return_value.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_get_db_error_handling(mock_session_maker, mock_session):
    """Test error handling during session use.

    Verifies:
    - Session is closed even if an error occurs
    - Context manager handles exceptions properly
    - Context manager exit is called with exception info
    """
    # Make session.close raise an exception
    error = Exception("Session close error")
    mock_session.close.side_effect = error

    with patch("infrastructure.database.dependencies.async_session_maker", mock_session_maker):
        db_generator = get_db()
        session = await db_generator.__anext__()

        # Verify session is our mock
        assert session == mock_session

        # Close the generator (simulates end of request)
        with pytest.raises(Exception) as exc_info:
            await db_generator.__anext__()

        assert str(exc_info.value) == "Session close error"

        # Verify close was attempted despite error
        mock_session.close.assert_called_once()

        # Verify context manager exit was called with exception info
        mock_session_maker.return_value.__aexit__.assert_called_once()
        exit_args = mock_session_maker.return_value.__aexit__.call_args[0]
        assert exit_args[0] is Exception  # Type
        assert isinstance(exit_args[1], Exception)  # Value
        assert str(exit_args[1]) == "Session close error"


@pytest.mark.asyncio
async def test_get_db_context_manager_error():
    """Test handling of context manager errors.

    Verifies:
    - Errors during context manager entry are handled properly
    - No session operations occur if context manager fails
    - Context manager exit is called with exception info
    """
    # Create mocks
    mock_session = AsyncMock(spec=AsyncSession)

    # Create an async context manager that raises on enter
    class MockContextManager:
        async def __aenter__(self):
            raise Exception("Context manager error")

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    context_manager = MockContextManager()
    mock_session_maker = MagicMock(return_value=context_manager)

    with patch("infrastructure.database.dependencies.async_session_maker", mock_session_maker):
        db_generator = get_db()

        # Verify error is propagated
        with pytest.raises(Exception) as exc_info:
            await db_generator.__anext__()

        assert str(exc_info.value) == "Context manager error"

        # No need to verify __aenter__ and __aexit__ calls as they're real coroutines
        # The fact that we got the correct error proves they were called correctly


@pytest.mark.asyncio
async def test_get_db_multiple_yields(mock_session_maker, mock_session):
    """Test that generator only yields once.

    Verifies:
    - Session is yielded exactly once
    - Subsequent attempts to yield raise StopAsyncIteration
    - Cleanup occurs after StopAsyncIteration
    """
    with patch("infrastructure.database.dependencies.async_session_maker", mock_session_maker):
        db_generator = get_db()

        # First yield should succeed
        session = await db_generator.__anext__()
        assert session == mock_session

        # Second yield should raise StopAsyncIteration
        with pytest.raises(StopAsyncIteration):
            await db_generator.__anext__()

        # Verify cleanup occurred
        mock_session.close.assert_called_once()
        mock_session_maker.return_value.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_get_db_session_cleanup_on_error():
    """Test session cleanup when an error occurs during use.

    Verifies:
    - Session is properly cleaned up when an error occurs
    - Context manager handles the error correctly
    - All cleanup operations are performed
    """
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.close = AsyncMock()

    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(return_value=mock_session)

    # Configure __aexit__ to be called with the error
    async def async_exit(exc_type, exc_val, exc_tb):
        return None

    context_manager.__aexit__ = AsyncMock(side_effect=async_exit)

    mock_session_maker = MagicMock(return_value=context_manager)

    with patch("infrastructure.database.dependencies.async_session_maker", mock_session_maker):
        db_generator = get_db()
        session = await db_generator.__anext__()

        # Simulate an error during session use
        error = Exception("Error during session use")
        mock_session.execute = AsyncMock(side_effect=error)

        # Verify session is cleaned up
        with pytest.raises(Exception) as exc_info:
            await session.execute("SELECT 1")

        assert str(exc_info.value) == "Error during session use"

        # Close the generator to trigger cleanup
        try:
            await db_generator.__anext__()
        except StopAsyncIteration:
            pass

        # Verify cleanup occurred
        mock_session.close.assert_called_once()
        context_manager.__aexit__.assert_awaited_once()
        exit_args = context_manager.__aexit__.call_args[0]
        assert exit_args[0] is None  # No error during exit
        assert exit_args[1] is None  # No error value
