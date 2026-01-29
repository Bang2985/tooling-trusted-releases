"""columns for pending distributions

Revision ID: 0042_2026.01.28_3e434625
Revises: 0041_2026.01.22_d1e357f5
Create Date: 2026-01-28 16:30:09.232235+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic
revision: str = "0042_2026.01.28_3e434625"
down_revision: str | None = "0041_2026.01.22_d1e357f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("distribution", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pending", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("retries", sa.Integer(), nullable=False, server_default="0"))
        batch_op.alter_column("api_url", existing_type=sa.VARCHAR(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("distribution", schema=None) as batch_op:
        batch_op.alter_column("api_url", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.drop_column("retries")
        batch_op.drop_column("pending")
