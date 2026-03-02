"""create events and polls tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-02 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "start_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "end_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_events_active_code",
        "events",
        ["code"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    op.create_table(
        "polls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column(
            "question",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "poll_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "options",
            JSONB(),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_polls_event_id",
        "polls",
        ["event_id"],
    )

    op.create_table(
        "poll_responses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("poll_id", sa.Uuid(), nullable=False),
        sa.Column(
            "fingerprint_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "response_data",
            JSONB(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["poll_id"],
            ["polls.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_poll_responses_poll_id",
        "poll_responses",
        ["poll_id"],
    )

    op.add_column(
        "topics",
        sa.Column(
            "event_id",
            sa.Uuid(),
            sa.ForeignKey("events.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("topics", "event_id")

    op.drop_index(
        "ix_poll_responses_poll_id",
        table_name="poll_responses",
    )
    op.drop_table("poll_responses")

    op.drop_index("ix_polls_event_id", table_name="polls")
    op.drop_table("polls")

    op.drop_index("ix_events_active_code", table_name="events")
    op.drop_table("events")
