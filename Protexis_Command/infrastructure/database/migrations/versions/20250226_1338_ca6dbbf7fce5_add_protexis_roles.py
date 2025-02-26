"""add_protexis_roles

Revision ID: ca6dbbf7fce5
Revises: 001
Create Date: 2025-02-26 13:38:26.558275+00:00

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca6dbbf7fce5"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL doesn't allow modifying enums directly
    # We need to create a new enum, update the columns, then drop the old enum

    # Create new enum type with all values
    op.execute(
        """
        CREATE TYPE userrole_new AS ENUM (
            'user',
            'admin',
            'accounting',
            'protexis_administrator',
            'protexis_view',
            'protexis_request_read',
            'protexis_request_write',
            'protexis_site_admin',
            'protexis_tech_admin',
            'protexis_admin'
        )
    """
    )

    # Update the column to use the new enum
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE userrole_new USING role::text::userrole_new"
    )

    # Drop the old enum
    op.execute("DROP TYPE userrole")

    # Rename the new enum to the original name
    op.execute("ALTER TYPE userrole_new RENAME TO userrole")


def downgrade() -> None:
    # Reverse the process
    op.execute("CREATE TYPE userrole_old AS ENUM ('user', 'admin')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE userrole_old USING role::text::userrole_old"
    )
    op.execute("DROP TYPE userrole")
    op.execute("ALTER TYPE userrole_old RENAME TO userrole")
