"""fix_userrole_enum_values

Revision ID: 0fe9acac5484
Revises: ca6dbbf7fce5
Create Date: 2025-02-26 23:54:26.558275+00:00

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = "0fe9acac5484"
down_revision: Union[str, None] = "ca6dbbf7fce5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix the userrole enum to have exactly the correct values.
    This preserves existing data by temporarily converting to text.
    """
    conn = op.get_bind()

    # First, temporarily change the column type to text to preserve the values
    conn.execute(
        text(
            """
            ALTER TABLE users ALTER COLUMN role TYPE text;
            """
        )
    )

    # Drop the old enum
    conn.execute(text("DROP TYPE userrole;"))

    # Create the new enum with exactly the correct values
    conn.execute(
        text(
            """
            CREATE TYPE userrole AS ENUM (
                'accounting',
                'protexis_administrator',
                'protexis_view',
                'protexis_request_read',
                'protexis_request_write',
                'protexis_site_admin',
                'protexis_tech_admin'
            );
            """
        )
    )

    # Convert the column back to the enum type
    conn.execute(
        text(
            """
            ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole;
            """
        )
    )


def downgrade() -> None:
    """
    We don't provide a downgrade path as this is a data correction.
    Downgrading would risk data loss for users with the new role values.
    """
    pass
