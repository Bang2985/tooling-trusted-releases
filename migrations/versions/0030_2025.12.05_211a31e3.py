"""Add a field for vote comment templates

Revision ID: 0030_2025.12.05_211a31e3
Revises: 0029_2025.11.28_6486ff5e
Create Date: 2025-12-05 10:25:32.833183+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic
revision: str = "0030_2025.12.05_211a31e3"
down_revision: str | None = "0029_2025.11.28_6486ff5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("releasepolicy", schema=None) as batch_op:
        batch_op.add_column(sa.Column("vote_comment_template", sa.String(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("releasepolicy", schema=None) as batch_op:
        batch_op.drop_column("vote_comment_template")
