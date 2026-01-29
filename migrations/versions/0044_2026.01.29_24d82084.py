"""Record check cache status and allow status to be set

Revision ID: 0044_2026.01.29_24d82084
Revises: 0043_2026.01.29_d7d89670
Create Date: 2026-01-29 20:16:47.043872+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic
revision: str = "0044_2026.01.29_24d82084"
down_revision: str | None = "0043_2026.01.29_d7d89670"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("checkresult", schema=None) as batch_op:
        batch_op.add_column(sa.Column("cached", sa.Boolean(), nullable=False, server_default=sa.false()))

    with op.batch_alter_table("revision", schema=None) as batch_op:
        batch_op.add_column(sa.Column("use_check_cache", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    with op.batch_alter_table("revision", schema=None) as batch_op:
        batch_op.drop_column("use_check_cache")

    with op.batch_alter_table("checkresult", schema=None) as batch_op:
        batch_op.drop_column("cached")
