"""Add a payload property to GitHub SSH keys

Revision ID: 0047_2026.02.03_525fe161
Revises: 0046_2026.01.30_72330898
Create Date: 2026-02-03 19:49:11.922836+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic
revision: str = "0047_2026.02.03_525fe161"
down_revision: str | None = "0046_2026.01.30_72330898"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("workflowsshkey", schema=None) as batch_op:
        batch_op.add_column(sa.Column("github_payload", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    with op.batch_alter_table("workflowsshkey", schema=None) as batch_op:
        batch_op.drop_column("github_payload")
