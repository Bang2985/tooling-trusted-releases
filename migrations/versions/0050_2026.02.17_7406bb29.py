"""Add inputs hash to task table

Revision ID: 0050_2026.02.17_7406bb29
Revises: 0049_2026.02.11_5b874ed2
Create Date: 2026-02-17 14:34:59.166215+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic
revision: str = "0050_2026.02.17_7406bb29"
down_revision: str | None = "0049_2026.02.11_5b874ed2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.add_column(sa.Column("inputs_hash", sa.String(), nullable=True))
        batch_op.create_index(batch_op.f("ix_task_inputs_hash"), ["inputs_hash"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_task_inputs_hash"))
        batch_op.drop_column("inputs_hash")
