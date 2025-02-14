"""Create users table.

Revision ID: 001
Revises: 
Create Date: 2024-02-13

This migration creates the initial users table with:
- Basic user information (name, email)
- Authentication fields (hashed_password)
- Role-based access control
- Account status tracking
- Timestamps
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, Boolean, DateTime


# revision identifiers, used by Alembic
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table."""
    # Create enum type for user roles
    op.execute(
        """
        CREATE TYPE user_role AS ENUM ('user', 'admin');
    """
    )

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", String(255), nullable=False),
        sa.Column("name", String(255), nullable=False),
        sa.Column("hashed_password", String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="user_role"),
            nullable=False,
            server_default="user",
        ),
        sa.Column("is_active", Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    """Remove users table."""
    # Drop indexes
    op.drop_index(op.f("ix_users_email"), table_name="users")

    # Drop table
    op.drop_table("users")

    # Drop enum type
    op.execute(
        """
        DROP TYPE user_role;
    """
    )
