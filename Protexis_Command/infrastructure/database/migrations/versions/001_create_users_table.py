"""Create users table and seed admin user.

Revision ID: 001
Revises:
Create Date: 2024-02-17 10:00:00.000000

Creates users table and seeds the default admin user for development.
"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from api_protexis.security.password import get_password_hash
from sqlalchemy import column, table

# revision identifiers, used by Alembic
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Development admin credentials
ADMIN_EMAIL = "aaron.porter225@gmail.com"
ADMIN_NAME = "Aaron Porter"
ADMIN_PASSWORD = "ThisIsRussia#225"  # Dev only


def upgrade() -> None:
    """Create users table and seed admin."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Create admin user
    users = table(
        "users",
        column("email", sa.String),
        column("name", sa.String),
        column("hashed_password", sa.String),
        column("role", sa.String),
        column("is_active", sa.Boolean),
        column("created_at", sa.DateTime),
    )

    op.bulk_insert(
        users,
        [
            {
                "email": ADMIN_EMAIL,
                "name": ADMIN_NAME,
                "hashed_password": get_password_hash(ADMIN_PASSWORD),
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow(),
            }
        ],
    )


def downgrade() -> None:
    """Remove users table."""
    op.drop_table("users")
