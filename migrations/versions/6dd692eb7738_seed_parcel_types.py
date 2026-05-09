"""seed parcel types

Revision ID: 6dd692eb7738
Revises: 1ce2661b0087
Create Date: 2026-05-04 23:58:48.595237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6dd692eb7738'
down_revision: Union[str, Sequence[str], None] = '1ce2661b0087'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(
        sa.table(
            "parcel_types",
            sa.column("id", sa.Integer),
            sa.column("name", sa.String),
        ),
        [
            {"id": 1, "name": "Одежда"},
            {"id": 2, "name": "Электроника"},
            {"id": 3, "name": "Разное"},
        ],
    )
    


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text(
            """
            DELETE FROM parcel_types
            WHERE id IN (1, 2, 3)
            """
        )
    )

