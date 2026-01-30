"""Add a GitHub repository branch property to release policies

Revision ID: 0046_2026.01.30_72330898
Revises: 0045_2026.01.30_9664bcb9
Create Date: 2026-01-30 17:27:25.246498+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic
revision: str = "0046_2026.01.30_72330898"
down_revision: str | None = "0045_2026.01.30_9664bcb9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("releasepolicy", schema=None) as batch_op:
        batch_op.add_column(sa.Column("github_repository_branch", sa.String(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("releasepolicy", schema=None) as batch_op:
        batch_op.drop_column("github_repository_branch")
