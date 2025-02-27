"""add_protexis_roles

Revision ID: ca6dbbf7fce5
Revises: 001
Create Date: 2025-02-26 13:38:26.558275+00:00

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = "ca6dbbf7fce5"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade the database schema to include additional Protexis roles.

    This migration adds new role values to the 'userrole' enum type in PostgreSQL.
    Since PostgreSQL doesn't allow directly modifying enums, we need to:
    1. Create a new enum type with all values (old + new)
    2. Update the column to use the new enum
    3. Drop the old enum
    4. Rename the new enum to match the original name
    """
    # PostgreSQL doesn't allow modifying enums directly
    # We need to create a new enum, update the columns, then drop the old enum

    # Create new enum type with all values
    conn = op.get_bind()  # type: ignore # pylint: disable=no-member

    conn.execute(
        text(
            """
        CREATE TYPE userrole_new AS ENUM (
            'accounting',
            'protexis_administrator',
            'protexis_view',
            'protexis_request_read',
            'protexis_request_write',
            'protexis_site_admin',
            'protexis_tech_admin',
        )
    """
        )
    )

    # Update the column to use the new enum
    conn.execute(
        text(
            """
        ALTER TABLE users
        ALTER COLUMN role TYPE userrole_new
        USING role::text::userrole_new
    """
        )
    )

    # Drop the old enum
    conn.execute(text("DROP TYPE userrole"))

    # Rename the new enum to the original name
    conn.execute(text("ALTER TYPE userrole_new RENAME TO userrole"))


def downgrade() -> None:
    """
    Revert the schema changes by restoring the original 'userrole' enum.

    This function removes the added enum values by:
    1. Creating a new enum with only the original values
    2. Converting existing data to fit the old enum (may lose information)
    3. Dropping the modified enum
    4. Renaming the old-style enum to the original name
    """
    conn = op.get_bind()  # type: ignore # pylint: disable=no-member

    # Reverse the process
    conn.execute(text("CREATE TYPE userrole_old AS ENUM ('user', 'admin')"))
    conn.execute(
        text(
            """
        ALTER TABLE users
        ALTER COLUMN role TYPE userrole_old
        USING role::text::userrole_old
    """
        )
    )
    conn.execute(text("DROP TYPE userrole"))
    conn.execute(text("ALTER TYPE userrole_old RENAME TO userrole"))
