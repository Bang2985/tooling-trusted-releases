"""Rename blocking check result status to blocker

Revision ID: 0048_2026.02.06_blocking_to_blocker
Revises: 0047_2026.02.03_525fe161
Create Date: 2026-02-06 16:00:00.000000+00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0048_2026.02.06_blocking_to_blocker"
down_revision: str | None = "0047_2026.02.03_525fe161"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE checkresult SET status = 'BLOCKER' WHERE status = 'BLOCKING'")
    op.execute("UPDATE checkresult SET status = 'BLOCKER' WHERE status = 'blocking'")


def downgrade() -> None:
    op.execute("UPDATE checkresult SET status = 'BLOCKING' WHERE status = 'BLOCKER'")
    op.execute("UPDATE checkresult SET status = 'BLOCKING' WHERE status = 'blocker'")
