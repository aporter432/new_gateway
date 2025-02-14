"""Database dependencies for FastAPI.

This module provides database-related dependencies for FastAPI:
- Database session management
- Connection handling
- Session cleanup

Implementation Notes:
    - Uses SQLAlchemy async session
    - Implements proper cleanup
    - Handles session lifecycle
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    This dependency provides an async database session
    that is automatically closed after use.

    Yields:
        AsyncSession: Database session

    Notes:
        - Session is created per request
        - Session is automatically closed after request
        - Uses async context manager for proper cleanup
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
