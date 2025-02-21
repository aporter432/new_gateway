"""Base model for SQLAlchemy ORM models.

This module provides the base model class for all database models.
It implements:
- Common model attributes
- Base configuration
- Type hints
- Metadata handling

Implementation Notes:
    - Uses SQLAlchemy declarative base
    - Provides common fields (id)
    - Configures naming conventions
    - Sets up metadata
"""

from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Define naming convention for constraints
NAMING_CONVENTION: dict[str, Any] = {
    "ix": "ix_%(column_0_label)s",  # Index
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # Unique constraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # Check constraint
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # Foreign key
    "pk": "pk_%(table_name)s",  # Primary key
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    This class provides:
    - Common fields (id)
    - Metadata configuration
    - Naming conventions
    - Type hints

    All model classes should inherit from this base.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Common fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    def __repr__(self) -> str:
        """Get string representation of the model.

        Returns:
            String representation with class name and id
        """
        return f"{self.__class__.__name__}(id={self.id})"
