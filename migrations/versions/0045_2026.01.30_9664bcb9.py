"""Associate check result ignores with projects not committees

Revision ID: 0045_2026.01.30_9664bcb9
Revises: 0044_2026.01.29_24d82084
Create Date: 2026-01-30 14:44:47.168525+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic
revision: str = "0045_2026.01.30_9664bcb9"
down_revision: str | None = "0044_2026.01.29_24d82084"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add the new project name column
    with op.batch_alter_table("checkresultignore", schema=None) as batch_op:
        batch_op.add_column(sa.Column("project_name", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            batch_op.f("fk_checkresultignore_project_name_project"), "project", ["project_name"], ["name"]
        )

    bind = op.get_bind()
    check_result_ignore = sa.table(
        "checkresultignore",
        sa.column("id", sa.Integer),
        sa.column("asf_uid", sa.String),
        sa.column("created", sa.DateTime),
        sa.column("committee_name", sa.String),
        sa.column("project_name", sa.String),
        sa.column("release_glob", sa.String),
        sa.column("revision_number", sa.String),
        sa.column("checker_glob", sa.String),
        sa.column("primary_rel_path_glob", sa.String),
        sa.column("member_rel_path_glob", sa.String),
        sa.column("status", sa.String),
        sa.column("message_glob", sa.String),
    )
    project = sa.table(
        "project",
        sa.column("name", sa.String),
        sa.column("committee_name", sa.String),
    )

    existing_ignores = bind.execute(
        sa.select(
            check_result_ignore.c.asf_uid,
            check_result_ignore.c.created,
            check_result_ignore.c.committee_name,
            check_result_ignore.c.release_glob,
            check_result_ignore.c.revision_number,
            check_result_ignore.c.checker_glob,
            check_result_ignore.c.primary_rel_path_glob,
            check_result_ignore.c.member_rel_path_glob,
            check_result_ignore.c.status,
            check_result_ignore.c.message_glob,
        ).where(check_result_ignore.c.project_name.is_(None))
    ).fetchall()

    # Expand each committee scoped ignore to cover all projects in its committee
    for ignore in existing_ignores:
        project_names = bind.execute(
            sa.select(project.c.name).where(project.c.committee_name == ignore.committee_name)
        ).fetchall()
        for (project_name,) in project_names:
            bind.execute(
                check_result_ignore.insert().values(
                    asf_uid=ignore.asf_uid,
                    created=ignore.created,
                    committee_name=ignore.committee_name,
                    project_name=project_name,
                    release_glob=ignore.release_glob,
                    revision_number=ignore.revision_number,
                    checker_glob=ignore.checker_glob,
                    primary_rel_path_glob=ignore.primary_rel_path_glob,
                    member_rel_path_glob=ignore.member_rel_path_glob,
                    status=ignore.status,
                    message_glob=ignore.message_glob,
                )
            )

    # Remove the original committee scoped ignores
    bind.execute(check_result_ignore.delete().where(check_result_ignore.c.project_name.is_(None)))

    # Complete the schema transition
    with op.batch_alter_table("checkresultignore", schema=None) as batch_op:
        batch_op.alter_column("project_name", nullable=False)
        batch_op.drop_column("committee_name")


def downgrade() -> None:
    # Restore the committee name column
    with op.batch_alter_table("checkresultignore", schema=None) as batch_op:
        batch_op.add_column(sa.Column("committee_name", sa.VARCHAR(), nullable=True))

    bind = op.get_bind()
    check_result_ignore = sa.table(
        "checkresultignore",
        sa.column("id", sa.Integer),
        sa.column("committee_name", sa.String),
        sa.column("project_name", sa.String),
    )
    project = sa.table(
        "project",
        sa.column("name", sa.String),
        sa.column("committee_name", sa.String),
    )

    # Populate committee names from project ownership or delete orphaned ignores
    project_committee_map = {
        name: committee_name
        for name, committee_name in bind.execute(sa.select(project.c.name, project.c.committee_name)).fetchall()
    }
    ignore_rows = bind.execute(sa.select(check_result_ignore.c.id, check_result_ignore.c.project_name)).fetchall()
    for ignore_id, project_name in ignore_rows:
        committee_name = project_committee_map.get(project_name)
        if committee_name is None:
            bind.execute(check_result_ignore.delete().where(check_result_ignore.c.id == ignore_id))
            continue
        bind.execute(
            check_result_ignore.update()
            .where(check_result_ignore.c.id == ignore_id)
            .values(committee_name=committee_name)
        )

    # Complete the schema rollback
    with op.batch_alter_table("checkresultignore", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_checkresultignore_project_name_project"), type_="foreignkey")
        batch_op.drop_column("project_name")
        batch_op.alter_column("committee_name", nullable=False)
