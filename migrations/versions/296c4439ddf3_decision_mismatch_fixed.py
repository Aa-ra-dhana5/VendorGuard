"""decision mismatch fixed

Revision ID: 296c4439ddf3
Revises: b73335fe7d8b
Create Date: 2026-05-01 11:21:11.464354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '296c4439ddf3'
down_revision: Union[str, Sequence[str], None] = 'b73335fe7d8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: add column as nullable
    op.add_column(
        'decision',
        sa.Column(
            'decision_status',
            sa.Enum(
                'released', 'on_hold', 'partially_released',
                'manual_check', 'block', 'cancelled', 'recovery',
                name='statusenum'
            ),
            nullable=True
        )
    )

    # Step 2: fill existing rows (VERY IMPORTANT)
    op.execute("""
        UPDATE decision
        SET decision_status = 'on_hold'
    """)

    # Step 3: make it NOT NULL
    op.alter_column(
        'decision',
        'decision_status',
        nullable=False
    )