"""create votes table

Revision ID: a1b2c3d4e5f6
Revises: 54baf5f8186d
Create Date: 2026-02-17 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "54baf5f8186d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "votes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column(
            "fingerprint_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "topic_id",
            "fingerprint_id",
            name="uq_votes_topic_fingerprint",
        ),
        sa.CheckConstraint(
            "value IN (-1, 1)",
            name="ck_votes_value",
        ),
    )
    op.create_index(
        "ix_votes_topic_id",
        "votes",
        ["topic_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_votes_topic_id", table_name="votes")
    op.drop_table("votes")
