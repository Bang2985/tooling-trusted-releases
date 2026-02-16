"""Rename input_hash inputs_hash

Revision ID: 0049_2026.02.11_5b874ed2
Revises: 0048_2026.02.06_blocking_to_blocker
Create Date: 2026-02-11 13:42:59.712570+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic
revision: str = "0049_2026.02.11_5b874ed2"
down_revision: str | None = "0048_2026.02.06_blocking_to_blocker"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("checkresult", schema=None) as batch_op:
        batch_op.add_column(sa.Column("inputs_hash", sa.String(), nullable=True))
        batch_op.drop_index(batch_op.f("ix_checkresult_input_hash"))
        batch_op.create_index(batch_op.f("ix_checkresult_inputs_hash"), ["inputs_hash"], unique=False)
    with op.batch_alter_table("checkresult", schema=None) as batch_op:
        batch_op.execute("UPDATE checkresult SET inputs_hash = input_hash")
        batch_op.drop_column("input_hash")


def downgrade() -> None:
    with op.batch_alter_table("checkresult", schema=None) as batch_op:
        batch_op.add_column(sa.Column("input_hash", sa.VARCHAR(), nullable=True))
        batch_op.drop_index(batch_op.f("ix_checkresult_inputs_hash"))
        batch_op.create_index(batch_op.f("ix_checkresult_input_hash"), ["input_hash"], unique=False)
    with op.batch_alter_table("checkresult", schema=None) as batch_op:
        batch_op.execute("UPDATE checkresult SET input_hash = inputs_hash")
        batch_op.drop_column("inputs_hash")
