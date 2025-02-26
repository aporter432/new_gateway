"""Create admin user script.

Creates the first admin user for the system.

Usage:
    docker-compose run ogx_gateway_api poetry run python -m Protexis_Command.scripts.auth.create_admin
"""

import asyncio
import getpass
import logging
import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from Protexis_Command.api.common.auth.password import get_password_hash
from Protexis_Command.infrastructure.database.models.user import User, UserRole
from Protexis_Command.infrastructure.database.session import async_session_maker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Create an admin user interactively."""
    logger.info("Starting admin user creation")

    try:
        # Get user input
        email = input("Enter admin email: ")
        if not email or "@" not in email:
            print("Invalid email format")
            sys.exit(1)

        name = input("Enter admin name: ")
        if not name:
            print("Name is required")
            sys.exit(1)

        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match")
            sys.exit(1)

        # Create user
        try:
            async with async_session_maker() as db:
                logger.info("Attempting database connection")
                # Test connection
                await db.execute(text("SELECT 1"))
                logger.info("Database connection successful")

                user = User(
                    email=email,
                    name=name,
                    hashed_password=get_password_hash(password),
                    role=UserRole.ADMIN,
                    is_active=True,
                )

                db.add(user)
                try:
                    await db.commit()
                    logger.info("Successfully committed user to database")
                except SQLAlchemyError as e:
                    logger.error(f"Database commit failed: {str(e)}")
                    await db.rollback()
                    raise

                print("\nAdmin user created successfully:")
                print(f"Email: {user.email}")
                print(f"Name: {user.name}")
                print(f"Role: {user.role}")

        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
